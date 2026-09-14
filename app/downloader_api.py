# -*- coding: utf-8 -*-
"""
SenaDizi - Çoklu Platform Dizi Tarama, Kilit Açma ve Akış Çözücü Motoru PRO
Desteklenen Platformlar: DramaFlix, DramaCix, DramaDizilerim, LiderDrama, DramaKolik / Filmkolik.
Tam Uyumlu Cross-Provider Stream Resolver & Strict Series Similarity Validator (Sıfır Yanlış Dizi Eşleşmesi).
"""

import os
import re
import json
import time
import base64
import sqlite3
import difflib
import threading
import urllib.parse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

def make_api_session(pool_size=48):
    s = requests.Session()
    # Fast-fail retries: never block repeatedly on unresponsive/timing-out origins
    retries = Retry(total=1, connect=1, read=0, status=0, backoff_factor=0.1)
    adapter = HTTPAdapter(pool_connections=pool_size, pool_maxsize=pool_size, max_retries=retries)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

# --- Circuit Breaker: Automatically avoid unresponsive providers for 60s instead of freezing ---
_PROVIDER_HEALTH = {}
def is_provider_available(provider_name: str) -> bool:
    down_until = _PROVIDER_HEALTH.get(provider_name.lower(), 0)
    return time.time() >= down_until

def mark_provider_failure(provider_name: str, cooldown_seconds: int = 60):
    _PROVIDER_HEALTH[provider_name.lower()] = time.time() + cooldown_seconds

def mark_provider_success(provider_name: str):
    _PROVIDER_HEALTH[provider_name.lower()] = 0

REALISTIC_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

DEFAULT_HEADERS = {
    'User-Agent': REALISTIC_USER_AGENT,
    'Accept': '*/*',
    'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
    'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(BASE_DIR)

def get_db_path():
    candidates = [
        os.path.join(BASE_DIR, 'senadizinet.db'),
        os.path.join(SCRATCH_DIR, 'senadizinet.db'),
        os.path.join(SCRATCH_DIR, 'senadizi', 'senadizinet.db'),
        os.path.join(os.path.dirname(SCRATCH_DIR), 'senadizinet.db'),
        os.path.join(os.path.dirname(SCRATCH_DIR), 'senadizi', 'senadizinet.db'),
        os.path.join(os.getcwd(), 'senadizinet.db'),
        '/opt/render/project/src/app/senadizinet.db',
        '/opt/render/project/src/senadizinet.db',
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return os.path.join(BASE_DIR, 'senadizinet.db')

DB_PATH = get_db_path()
TOKEN_FILE = os.path.join(BASE_DIR, 'tokens.json')

def is_jwt_valid(token: str) -> bool:
    if not token:
        return False
    clean = token.replace('Bearer ', '').strip()
    parts = clean.split('.')
    if len(parts) != 3:
        return False
    try:
        payload = json.loads(base64.b64decode(parts[1] + '===').decode('utf-8'))
        exp = payload.get('exp', 0)
        return exp > time.time() + 60
    except Exception:
        return False


class TokenVault:
    """Persistent token & bypass vault for all supported platforms with auto-extraction."""
    def __init__(self):
        self.data = {
            'dramacix': {'enabled': True, 'cookie': '', 'status': 'Aktif'},
            'dramadizilerim': {'enabled': True, 'cookie': '', 'status': 'Aktif'},
            'dramaflix': {'enabled': True, 'cookie': '', 'auth_token': '', 'status': 'Aktif VIP'},
            'dramakolik': {'enabled': True, 'cookie': '', 'status': 'Aktif'},
            'liderdrama': {'enabled': True, 'cookie': '', 'status': 'Aktif'}
        }
        self.load()

    def load(self):
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.data.update(saved)
            except Exception:
                pass

    def save(self):
        try:
            with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _extract_chrome_token(self) -> str:
        ls_dir = os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Local Storage', 'leveldb')
        if not os.path.exists(ls_dir):
            return ''
        now = time.time()
        best_token = ''
        max_exp = 0
        try:
            for f in os.listdir(ls_dir):
                if not f.endswith(('.log', '.ldb')):
                    continue
                fp = os.path.join(ls_dir, f)
                try:
                    with open(fp, 'rb') as lbf:
                        content = lbf.read().decode('latin1', errors='ignore')
                    for j in re.findall(r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+', content):
                        parts = j.split('.')
                        try:
                            payload = json.loads(base64.b64decode(parts[1] + '===').decode('utf-8'))
                            exp = payload.get('exp', 0)
                            if exp > now and exp > max_exp:
                                max_exp = exp
                                best_token = f'Bearer {j}'
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass
        return best_token

    def get_token(self, platform: str) -> str:
        plat = platform.lower()
        plat_data = self.data.get(plat, {})
        cur = plat_data.get('cookie') or plat_data.get('auth_token') or ''
        if plat == 'dramaflix':
            if not is_jwt_valid(cur):
                fresh = self._extract_chrome_token()
                if fresh:
                    cur = fresh
                    self.data['dramaflix']['cookie'] = fresh
                    self.data['dramaflix']['auth_token'] = fresh
                    self.data['dramaflix']['status'] = 'Aktif VIP (Otomatik Chrome)'
                    self.save()
        return cur

    def set_token(self, platform: str, token: str):
        if platform.lower() in self.data:
            self.data[platform.lower()]['cookie'] = token
            self.save()

token_vault = TokenVault()

# --- Normalization & Similarity Matchers (Zero Wrong Drama Matching) ---
def normalize_drama_text(text: str) -> str:
    if not text:
        return ""
    t = text.lower().strip()
    tr_map = str.maketrans('çğıöşüÇĞİÖŞÜ', 'cgiosuCGIOSU')
    t = t.translate(tr_map)
    t = re.sub(r'[\(\[\{].*?[\)\]\}]', ' ', t)
    t = re.sub(r'-(freereels|netshort|pinedrama|storyreel|moboreels|dramawave|shorttv|reelshort|goodshort|dramabox|dramacix|dramadizilerim|dramakolik|liderdrama)(?:-[a-z]{2})?$', '', t)
    t = re.sub(r'-(dublajli|dublaj|altyazili|tr|izle|full|hd)$', '', t)
    t = re.sub(r'^(dublajli-|dublaj-|altyazili-)', '', t)
    t = re.sub(r'[^a-z0-9\s]', ' ', t)
    return ' '.join(t.split())

def is_similar_series(orig_title: str, orig_slug: str, cand_title: str, cand_slug: str) -> bool:
    """Strict similarity checker to guarantee episode unlocks match the exact same series."""
    # Strict Dubbing Distinction: A dubbed drama must NEVER match a non-dubbed (subtitled) drama!
    raw1 = f"{orig_title} {orig_slug}".lower()
    raw2 = f"{cand_title} {cand_slug}".lower()
    is_dub1 = ('dublaj' in raw1 or 'dublajli' in raw1)
    is_dub2 = ('dublaj' in raw2 or 'dublajli' in raw2)
    if is_dub1 != is_dub2:
        return False

    t1 = normalize_drama_text(orig_title)
    t2 = normalize_drama_text(cand_title)
    s1 = normalize_drama_text(orig_slug.replace('-', ' '))
    s2 = normalize_drama_text(cand_slug.replace('-', ' '))

    if not t1 and s1: t1 = s1
    if not t2 and s2: t2 = s2

    # Exact or substring match on title or slug
    if t1 and t2:
        if t1 == t2 or t1 in t2 or t2 in t1:
            return True
    if s1 and s2:
        if s1 == s2 or s1 in s2 or s2 in s1:
            return True

    # Sequence matcher ratio
    ratio_t = difflib.SequenceMatcher(None, t1, t2).ratio() if t1 and t2 else 0.0
    ratio_s = difflib.SequenceMatcher(None, s1, s2).ratio() if s1 and s2 else 0.0

    if ratio_t >= 0.70 or ratio_s >= 0.70:
        return True

    # Token overlap check
    words1 = set(t1.split()) | set(s1.split())
    words2 = set(t2.split()) | set(s2.split())
    noise = {'bir', 've', 'ile', 'veya', 'icin', 'kiz', 'kizi', 'ask', 'aski', 'kral', 'kralice', 'son', 'ilk'}
    sig1 = {w for w in words1 if len(w) > 2 and w not in noise}
    sig2 = {w for w in words2 if len(w) > 2 and w not in noise}

    if sig1 and sig2:
        overlap = len(sig1 & sig2) / min(len(sig1), len(sig2))
        if overlap >= 0.60:
            return True

    return False

def clean_slug_variations(slug: str) -> list:
    slug = slug.strip().lower()
    is_dub = ('dublaj' in slug or 'dublajli' in slug)
    variations = [slug]
    s1 = re.sub(r'-(freereels|netshort|pinedrama|storyreel|moboreels|dramawave|shorttv|reelshort|goodshort|dramabox)-tr$', '', slug)
    if s1 not in variations: variations.append(s1)

    if not is_dub:
        s2 = re.sub(r'-(altyazili|tr|izle)$', '', s1)
        if s2 not in variations: variations.append(s2)
        out = []
        for s in variations:
            if s not in out: out.append(s)
            for suf in ['-tr', '-altyazili']:
                cand = s + suf
                if cand not in out: out.append(cand)
        return out
    else:
        # If dubbed, only vary suffixes while strictly keeping dublajli intact
        out = [slug]
        base_no_dub = re.sub(r'-(dublajli|dublaj)$', '', slug)
        for suf in ['-dublajli', '-dublaj', '-dublajli-tr', 'dublajli']:
            cand = base_no_dub + suf
            if cand not in out: out.append(cand)
        return out

def safe_b64decode(s: str) -> str:
    if not s:
        return ''
    try:
        if 'url=' in s:
            s = s.split('url=')[1].split('&')[0]
        s = urllib.parse.unquote(s).strip()
        rem = len(s) % 4
        if rem != 0:
            s += '=' * (4 - rem)
        dec = base64.b64decode(s).decode('utf-8', errors='ignore')
        dec = dec.split('\x00')[0].strip()
        dec = re.sub(r'[\s=\x00]+$', '', dec)
        return dec if dec.startswith('http') else s
    except Exception:
        return s

def unwrap_stream_url(url: str) -> str:
    if not url:
        return ''
    url = str(url).strip()
    url = re.sub(r'[\s=\x00]+$', '', url)
    url = re.sub(r'(\.(?:m3u8|mp4|ts|m3u))(=+|\s+)+$', r'\1', url)
    if 'dramaloji.com/api/stream?u=' in url or '/api/stream?u=' in url or '/api/stream/proxy?url=' in url:
        try:
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            if 'u' in qs and qs['u']:
                return unwrap_stream_url(qs['u'][0])
            if 'url' in qs and qs['url']:
                return unwrap_stream_url(qs['url'][0])
        except Exception:
            pass
    return url

def is_valid_stream_url(url: str) -> bool:
    """Checks whether a URL is an actual playable video stream (M3U8/MP4/HLS) and not a website HTML page."""
    if not url or not isinstance(url, str):
        return False
    u = str(url).strip()
    if not (u.startswith('http://') or u.startswith('https://')):
        return False
    u_low = u.lower()
    # Website HTML page URLs are never video streams
    if any(p in u_low for p in ['/dizi/', '/izle/', 'dramacix.com/dizi', 'dramadizilerim.com/dizi', 'dramadizilerim.com/izle', 'dramaflix.net/tr/drama']):
        return False
    # Valid stream signatures
    valid_markers = ['.m3u8', '.mp4', '.ts', '/e/m/', 'video', 'stream', 'media', 'hls', '_s=', '_t=', 'cdn', 'narto-drama', 'mydramawave', 'akamaized', 'cloudfront']
    return any(m in u_low for m in valid_markers)

def convert_vtt_to_srt(vtt_text: str) -> str:
    if not vtt_text or not vtt_text.strip():
        return ''
    text = vtt_text.replace('\r\n', '\n').strip()
    time_pattern = re.compile(r'(\d{1,2}:)?(\d{2}):(\d{2})[\.,](\d{3})\s*-->\s*(\d{1,2}:)?(\d{2}):(\d{2})[\.,](\d{3})')
    
    def format_time_part(hours, minutes, seconds, millis):
        h = int(hours.rstrip(':')) if hours else 0
        return f"{h:02d}:{int(minutes):02d}:{int(seconds):02d},{int(millis):03d}"

    blocks = re.split(r'\n\s*\n', text)
    out_blocks = []
    idx = 1

    for block in blocks:
        block_lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not block_lines:
            continue
        time_line_idx = -1
        m = None
        for i, bl in enumerate(block_lines):
            m_test = time_pattern.search(bl)
            if m_test and '-->' in bl:
                time_line_idx = i
                m = m_test
                break
        if time_line_idx == -1 or not m:
            continue
        s_h, s_m, s_s, s_ms, e_h, e_m, e_s, e_ms = m.groups()
        start_ts = format_time_part(s_h, s_m, s_s, s_ms)
        end_ts = format_time_part(e_h, e_m, e_s, e_ms)
        text_lines = block_lines[time_line_idx + 1:]
        clean_text_lines = [re.sub(r'<[^>]+>', '', tl).strip() for tl in text_lines if not any(tl.startswith(k) for k in ['NOTE', 'STYLE', 'REGION']) and re.sub(r'<[^>]+>', '', tl).strip()]
        if clean_text_lines:
            sub_body = '\n'.join(clean_text_lines)
            out_blocks.append(f"{idx}\n{start_ts} --> {end_ts}\n{sub_body}")
            idx += 1

    return '\n\n'.join(out_blocks).strip()

def convert_srt_to_vtt(srt_text: str) -> str:
    if not srt_text or not srt_text.strip():
        return "WEBVTT\n\n"
    text = srt_text.replace('\r\n', '\n').strip()
    time_pat = re.compile(r'(\d{2}:\d{2}:\d{2})[,\.](\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2})[,\.](\d{3})')
    out = ["WEBVTT\n"]
    for line in text.split('\n'):
        stripped = line.strip()
        m = time_pat.search(stripped)
        if m:
            s_time, s_ms, e_time, e_ms = m.groups()
            out.append(f"{s_time}.{s_ms} --> {e_time}.{e_ms}")
        else:
            out.append(stripped)
    return '\n'.join(out).strip() + '\n'


# =========================================================================
# 1. DRAMADIZILERIM API
# =========================================================================
class DramaDizilerimAPI:
    """Scraper and stream extractor for dramadizilerim.com"""
    def __init__(self, user_cookie=None):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.headers['Referer'] = 'https://dramadizilerim.com/'
        self.session.headers['Origin'] = 'https://dramadizilerim.com'

    def _request(self, method, url, **kwargs):
        kwargs.setdefault('timeout', 5.0)
        try:
            from curl_cffi import requests as c_requests
            res = c_requests.request(method, url, impersonate='chrome120', **kwargs)
            if res.status_code == 200:
                return res
        except Exception:
            pass
        try:
            res = self.session.request(method, url, **kwargs)
            if res.status_code == 200:
                return res
        except Exception:
            pass
        return None

    def extract_slug(self, url_or_slug: str) -> str:
        if not url_or_slug: return ''
        url_or_slug = url_or_slug.strip().rstrip('/')
        m = re.search(r'dramadizilerim\.com/(?:[a-z]{2}/)?(?:dizi|izle|drama|shorts)/([^/?#]+)', url_or_slug)
        if m: return m.group(1).rstrip('/')
        return url_or_slug.split('/')[-1].split('?')[0].split('#')[0].strip().rstrip('/')

    def scan_series(self, url_or_slug: str, user_cookie=None) -> dict:
        slug = self.extract_slug(url_or_slug)
        if not slug: raise ValueError('Geçerli bir DramaDizilerim dizi linki bulunamadı.')
        target_url = f'https://dramadizilerim.com/dizi/{slug}'
        res = self._request('GET', target_url)
        if not res or res.status_code != 200:
            target_url = f'https://dramadizilerim.com/izle/{slug}?s=1&e=1'
            res = self._request('GET', target_url)
            if not res or res.status_code != 200:
                raise ValueError(f"DramaDizilerim üzerinde dizi bulunamadı: {slug}")

        soup = BeautifulSoup(res.text, 'html.parser')
        title = ''
        h1 = soup.find('h1') or soup.find('meta', property='og:title')
        if h1:
            title = h1.get_text(strip=True) if hasattr(h1, 'get_text') else h1.get('content', '')
            title = re.sub(r'izle|türkçe|altyazılı|dublajlı|dramadizilerim', '', title, flags=re.IGNORECASE).strip(' -:|')
        if not title: title = slug.replace('-', ' ').title()

        episodes = []
        for i in range(1, 150):
            ep_watch = f'https://dramadizilerim.com/izle/{slug}?s=1&e={i}'
            episodes.append({
                'id': i, 'episode_number': i, 'title': f'{i}. Bölüm',
                'url': ep_watch, 'watch_url': ep_watch, 'slug': slug,
                'locked': False, 'is_free': True, 'requires_vip': False, 'subtitles': []
            })

        return {'slug': slug, 'title': title, 'platform': 'DramaDizilerim', 'total_episodes': len(episodes), 'episodes': episodes}

    def resolve_episode_stream(self, episode_data_or_url: any, user_cookie=None) -> tuple:
        watch_url = episode_data_or_url if isinstance(episode_data_or_url, str) else (episode_data_or_url.get('url') or episode_data_or_url.get('watch_url'))
        if not watch_url:
            return None, []
        res = self._request('GET', watch_url)
        if not res or res.status_code != 200:
            return None, []
        soup = BeautifulSoup(res.text, 'html.parser')

        # 1. Check iframes (embed.php)
        for ifr in soup.find_all('iframe'):
            src = ifr.get('src', '')
            if 'embed.php' in src or 'embed' in src:
                if src.startswith('/'):
                    src = 'https://dramadizilerim.com' + src
                r_emb = self._request('GET', src, headers={'Referer': watch_url})
                if r_emb and r_emb.status_code == 200:
                    m_src = re.search(r'(?:var|let|const)\s+source\s*=\s*["\']([^"\']+)["\']', r_emb.text)
                    v_url = m_src.group(1) if m_src else None
                    if not v_url:
                        m_m3u8 = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', r_emb.text)
                        if m_m3u8:
                            v_url = m_m3u8[0]

                    subs = []
                    soup_emb = BeautifulSoup(r_emb.text, 'html.parser')
                    for tr in soup_emb.find_all('track'):
                        tsrc = tr.get('src', '')
                        if tsrc:
                            if tsrc.startswith('/'):
                                tsrc = 'https://dramadizilerim.com' + tsrc
                            elif not tsrc.startswith('http'):
                                tsrc = 'https://dramadizilerim.com/' + tsrc.lstrip('/')
                            direct_u = None
                            m_tok = re.search(r'token=([^&"\'<>]+)', tsrc)
                            if m_tok:
                                try:
                                    raw_b64 = urllib.parse.unquote(m_tok.group(1))
                                    payload_json = json.loads(base64.b64decode(raw_b64).decode('utf-8'))
                                    d_inner = payload_json.get('data')
                                    if isinstance(d_inner, str):
                                        d_inner = json.loads(d_inner)
                                    if isinstance(d_inner, dict) and d_inner.get('url'):
                                        direct_u = d_inner['url']
                                except Exception:
                                    pass
                            if direct_u:
                                subs.append({'url': direct_u, 'language': 'tr', 'label': 'Türkçe'})
                            subs.append({'url': tsrc, 'language': tr.get('srclang', 'tr'), 'label': tr.get('label', 'Türkçe')})

                    if not subs:
                        m_trk = re.findall(r'(?:src=["\'])([^"\']*caption\.php\?token=[^"\']*)["\']', r_emb.text)
                        for c_url in m_trk:
                            if c_url.startswith('/'): c_url = 'https://dramadizilerim.com' + c_url
                            elif not c_url.startswith('http'): c_url = 'https://dramadizilerim.com/' + c_url.lstrip('/')
                            subs.append({'url': c_url, 'language': 'tr', 'label': 'Türkçe'})

                    m_cap = re.search(r'(?:var|let|const)\s+_captionUrl\s*=\s*["\']([^"\']+)["\']', r_emb.text)
                    if m_cap and m_cap.group(1):
                        subs.append({'url': m_cap.group(1), 'language': 'tr', 'label': 'Türkçe'})

                    if v_url:
                        return v_url, subs

        # 2. Check main page scripts & tags
        subs_main = []
        for tr in soup.find_all('track'):
            tsrc = tr.get('src', '')
            if tsrc:
                if tsrc.startswith('/'): tsrc = 'https://dramadizilerim.com' + tsrc
                elif not tsrc.startswith('http'): tsrc = 'https://dramadizilerim.com/' + tsrc.lstrip('/')
                subs_main.append({'url': tsrc, 'language': tr.get('srclang', 'tr'), 'label': tr.get('label', 'Türkçe')})

        m_src = re.search(r'(?:var|let|const)\s+source\s*=\s*["\']([^"\']+)["\']', res.text)
        if m_src:
            return m_src.group(1), subs_main

        for tag in soup.find_all(['video', 'source']):
            src = tag.get('src')
            if src and ('.mp4' in src or '.m3u8' in src):
                return src, subs_main
        m3u8 = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', res.text)
        if m3u8:
            return m3u8[0], subs_main
        mp4 = re.findall(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', res.text)
        if mp4:
            return mp4[0], subs_main
        return None, []


# =========================================================================
_GLOBAL_CDN_CACHE = {
    'cookies': {},
    'expiry': 0.0,
    'lock': threading.Lock()
}

_CDN_TICKET_FILE = os.path.join(os.path.dirname(__file__), 'cdn_ticket.json')

def get_global_cdn_cookies(force=False):
    now = time.time()
    with _GLOBAL_CDN_CACHE['lock']:
        # 1. In-memory cache
        if not force and now < _GLOBAL_CDN_CACHE['expiry'] and _GLOBAL_CDN_CACHE['cookies']:
            return dict(_GLOBAL_CDN_CACHE['cookies'])

        # 2. Disk cache
        if not force and os.path.exists(_CDN_TICKET_FILE):
            try:
                with open(_CDN_TICKET_FILE, 'r', encoding='utf-8') as f:
                    disk_cache = json.load(f)
                if disk_cache and disk_cache.get('cookies'):
                    exp = disk_cache.get('expiry', 0)
                    if now < exp - 30:
                        _GLOBAL_CDN_CACHE['cookies'] = disk_cache['cookies']
                        _GLOBAL_CDN_CACHE['expiry'] = exp
                        return dict(_GLOBAL_CDN_CACHE['cookies'])
            except Exception:
                pass

        vip_token = token_vault.get_token('dramaflix')
        auth_h = {}
        if vip_token:
            tok = vip_token.strip()
            if not tok.startswith('Bearer '):
                tok = f'Bearer {tok}'
            auth_h['Authorization'] = tok

        for d in ['https://dramaflix.net', 'https://dramaflix.cc']:
            headers_ticket = {
                'User-Agent': REALISTIC_USER_AGENT,
                'Referer': f'{d}/',
                'Origin': d,
                **auth_h
            }
            try:
                from curl_cffi import requests as c_requests
                r = c_requests.get(f'{d}/api/cdn-ticket', headers=headers_ticket, timeout=5.0, impersonate='chrome120')
                if r and r.status_code == 200:
                    data = r.json()
                    exp = now + data.get('ttl', 3600) - 60
                    _GLOBAL_CDN_CACHE['expiry'] = exp
                    c_dict = r.cookies.get_dict() if hasattr(r.cookies, 'get_dict') else dict(r.cookies)
                    if c_dict:
                        _GLOBAL_CDN_CACHE['cookies'].update(c_dict)
                        try:
                            with open(_CDN_TICKET_FILE, 'w', encoding='utf-8') as f:
                                json.dump({'cookies': _GLOBAL_CDN_CACHE['cookies'], 'expiry': exp, 'premium': data.get('premium', False)}, f, indent=2)
                        except Exception:
                            pass
                        return dict(_GLOBAL_CDN_CACHE['cookies'])
            except Exception:
                pass

            try:
                r = requests.get(f'{d}/api/cdn-ticket', headers=headers_ticket, timeout=5.0)
                if r and r.status_code == 200:
                    data = r.json()
                    exp = now + data.get('ttl', 3600) - 60
                    _GLOBAL_CDN_CACHE['expiry'] = exp
                    for k, v in r.cookies.items():
                        _GLOBAL_CDN_CACHE['cookies'][k] = v
                    try:
                        with open(_CDN_TICKET_FILE, 'w', encoding='utf-8') as f:
                            json.dump({'cookies': _GLOBAL_CDN_CACHE['cookies'], 'expiry': exp, 'premium': data.get('premium', False)}, f, indent=2)
                    except Exception:
                        pass
                    return dict(_GLOBAL_CDN_CACHE['cookies'])
            except Exception:
                pass

        # Fallback to disk cache if available
        if os.path.exists(_CDN_TICKET_FILE):
            try:
                with open(_CDN_TICKET_FILE, 'r', encoding='utf-8') as f:
                    disk_cache = json.load(f)
                if disk_cache and disk_cache.get('cookies'):
                    _GLOBAL_CDN_CACHE['cookies'] = disk_cache['cookies']
                    _GLOBAL_CDN_CACHE['expiry'] = now + 300
                    return dict(_GLOBAL_CDN_CACHE['cookies'])
            except Exception:
                pass

        if _GLOBAL_CDN_CACHE['cookies']:
            _GLOBAL_CDN_CACHE['expiry'] = now + 300
            return dict(_GLOBAL_CDN_CACHE['cookies'])

        return {}


class DramaFlixAPI:
    """Unified API client for dramaflix.net, dramaflix.cc, dramakolik.co, filmkolik."""
    def __init__(self, user_cookie=None):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.headers['Referer'] = 'https://dramaflix.net/'
        self.session.headers['Origin'] = 'https://dramaflix.net'
        self.user_cookie = user_cookie or token_vault.get_token('dramaflix')
        self._apply_user_cookie()

    @property
    def cdn_cookies(self):
        return get_global_cdn_cookies()

    def _apply_user_cookie(self):
        tok = self.user_cookie or token_vault.get_token('dramaflix')
        if not tok:
            return
        cookie_val = tok.strip()
        if cookie_val.startswith('Bearer ') or (len(cookie_val) > 30 and ';' not in cookie_val and '=' not in cookie_val):
            token = cookie_val.replace('Bearer ', '').strip()
            self.session.headers['Authorization'] = f'Bearer {token}'
        else:
            self.session.headers['Cookie'] = cookie_val

    def set_user_cookie(self, user_cookie: str):
        if user_cookie:
            self.user_cookie = user_cookie.strip()
            self._apply_user_cookie()

    def _get(self, url, **kwargs):
        self._apply_user_cookie()
        kwargs.setdefault('timeout', 5.0)
        headers = dict(self.session.headers)
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
        cookies = self.cdn_cookies
        if cookies and 'Cookie' not in headers:
            headers['Cookie'] = '; '.join(f"{k}={v}" for k, v in cookies.items())
        try:
            from curl_cffi import requests as c_requests
            res = c_requests.get(url, headers=headers, impersonate='chrome120', **kwargs)
            if res.status_code == 200:
                return res
        except Exception:
            pass
        try:
            return self.session.get(url, headers=headers, **kwargs)
        except Exception:
            return None

    def refresh_cdn_ticket(self, force=False):
        c = get_global_cdn_cookies(force=force)
        return bool(c)

    def extract_slug(self, url_or_slug: str) -> str:
        if not url_or_slug: return ''
        url_or_slug = url_or_slug.strip().rstrip('/')
        m = re.search(r'(?:dramaflix\.[a-z]+|dramakolik\.[a-z]+|filmkolik\.[a-z]+)/(?:[a-z]{2}/)?(?:drama|dizi|izle|shorts|series|show)/([^/?#]+)', url_or_slug)
        if m: return m.group(1).rstrip('/')
        m2 = re.search(r'/(?:[a-z]{2}/)?(?:drama|dizi|izle|shorts|series|show)/([^/?#]+)', url_or_slug)
        if m2: return m2.group(1).rstrip('/')
        return url_or_slug.split('/')[-1].split('?')[0].split('#')[0].strip().rstrip('/')

    def scan_series(self, url_or_slug: str, user_cookie=None) -> dict:
        if user_cookie:
            self.set_user_cookie(user_cookie)
        slug = self.extract_slug(url_or_slug)
        if not slug: raise ValueError('Geçerli bir dizi adı veya linki bulunamadı.')
        self.refresh_cdn_ticket()

        is_dub = ('dublaj' in slug.lower() or 'dublajli' in slug.lower())
        domains = ['https://dramaflix.net', 'https://dramaflix.cc']
        detail_data = None
        series_info = None

        # 1. Direct fetch by slug from REST API
        cands = [slug, slug.replace('-dublajli', 'dublajli'), slug.replace('dublajli', '-dublajli')] if is_dub else [slug, slug + '-dramawave-tr', slug + '-tr']
        for d in domains:
            for s_cand in cands:
                try:
                    r = self._get(f"{d}/api/series/{s_cand}")
                    if r and r.status_code == 200:
                        data = r.json()
                        if data.get('episodes') or data.get('series'):
                            s_obj = data.get('series') or {}
                            t_check = ((s_obj.get('title') or '') + ' ' + s_cand).lower()
                            if is_dub and ('dublaj' not in t_check and 'dublajli' not in t_check):
                                continue
                            detail_data = data
                            slug = s_cand
                            break
                except Exception:
                    pass
            if detail_data:
                break

        # 2. Search by keyword if direct slug fetch didn't return episodes
        if not detail_data or not detail_data.get('episodes'):
            search_queries = [slug.replace('-', ' '), slug]
            for d in domains:
                for q in search_queries:
                    if not q: continue
                    try:
                        r = self._get(f"{d}/api/series?search={requests.utils.quote(q)}")
                        if r and r.status_code == 200:
                            data = r.json()
                            s_list = data.get('series', [])
                            for cand in s_list:
                                if is_similar_series(slug.replace('-', ' '), slug, cand.get('title', ''), cand.get('slug', '')):
                                    series_info = cand
                                    break
                            if series_info:
                                r_det = self._get(f"{d}/api/series/{series_info['slug']}")
                                if r_det and r_det.status_code == 200:
                                    detail_data = r_det.json()
                                    slug = series_info['slug']
                                    break
                    except Exception:
                        pass
                if detail_data and detail_data.get('episodes'):
                    break

        if not detail_data or not detail_data.get('episodes'):
            raise ValueError(f"DramaFlix üzerinde dizi bulunamadı: {slug}")

        s_obj = detail_data.get('series') or series_info or {}
        s_title = s_obj.get('title') or (series_info.get('title') if series_info else '') or slug.replace('-', ' ').title()
        s_cover = s_obj.get('cover_image') or (series_info.get('cover_image') if series_info else '') or ''
        s_prov = s_obj.get('platform') or (series_info.get('platform') if series_info else 'ReelShort')

        raw_eps = detail_data.get('episodes', [])
        episodes = []
        for ep in raw_eps:
            ep_n = int(ep.get('episode_number') or (len(episodes) + 1))
            ep_url = ep.get('url') or ''
            if not ep_url:
                ep_url = f"https://cdn.dramaflix.cc/media/{s_prov}/TR/{slug}/ep_{ep_n}_hls/playlist.m3u8"
            subs = ep.get('subtitles', [])
            if not subs and ep_url and '.m3u8' in ep_url:
                try:
                    parsed_ep = urllib.parse.urlparse(ep_url)
                    base_p = parsed_ep.path.rsplit('/', 1)[0]
                    sub_vtt = urllib.parse.urlunparse((parsed_ep.scheme, parsed_ep.netloc, f"{base_p}/subtitle.vtt", parsed_ep.params, parsed_ep.query, parsed_ep.fragment))
                    subs = [{'language': 'TR', 'url': sub_vtt, 'label': 'TR'}]
                except Exception:
                    pass

            episodes.append({
                'id': ep.get('id') or ep_n,
                'episode_number': ep_n,
                'title': ep.get('title') or f'{ep_n}. Bölüm',
                'url': ep_url,
                'slug': slug,
                'series_title': s_title,
                'locked': False,
                'is_free': True,
                'requires_vip': False,
                'subtitles': subs
            })

        episodes.sort(key=lambda x: x['episode_number'])
        return {
            'slug': slug,
            'title': s_title,
            'cover': s_cover,
            'platform': f'DramaFlix ({s_prov})',
            'total_episodes': len(episodes),
            'episodes': episodes
        }


# =========================================================================
# 3. DRAMACIX API
# =========================================================================
class DramacixAPI:
    """High-speed scraper & direct video resolver for dramacix.com"""
    def __init__(self, user_cookie=None):
        self.session = make_api_session(pool_size=48)
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.headers['Referer'] = 'https://dramacix.com/'
        self.session.headers['Origin'] = 'https://dramacix.com'

    def extract_slug(self, url_or_slug: str) -> str:
        if not url_or_slug: return ''
        url_or_slug = url_or_slug.strip().rstrip('/')
        m = re.search(r'dramacix\.[a-z]+/(?:[a-z]{2}/)?(?:dizi|izle|kisa-dizi|drama|shorts)/([^/?#]+)', url_or_slug)
        if m:
            slug = m.group(1)
            slug = re.sub(r'-(?:sezon-\d+-)?bolum-\d+.*$', '', slug, flags=re.IGNORECASE)
            return slug
        m2 = re.search(r'/(?:[a-z]{2}/)?(?:dizi|izle|kisa-dizi|drama|shorts)/([^/?#]+)', url_or_slug)
        if m2:
            slug = m2.group(1)
            slug = re.sub(r'-(?:sezon-\d+-)?bolum-\d+.*$', '', slug, flags=re.IGNORECASE)
            return slug
        return url_or_slug.split('/')[-1].split('?')[0].split('#')[0].strip().rstrip('/')

    def search_series(self, query: str, is_dub: bool = False) -> list:
        if not is_provider_available('dramacix'):
            return []
        clean = re.sub(r'[^a-zA-Z0-9\sğüşıöçĞÜŞİÖÇ]', ' ', str(query)).strip()
        words = [w for w in clean.split() if len(w) > 2]
        if not words:
            words = clean.split()
        if not words:
            return []

        search_terms = []
        search_terms.append(' '.join(words[:3]))
        if len(words) > 1:
            search_terms.append(' '.join(words[:2]))
        # Clean common Turkish word suffixes (prensin -> prens, sovalyesi -> sovalye)
        stemmed = [re.sub(r'(in|nin|un|nun|si|su|lar|ler|den|dan|e|a)$', '', w) for w in words if len(w) > 3]
        if stemmed and len(stemmed) >= 2:
            search_terms.append(' '.join(stemmed[:2]))

        candidates = set()
        for st in search_terms:
            if not st:
                continue
            try:
                url = f'https://dramacix.com/ara?q={requests.utils.quote(st)}'
                r = self.session.get(url, timeout=(2.0, 3.0))
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    for a in soup.find_all('a', href=re.compile(r'/dizi/')):
                        href = a.get('href', '')
                        cand_slug = href.split('/dizi/')[-1].strip('/')
                        if cand_slug:
                            candidates.add(cand_slug)
                    mark_provider_success('dramacix')
                    if len(candidates) >= 6:
                        break
            except Exception:
                mark_provider_failure('dramacix', 60)
                break

        if not candidates:
            return []

        # Rank candidates using intelligent similarity scoring
        q_norm = normalize_drama_text(query)
        q_words = set(q_norm.split())
        ranked = []
        for cand in candidates:
            t_norm = normalize_drama_text(cand.replace('-', ' '))
            t_words = set(t_norm.split())
            cand_is_dub = ('dublaj' in cand.lower())
            
            common = q_words & t_words
            score = len(common) / max(len(q_words), 1)
            if q_norm and q_norm in t_norm:
                score += 1.0
            if is_dub == cand_is_dub:
                score += 0.3
            elif is_dub and not cand_is_dub:
                score -= 0.5
            ranked.append((cand, score))

        ranked.sort(key=lambda x: x[1], reverse=True)
        return [c for c, sc in ranked if sc >= 0.3]

    def scan_series(self, url_or_slug: str, user_cookie=None) -> dict:
        if not is_provider_available('dramacix'):
            return None
        slug = self.extract_slug(url_or_slug)
        if not slug: return None
        is_dub = ('dublaj' in str(url_or_slug).lower() or 'dublaj' in slug.lower())

        html_text = ""
        candidates = [slug]
        clean_base = re.sub(r'-(dublajli|dublaj|altyazili|tr)$', '', slug)
        for cand_s in [clean_base, f"{clean_base}-dublajli"]:
            if cand_s not in candidates:
                candidates.append(cand_s)

        for cand in candidates[:2]:
            try:
                r = self.session.get(f'https://dramacix.com/dizi/{cand}', timeout=(2.5, 3.5))
                if r.status_code == 200 and ('DH_CONFIG' in r.text or 'diziBaslik' in r.text or 'ITEMS' in r.text or 'epList' in r.text):
                    html_text = r.text
                    slug = cand
                    mark_provider_success('dramacix')
                    break
            except Exception:
                mark_provider_failure('dramacix', 60)
                break

        # 2. If direct slug fetch failed, run search on DramaCix
        if not html_text:
            search_slugs = self.search_series(url_or_slug, is_dub=is_dub)
            for cand_slug in search_slugs[:3]:
                try:
                    r = self.session.get(f'https://dramacix.com/dizi/{cand_slug}', timeout=(2.0, 3.0))
                    if r.status_code == 200 and ('DH_CONFIG' in r.text or 'diziBaslik' in r.text or 'ITEMS' in r.text or 'epList' in r.text):
                        html_text = r.text
                        slug = cand_slug
                        mark_provider_success('dramacix')
                        break
                except Exception:
                    pass

        if not html_text:
            return None

        soup = BeautifulSoup(html_text, 'html.parser')
        title = ''
        cover = ''
        episodes = []

        # 1. Check window.DH_CONFIG (Modern Dramacix architecture)
        m_dh = re.search(r'window\.DH_CONFIG\s*=\s*(\{.*?\});', html_text)
        if m_dh:
            try:
                dh = json.loads(m_dh.group(1))
                if dh.get('baslik'):
                    title = dh.get('baslik')
                if dh.get('poster'):
                    cover = dh.get('poster')
                if dh.get('slug'):
                    slug = dh.get('slug')

                items_list = dh.get('items') or []
                items_map = {}
                for it in items_list:
                    ep_n = int(it.get('ep') or (it.get('idx', 0) + 1))
                    items_map[ep_n] = it

                raw_eplist = dh.get('epList') or []
                for ep_raw in raw_eplist:
                    ep_num = int(ep_raw.get('episode_number', len(episodes) + 1))
                    it_info = items_map.get(ep_num, {})
                    episodes.append({
                        'id': ep_num,
                        'episode_number': ep_num,
                        'title': ep_raw.get('title') or f'{ep_num}. Bölüm',
                        'url': f'https://dramacix.com/dizi/{slug}',
                        'slug': slug,
                        't': it_info.get('t', ''),
                        'locked': False,
                        'is_free': True,
                        'requires_vip': False,
                        'subtitles': it_info.get('subs', [])
                    })

                if not episodes and items_map:
                    for ep_n, it_info in sorted(items_map.items()):
                        episodes.append({
                            'id': ep_n,
                            'episode_number': ep_n,
                            'title': f'{ep_n}. Bölüm',
                            'url': f'https://dramacix.com/dizi/{slug}',
                            'slug': slug,
                            't': it_info.get('t', ''),
                            'locked': False,
                            'is_free': True,
                            'requires_vip': False,
                            'subtitles': it_info.get('subs', [])
                        })
            except Exception:
                pass

        # 2. Fallback to legacy parser if DH_CONFIG didn't populate episodes
        if not episodes:
            m_title = re.search(r'const diziBaslik\s*=\s*["\'](.*?)["\'];', html_text)
            if m_title and m_title.group(1):
                try: title = json.loads(f'"{m_title.group(1)}"')
                except Exception: title = m_title.group(1)

            m_poster = re.search(r'const diziPoster\s*=\s*["\'](.*?)["\'];', html_text)
            if m_poster and m_poster.group(1):
                cover = m_poster.group(1).replace(r'\/', '/')

            items_map = {}
            m_items = re.search(r'(?:const\s+ITEMS\s*=\s*|["\']ITEMS["\']\s*:\s*)(\[\s*\{.*?\}\s*\])', html_text, re.DOTALL)
            if m_items:
                try:
                    for it in json.loads(m_items.group(1)):
                        ep_n = int(it.get('ep') or (it.get('idx', 0) + 1))
                        items_map[ep_n] = it
                except Exception:
                    pass

            m_eplist = re.search(r'(?:const\s+epList\s*=\s*|["\']epList["\']\s*:\s*)(\[\s*\{.*?\}\s*\])', html_text, re.DOTALL)
            if m_eplist:
                try:
                    for ep_raw in json.loads(m_eplist.group(1)):
                        ep_num = int(ep_raw.get('episode_number', len(episodes) + 1))
                        it_info = items_map.get(ep_num, {})
                        episodes.append({
                            'id': ep_num, 'episode_number': ep_num, 'title': ep_raw.get('title') or f'{ep_num}. Bölüm',
                            'url': f'https://dramacix.com/dizi/{slug}', 'slug': slug,
                            't': it_info.get('t', ''), 'locked': False, 'is_free': True, 'requires_vip': False,
                            'subtitles': it_info.get('subs', [])
                        })
                except Exception:
                    pass

            if not episodes and items_map:
                for ep_n, it_info in sorted(items_map.items()):
                    episodes.append({
                        'id': ep_n, 'episode_number': ep_n, 'title': f'{ep_n}. Bölüm',
                        'url': f'https://dramacix.com/dizi/{slug}', 'slug': slug,
                        't': it_info.get('t', ''), 'locked': False, 'is_free': True, 'requires_vip': False,
                        'subtitles': it_info.get('subs', [])
                    })

        if not title:
            h1 = soup.find('h1') or soup.find('meta', property='og:title')
            if h1:
                title = h1.get_text(strip=True) if hasattr(h1, 'get_text') else h1.get('content', '')
                title = re.sub(r'izle|türkçe|altyazılı|dublajlı|dramacix', '', title, flags=re.IGNORECASE).strip(' -:|')
        if not title:
            title = slug.replace('-', ' ').title()

        if cover and not cover.startswith('http'):
            cover = urllib.parse.urljoin('https://dramacix.com', cover)

        episodes.sort(key=lambda x: x['episode_number'])
        return {'slug': slug, 'title': title, 'cover': cover, 'cover_image': cover, 'platform': 'DramaCix', 'total_episodes': len(episodes), 'episodes': episodes}


    def resolve_episode_stream(self, episode_data_or_url: any, user_cookie=None) -> tuple:
        slug = ''
        ep_num = 1
        t_token = ''
        subtitles = []

        if isinstance(episode_data_or_url, dict):
            slug = episode_data_or_url.get('slug') or ''
            ep_num = int(episode_data_or_url.get('episode_number') or 1)
            t_token = episode_data_or_url.get('t', '')
            subtitles = episode_data_or_url.get('subtitles', [])
        else:
            watch_url = str(episode_data_or_url)
            slug = self.extract_slug(watch_url)
            m_ep = re.search(r'bolum[-_ ]*(\d+)', watch_url, re.I)
            if m_ep: ep_num = int(m_ep.group(1))

        if not is_provider_available('dramacix'):
            return None, []

        if not slug:
            return None, []

        page_url = f'https://dramacix.com/dizi/{slug}'
        headers = dict(DEFAULT_HEADERS)
        headers['Referer'] = page_url
        headers['Origin'] = 'https://dramacix.com'

        def query_video_api(token):
            if not token:
                return None, []
            for g_param in ['&g=1', '']:
                api_url = f'https://dramacix.com/api/video?slug={slug}&ep={ep_num}&t={token}{g_param}'
                try:
                    r_api = self.session.get(api_url, headers=headers, timeout=(2.5, 3.5))
                    if r_api.status_code == 200:
                        data = r_api.json()
                        v_url = data.get('url', '')
                        if v_url:
                            v_url = safe_b64decode(v_url)
                            if is_valid_stream_url(v_url):
                                raw_subs = data.get('subs', []) or subtitles
                                subs_out = [{'language': (s.get('lang') or 'tr').lower(), 'url': safe_b64decode(s.get('url', '')), 'label': s.get('lang') or 'TR'} for s in raw_subs if s.get('url')]
                                # Ensure Turkish subtitle is included if available on CDN
                                has_tr = any('tr' in s.get('language', '') for s in subs_out)
                                if not has_tr and subs_out:
                                    for s in subs_out:
                                        s_url = s.get('url', '')
                                        if '/assets/subtitle/' in s_url:
                                            base_sub = re.sub(r'/[a-zA-Z0-9\-_]+/subtitle\.[a-z]+$', '', s_url)
                                            for tr_variant in ['/tr-TR/subtitle.srt', '/tr/subtitle.srt']:
                                                tr_cand = base_sub + tr_variant
                                                try:
                                                    r_cand = self.session.head(tr_cand, timeout=2.0)
                                                    if r_cand.status_code == 200:
                                                        subs_out.insert(0, {'language': 'tr', 'url': tr_cand, 'label': 'tr-TR'})
                                                        has_tr = True
                                                        break
                                                except Exception:
                                                    pass
                                            if has_tr:
                                                break
                                mark_provider_success('dramacix')
                                return v_url, subs_out
                except Exception:
                    mark_provider_failure('dramacix', 60)
                    pass
            return None, []

        # 1. Try with existing token if provided
        if t_token:
            v_url, subs = query_video_api(t_token)
            if v_url:
                return v_url, subs

        # 2. Freshly fetch dynamic token from page
        try:
            r = self.session.get(page_url, headers=headers, timeout=(2.5, 3.5))
            if r.status_code == 200:
                m_items = re.search(r'const ITEMS\s*=\s*(\[.*?\]);', r.text)
                if m_items:
                    items = json.loads(m_items.group(1))
                    found = next((it for it in items if int(it.get('ep', 0)) == ep_num or int(it.get('idx', -1)) + 1 == ep_num), None)
                    if found:
                        fresh_t = found.get('t', '')
                        if not subtitles:
                            subtitles = found.get('subs', [])
                        v_url, subs = query_video_api(fresh_t)
                        if v_url:
                            return v_url, subs
            else:
                mark_provider_failure('dramacix', 60)
        except Exception:
            mark_provider_failure('dramacix', 60)
            pass

        return None, []


# =========================================================================
# 4. LIDERDRAMA API
# =========================================================================
class LiderDramaAPI:
    """Scraper and stream extractor for liderdrama.com"""
    def __init__(self, user_cookie=None):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.headers['Referer'] = 'https://liderdrama.com/'

    def extract_slug(self, url_or_slug: str) -> str:
        if not url_or_slug: return ''
        url_or_slug = url_or_slug.strip().rstrip('/')
        m = re.search(r'liderdrama\.[a-z]+/(?:[a-z]{2}/)?(?:dizi|izle|drama|shorts)/([^/?#]+)', url_or_slug)
        if m: return m.group(1).rstrip('/')
        return url_or_slug.split('/')[-1].split('?')[0].split('#')[0].strip().rstrip('/')

    def scan_series(self, url_or_slug: str, user_cookie=None) -> dict:
        slug = self.extract_slug(url_or_slug)
        if not slug: raise ValueError('Geçerli bir LiderDrama dizi linki bulunamadı.')
        target_url = f'https://liderdrama.com/dizi/{slug}'
        try:
            r = self.session.get(target_url, timeout=2.0)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                title = soup.find('h1')
                t_str = title.get_text(strip=True) if title else slug.replace('-', ' ').title()
                episodes = []
                for a in soup.find_all('a', href=True):
                    if '/bolum-' in a['href'] or 'bolum=' in a['href']:
                        m = re.search(r'bolum[-_ ]*(\d+)', a['href'], re.I)
                        ep_n = int(m.group(1)) if m else (len(episodes) + 1)
                        if not any(e['episode_number'] == ep_n for e in episodes):
                            episodes.append({
                                'id': ep_n, 'episode_number': ep_n, 'title': f'{ep_n}. Bölüm',
                                'url': urllib.parse.urljoin('https://liderdrama.com', a['href']),
                                'slug': slug, 'locked': False, 'is_free': True, 'requires_vip': False, 'subtitles': []
                            })
                episodes.sort(key=lambda x: x['episode_number'])
                return {'slug': slug, 'title': t_str, 'platform': 'LiderDrama', 'total_episodes': len(episodes), 'episodes': episodes}
        except Exception:
            pass
        raise ValueError(f"LiderDrama üzerinde dizi bulunamadı: {slug}")


# =========================================================================
# 5. SENADIZI.COM DEDICATED SCRAPER & RESOLVER
# =========================================================================
class SenaDiziNetAPI:
    """Fast scraper & resolver for senadizi.com / senadizinet platform."""
    def __init__(self, user_cookie=None):
        self.session = make_api_session(pool_size=32)
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.headers['Referer'] = 'https://senadizi.com/'
        self.session.headers['Origin'] = 'https://senadizi.com'
        self.user_cookie = user_cookie

    def extract_slug(self, url_or_slug: str) -> str:
        if not url_or_slug:
            return ''
        url_or_slug = url_or_slug.strip().rstrip('/')
        m = re.search(r'senadizi\.(?:com|net)/(?:[a-z]{2}/)?(?:dizi|izle|drama|shorts)/([^/?#]+)', url_or_slug)
        if m:
            slug = m.group(1)
            slug = re.sub(r'-(?:sezon-\d+-)?bolum-\d+.*$', '', slug, flags=re.IGNORECASE)
            return slug
        m2 = re.search(r'/(?:[a-z]{2}/)?(?:dizi|izle|drama|shorts)/([^/?#]+)', url_or_slug)
        if m2:
            slug = m2.group(1)
            slug = re.sub(r'-(?:sezon-\d+-)?bolum-\d+.*$', '', slug, flags=re.IGNORECASE)
            return slug
        return url_or_slug.split('/')[-1].split('?')[0].split('#')[0].strip().rstrip('/')

    def scan_series(self, url_or_slug: str, user_cookie=None) -> dict:
        slug = self.extract_slug(url_or_slug)
        if not slug:
            raise ValueError('Geçerli bir SenaDizi linki bulunamadı.')

        # 1. First check local SQLite database (instant 0ms)
        try:
            if os.path.exists(DB_PATH):
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('SELECT id, title, slug, poster_url, description FROM series WHERE slug = ?', (slug,))
                row = c.fetchone()
                if not row:
                    for sv in clean_slug_variations(slug)[:3]:
                        c.execute('SELECT id, title, slug, poster_url, description FROM series WHERE slug = ?', (sv,))
                        row = c.fetchone()
                        if row:
                            break
                if row:
                    s_id, s_title, s_slug, s_poster, s_desc = row
                    c.execute('SELECT id, episode_number, title, video_url FROM episodes WHERE season_id IN (SELECT id FROM seasons WHERE series_id = ?) ORDER BY episode_number', (s_id,))
                    ep_rows = c.fetchall()
                    conn.close()
                    if ep_rows:
                        episodes = []
                        for eid, ep_num, ep_t, v_url in ep_rows:
                            episodes.append({
                                'id': ep_num,
                                'episode_number': ep_num,
                                'title': ep_t or f'{ep_num}. Bölüm',
                                'url': v_url or f'https://senadizi.com/dizi/{s_slug}/sezon-1/bolum-{ep_num}',
                                'watch_url': v_url or f'https://senadizi.com/dizi/{s_slug}/sezon-1/bolum-{ep_num}',
                                'slug': s_slug,
                                'locked': False,
                                'is_free': True,
                                'requires_vip': False,
                                'subtitles': []
                            })
                        return {
                            'title': s_title,
                            'slug': s_slug,
                            'description': s_desc or f'{s_title} Türkçe Altyazılı',
                            'cover_image': s_poster or '',
                            'cover': s_poster or '',
                            'platform': 'SenaDizi',
                            'total_episodes': len(episodes),
                            'episodes': episodes
                        }
        except Exception:
            pass

        # 2. Online HTTP query to senadizi.com
        for domain in ['https://senadizi.com', 'https://www.senadizi.com']:
            try:
                r = self.session.get(f'{domain}/dizi/{slug}', timeout=10.0)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    h1 = soup.find('h1')
                    title = h1.get_text(strip=True) if h1 else slug.replace('-', ' ').title()
                    cover = ''
                    img = soup.find('meta', property='og:image') or soup.find('img', class_='poster')
                    if img:
                        cover = img.get('content') or img.get('src') or ''

                    episodes = []
                    ep_links = soup.find_all('a', href=re.compile(r'/bolum-\d+'))
                    for a in ep_links:
                        href = a.get('href', '')
                        m_num = re.search(r'bolum-(\d+)', href)
                        if m_num:
                            num = int(m_num.group(1))
                            episodes.append({
                                'id': num,
                                'episode_number': num,
                                'title': a.get_text(strip=True) or f'{num}. Bölüm',
                                'url': urllib.parse.urljoin(domain, href),
                                'watch_url': urllib.parse.urljoin(domain, href),
                                'slug': slug,
                                'locked': False,
                                'is_free': True,
                                'requires_vip': False,
                                'subtitles': []
                            })
                    if episodes:
                        seen = set()
                        dedup = []
                        for ep in sorted(episodes, key=lambda x: x['episode_number']):
                            if ep['episode_number'] not in seen:
                                seen.add(ep['episode_number'])
                                dedup.append(ep)
                        return {
                            'title': title,
                            'slug': slug,
                            'cover_image': cover,
                            'cover': cover,
                            'platform': 'SenaDizi',
                            'total_episodes': len(dedup),
                            'episodes': dedup
                        }
            except Exception:
                pass

        raise ValueError(f"SenaDizi üzerinde dizi bulunamadı: {slug}")

    def resolve_episode_stream(self, episode_data_or_url: any, user_cookie=None) -> tuple:
        video_url = None
        subtitles = []
        slug = ''
        ep_num = 1
        if isinstance(episode_data_or_url, dict):
            video_url = episode_data_or_url.get('url') or episode_data_or_url.get('video_url')
            subtitles = episode_data_or_url.get('subtitles') or []
            slug = episode_data_or_url.get('slug') or ''
            ep_num = int(episode_data_or_url.get('episode_number') or 1)
        else:
            slug = self.extract_slug(str(episode_data_or_url))
            m = re.search(r'bolum-(\d+)', str(episode_data_or_url))
            if m:
                ep_num = int(m.group(1))

        if video_url and (video_url.startswith('http://') or video_url.startswith('https://')) and not ('/dizi/' in video_url and '/bolum-' in video_url):
            return video_url, subtitles

        # Fallback to local database lookup
        try:
            if os.path.exists(DB_PATH):
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('SELECT video_url FROM episodes WHERE season_id IN (SELECT id FROM seasons WHERE series_id IN (SELECT id FROM series WHERE slug = ?)) AND episode_number = ?', (slug, ep_num))
                row = c.fetchone()
                conn.close()
                if row and row[0] and row[0].startswith('http'):
                    return row[0], subtitles
        except Exception:
            pass

        return None, subtitles


# =========================================================================
# 6. SENADIZI MASTER API (CROSS-PROVIDER UNLOCK & STREAM ENGINE)
# =========================================================================
CROSS_SERIES_CACHE = {}

class SenaDiziAPI:
    """Master orchestrator across SQLite Local DB, SenaDiziNet, DramaFlix, DramaCix, DramaDizilerim, LiderDrama, DramaKolik."""
    def __init__(self, user_cookie=None):
        self.user_cookie = user_cookie or token_vault.get_token('dramaflix')
        self.senadizi_net = SenaDiziNetAPI(user_cookie=self.user_cookie)
        self.dramaflix = DramaFlixAPI(user_cookie=self.user_cookie)
        self.dramacix = DramacixAPI(user_cookie=user_cookie or token_vault.get_token('dramacix'))
        self.dramadizilerim = DramaDizilerimAPI(user_cookie=user_cookie or token_vault.get_token('dramadizilerim'))
        self.liderdrama = LiderDramaAPI(user_cookie=user_cookie or token_vault.get_token('liderdrama'))
        self._sub_series_cache = {}


    def _scan_db(self, query_or_slug: str) -> dict:
        """Instant lookup from local SQLite database with intelligent fuzzy title/token matching and online enrichment."""
        if not os.path.exists(DB_PATH) or not query_or_slug or not query_or_slug.strip():
            return None
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            is_dub = ('dublaj' in query_or_slug.lower() or 'dublajli' in query_or_slug.lower())
            clean_s = self.dramacix.extract_slug(query_or_slug)
            
            # 1. Exact match on clean slug or slug variations
            row = None
            for sv in [clean_s] + clean_slug_variations(clean_s):
                c.execute('SELECT id, title, slug, poster_url, description FROM series WHERE slug = ?', (sv,))
                row = c.fetchone()
                if row:
                    break

            # 2. Intelligent fuzzy title/token match across all series in DB
            if not row:
                c.execute('SELECT id, title, slug, poster_url, description FROM series')
                all_series = c.fetchall()
                
                q_norm = normalize_drama_text(query_or_slug)
                q_words = set(q_norm.split())
                q_clean = q_norm.replace('prensin', 'prens in').replace('babasinin', 'babasi').replace('sovalyesi', 'sovalye')
                q_words_expanded = set(q_clean.split())
                
                best_match = None
                best_score = 0.0

                for s_id, s_title, s_slug, s_poster, s_desc in all_series:
                    t_norm = normalize_drama_text(f"{s_title} {s_slug}")
                    t_words = set(t_norm.split())
                    row_is_dub = ('dublaj' in t_norm)

                    common = (q_words | q_words_expanded) & t_words
                    if not common:
                        continue

                    score = len(common) / max(len(q_words), 1)

                    if is_dub == row_is_dub:
                        score += 0.5
                    elif is_dub and not row_is_dub:
                        score -= 0.5

                    if q_norm in t_norm or q_clean in t_norm:
                        score += 1.0

                    if score > best_score:
                        best_score = score
                        best_match = (s_id, s_title, s_slug, s_poster, s_desc)

                if best_match and best_score >= 0.5:
                    row = best_match

            if row:
                s_id, s_title, s_slug, s_poster, s_desc = row
                
                # Fetch DB episodes
                c.execute('SELECT id, episode_number, title, video_url FROM episodes WHERE season_id IN (SELECT id FROM seasons WHERE series_id = ?) ORDER BY episode_number', (s_id,))
                ep_rows = c.fetchall()
                conn.close()

                episodes = []
                if ep_rows:
                    for eid, ep_num, ep_t, v_url in ep_rows:
                        episodes.append({
                            'id': eid,
                            'episode_number': ep_num,
                            'title': ep_t or f'{ep_num}. Bölüm',
                            'url': v_url,
                            'watch_url': v_url,
                            'slug': s_slug,
                            'locked': False,
                            'is_free': True,
                            'requires_vip': False,
                            'subtitles': []
                        })

                # Check if online providers have a more complete episode list
                clean_b = re.sub(r'[-_]?(?:dublajli|dublaj|altyazili|tr)$', '', s_slug, flags=re.I)
                enrich_cands = [s_slug]
                if 'dublajli' in s_slug:
                    enrich_cands.append(s_slug.replace('dublajli', '-dublajli'))
                    enrich_cands.append(s_slug.replace('-dublajli', 'dublajli'))
                if clean_b:
                    if is_dub or 'dublaj' in str(s_title).lower():
                        enrich_cands.insert(0, f"{clean_b}-dublajli")
                        enrich_cands.insert(1, f"{clean_b}dublajli")
                    else:
                        enrich_cands.insert(0, clean_b)
                if '-bir-kizdublajli' in s_slug:
                    enrich_cands.insert(0, 'ejderha-prens-in-sovalyesi-bir-kiz-dublajli')
                    enrich_cands.insert(1, s_slug.replace('-bir-kizdublajli', '-bir-kiz-dublajli'))

                for ec in enrich_cands:
                    try:
                        res_en = self.dramacix.scan_series(ec)
                        if res_en and res_en.get('episodes') and len(res_en['episodes']) > len(episodes):
                            return res_en
                    except Exception:
                        pass
                    try:
                        res_en_df = self.dramaflix.scan_series(ec)
                        if res_en_df and res_en_df.get('episodes') and len(res_en_df['episodes']) > len(episodes):
                            return res_en_df
                    except Exception:
                        pass

                if episodes:
                    return {
                        'title': s_title,
                        'slug': s_slug,
                        'description': s_desc or f'{s_title} Türkçe Altyazılı',
                        'cover_image': s_poster or '',
                        'platform': 'SenaDizi (Yerel DB)',
                        'total_episodes': len(episodes),
                        'episodes': episodes
                    }
            else:
                conn.close()
        except Exception:
            pass
        return None

    def scan_series(self, url_or_slug: str, user_cookie=None) -> dict:
        raw = url_or_slug.strip()
        if not raw:
            raise ValueError("Lütfen geçerli bir dizi adı veya linki girin.")

        clean_s = self.dramacix.extract_slug(raw)
        is_dub = ('dublaj' in clean_s.lower() or 'dublaj' in raw.lower())

        # 1. DOMAIN SPECIFIC: If user pasted an explicit provider URL, scan that exact provider first!
        if 'dramaflix' in raw or 'dramakolik' in raw or 'filmkolik' in raw:
            try:
                res = self.dramaflix.scan_series(raw, user_cookie=user_cookie or self.user_cookie)
                if res and res.get('episodes'):
                    # Check if DramaCix has more episodes
                    clean_b = re.sub(r'[-_]?(?:dublajli|dublaj|altyazili|tr)$', '', clean_s, flags=re.I)
                    for cand_c in [clean_s, f"{clean_b}-dublajli", clean_b]:
                        try:
                            res_dc = self.dramacix.scan_series(cand_c)
                            if res_dc and res_dc.get('episodes') and len(res_dc['episodes']) > len(res['episodes']):
                                return res_dc
                        except Exception:
                            pass
                    return res
            except Exception:
                pass

        if 'dramacix.com' in raw:
            try:
                res = self.dramacix.scan_series(clean_s, user_cookie=user_cookie or self.user_cookie)
                if res and res.get('episodes'):
                    return res
            except Exception:
                pass

        if 'dramadizilerim.com' in raw:
            try:
                res = self.dramadizilerim.scan_series(clean_s, user_cookie=user_cookie or self.user_cookie)
                if res and res.get('episodes'):
                    return res
            except Exception:
                pass

        if 'liderdrama.com' in raw:
            try:
                res = self.liderdrama.scan_series(clean_s, user_cookie=user_cookie or self.user_cookie)
                if res and res.get('episodes'):
                    return res
            except Exception:
                pass

        if 'senadizi' in raw or 'senadizinet' in raw:
            try:
                res = self.senadizi_net.scan_series(raw, user_cookie=user_cookie or self.user_cookie)
                if res and res.get('episodes'):
                    return res
            except Exception:
                pass

        # 2. LOCAL DB SCAN (Takes 0ms, with fuzzy title matching & automatic online enrichment)
        db_res = self._scan_db(raw)
        if not db_res and clean_s != raw:
            db_res = self._scan_db(clean_s)
        if db_res and db_res.get('episodes'):
            return db_res

        # 3. Cross-provider fallback scan
        if is_dub:
            for provider_fn in [
                lambda: self.dramacix.scan_series(raw, user_cookie=user_cookie or self.user_cookie),
                lambda: self.dramaflix.scan_series(raw, user_cookie=user_cookie or self.user_cookie),
                lambda: self.senadizi_net.scan_series(clean_s, user_cookie=user_cookie or self.user_cookie),
                lambda: self.dramadizilerim.scan_series(clean_s, user_cookie=user_cookie or self.user_cookie),
                lambda: self.liderdrama.scan_series(clean_s, user_cookie=user_cookie or self.user_cookie),
            ]:
                try:
                    res = provider_fn()
                    if res and res.get('episodes'):
                        t_check = ((res.get('title') or '') + ' ' + (res.get('slug') or '')).lower()
                        if 'dublaj' in t_check:
                            return res
                except Exception:
                    pass
        else:
            for provider_fn in [
                lambda: self.dramacix.scan_series(raw, user_cookie=user_cookie or self.user_cookie),
                lambda: self.dramaflix.scan_series(raw, user_cookie=user_cookie or self.user_cookie),
                lambda: self.senadizi_net.scan_series(clean_s, user_cookie=user_cookie or self.user_cookie),
                lambda: self.dramadizilerim.scan_series(clean_s, user_cookie=user_cookie or self.user_cookie),
                lambda: self.liderdrama.scan_series(clean_s, user_cookie=user_cookie or self.user_cookie),
            ]:
                try:
                    res = provider_fn()
                    if res and res.get('episodes'):
                        return res
                except Exception:
                    pass

        raise ValueError(f"'{url_or_slug}' adına veya linkine sahip bir dizi bulunamadı.")

    def resolve_turkish_subtitles(self, series_slug: str, ep_num: int, series_title: str = "") -> list:
        """
        🎯 Kullanıcı Kesin Kuralı:
        '1. bölümden son bölüme kadar indirilen tüm dizilere altyazılı desteği ekle'
        Eğer bir sağlayıcı (örn: DramaCix) belirli bölümlerden sonra (örn: 5. veya 10. bölümden sonra)
        altyazı listesini boş dönerse, çapraz sağlayıcılardan (DramaFlix, orijinal ana dizi, DramaDizilerim, DB)
        ilgili bölümün Türkçe altyazısını bulur.
        """
        base_slug = re.sub(r'-(?:dublajli|dublaj|turkce-dublaj)$', '', str(series_slug or ''), flags=re.I)

        # 1. Dublajlı dizilerde orijinal altyazılı ana diziyi DramaCix üzerinde sorgula (aktifse)
        if base_slug and base_slug != series_slug and is_provider_available('dramacix'):
            try:
                cache_k = f'dc:{base_slug}'
                if cache_k not in self._sub_series_cache:
                    self._sub_series_cache[cache_k] = self.dramacix.scan_series(base_slug)
                dc_res = self._sub_series_cache[cache_k]
                if dc_res and dc_res.get('episodes'):
                    found_ep = next((e for e in dc_res['episodes'] if int(e.get('episode_number') or 0) == ep_num), None)
                    if found_ep:
                        _, dc_subs = self.dramacix.resolve_episode_stream(found_ep)
                        tr_subs = [s for s in (dc_subs or []) if 'tr' in (s.get('language') or s.get('label') or '').lower() or 'türk' in (s.get('label') or '').lower()]
                        if tr_subs:
                            return tr_subs
            except Exception:
                pass

        # 2. DramaFlix üzerinde dizi slug'ı ve base_slug'ı tara
        for test_slug in [series_slug, base_slug]:
            if not test_slug:
                continue
            try:
                cache_k = f'df:{test_slug}'
                if cache_k not in self._sub_series_cache:
                    self._sub_series_cache[cache_k] = self.dramaflix.scan_series(test_slug)
                df_res = self._sub_series_cache[cache_k]
                if df_res and df_res.get('episodes'):
                    found_ep = next((e for e in df_res['episodes'] if int(e.get('episode_number') or 0) == ep_num), None)
                    if found_ep and found_ep.get('subtitles'):
                        tr_subs = [s for s in found_ep['subtitles'] if 'tr' in (s.get('language') or s.get('label') or '').lower() or 'türk' in (s.get('label') or '').lower()]
                        if tr_subs:
                            return tr_subs
            except Exception:
                pass

        # 3. DramaDizilerim üzerinden kontrol et
        for test_slug in [series_slug, base_slug]:
            if not test_slug:
                continue
            try:
                dd_url = f"https://dramadizilerim.com/izle/{test_slug}?s=1&e={ep_num}"
                _, dd_subs = self.dramadizilerim.resolve_episode_stream(dd_url)
                tr_subs = [s for s in (dd_subs or []) if 'tr' in (s.get('language') or s.get('label') or '').lower() or 'türk' in (s.get('label') or '').lower()]
                if tr_subs:
                    return tr_subs
            except Exception:
                pass

        # 4. Yerel SQLite DB üzerinden kontrol et
        for test_slug in [series_slug, base_slug]:
            if not test_slug:
                continue
            try:
                db_res = self._scan_db(test_slug)
                if db_res and db_res.get('episodes'):
                    found_ep = next((e for e in db_res['episodes'] if int(e.get('episode_number') or 0) == ep_num), None)
                    if found_ep and found_ep.get('subtitles'):
                        tr_subs = [s for s in found_ep['subtitles'] if 'tr' in (s.get('language') or s.get('label') or '').lower() or 'türk' in (s.get('label') or '').lower()]
                        if tr_subs:
                            return tr_subs
            except Exception:
                pass

        return []

    def ensure_turkish_subtitles(self, current_subs: list, series_slug: str, ep_num: int, series_title: str = "") -> list:
        """Mevcut altyazı listesinde Türkçe yoksa çapraz kaynaklardan otomatik bulup ekler."""
        subs_list = list(current_subs or [])
        has_tr = False
        for s in subs_list:
            if isinstance(s, dict):
                l = (s.get('language') or s.get('label') or '').lower()
                lb = (s.get('label') or '').lower()
                if 'tr' in l or 'türk' in l or 'tr' in lb or 'tur' in lb:
                    has_tr = True
                    break
            elif isinstance(s, str) and ('tr' in s.lower() or 'tur' in s.lower()):
                has_tr = True
                break
        
        if not has_tr:
            extra = self.resolve_turkish_subtitles(series_slug, ep_num, series_title)
            if extra:
                return extra + [s for s in subs_list if s not in extra]
        return subs_list

    def resolve_episode_stream(self, episode_data: dict, series_slug: str = None, force_refresh: bool = False) -> tuple:
        ep_num = int(episode_data.get('episode_number') or 1)
        ep_slug = series_slug or episode_data.get('slug') or 'dizi'
        ep_title = episode_data.get('title') or f'{ep_num}. Bölüm'
        series_title = episode_data.get('series_title') or ep_slug.replace('-', ' ').title()
        cache_key = f"{ep_slug}:{ep_num}"

        def finalize_stream(v_u, s_list):
            if not v_u:
                return None, []
            u_url = unwrap_stream_url(v_u)
            ensured_subs = self.ensure_turkish_subtitles(s_list, ep_slug, ep_num, series_title)
            CROSS_SERIES_CACHE[cache_key] = (u_url, ensured_subs)
            return u_url, ensured_subs

        raw_url = episode_data.get('url') or episode_data.get('watch_url') or ''

        # 0. PRIMARY: Direct SenaDizi episode resolution
        if 'senadizi' in str(raw_url) or episode_data.get('platform') == 'SenaDizi':
            try:
                v_url, subs = self.senadizi_net.resolve_episode_stream(episode_data)
                if v_url:
                    return finalize_stream(v_url, subs)
            except Exception:
                pass
        
        # 1. PRIMARY: Direct DramaCix episode resolution
        if 'dramacix.com' in str(raw_url) or episode_data.get('t'):
            try:
                dc_data = dict(episode_data)
                if not dc_data.get('slug'):
                    dc_data['slug'] = ep_slug
                v_url, subs = self.dramacix.resolve_episode_stream(dc_data)
                if v_url:
                    return finalize_stream(v_url, subs)
            except Exception:
                pass

        # 2. PRIMARY: Direct DramaDizilerim watch URL
        if raw_url and 'dramadizilerim.com' in str(raw_url):
            try:
                v_url, subs = self.dramadizilerim.resolve_episode_stream(raw_url)
                if v_url:
                    return finalize_stream(v_url, subs)
            except Exception:
                pass

        # 3. PRIMARY: Direct authenticated or public stream from provider
        has_vip = bool(_GLOBAL_CDN_CACHE.get('premium', False) or token_vault.get_token('dramaflix'))
        if raw_url and str(raw_url).startswith('http') and str(raw_url).strip() != '' and str(raw_url) != 'None':
            is_df_url = ('dramaflix' in str(raw_url) or 'dramakolik' in str(raw_url) or 'filmkolik' in str(raw_url))
            if is_df_url and ep_num > 15 and not has_vip:
                # DramaFlix free tier strictly limits to eps 1-15. Without VIP, do NOT return unplayable locked URLs!
                pass
            elif has_vip or '_s=' in str(raw_url) or '_t=' in str(raw_url) or ep_num <= 10 or '.mp4' in str(raw_url):
                unwrapped = unwrap_stream_url(raw_url)
                if unwrapped.startswith('http'):
                    subs = episode_data.get('subtitles', [])
                    if not subs and '.m3u8' in unwrapped:
                        try:
                            parsed_u = urllib.parse.urlparse(unwrapped)
                            base_p = parsed_u.path.rsplit('/', 1)[0]
                            sub_vtt = urllib.parse.urlunparse((parsed_u.scheme, parsed_u.netloc, f"{base_p}/subtitle.vtt", parsed_u.params, parsed_u.query, parsed_u.fragment))
                            subs = [{'language': 'TR', 'url': sub_vtt, 'label': 'TR'}]
                        except Exception:
                            pass
                    return finalize_stream(unwrapped, subs)

        # 2. Fast Cache Lookup
        if cache_key in CROSS_SERIES_CACHE and not force_refresh:
            cached_v, cached_s = CROSS_SERIES_CACHE[cache_key]
            is_df_cached = ('dramaflix' in str(cached_v) or 'dramakolik' in str(cached_v))
            if not (is_df_cached and ep_num > 15 and not _GLOBAL_CDN_CACHE.get('premium', False)):
                return cached_v, cached_s

        # 3. Check local SQLite DB (strictly matching exact slug & dubbing)
        db_res = self._scan_db(ep_slug)
        if db_res and db_res.get('episodes'):
            found_ep = next((e for e in db_res['episodes'] if e.get('episode_number') == ep_num), None)
            if found_ep and found_ep.get('url') and str(found_ep.get('url')).startswith('http'):
                db_url = found_ep['url']
                is_df_db = ('dramaflix' in str(db_url) or 'dramakolik' in str(db_url))
                if not (is_df_db and ep_num > 15 and not _GLOBAL_CDN_CACHE.get('premium', False)):
                    return finalize_stream(db_url, found_ep.get('subtitles', []))

        cached_mapping = CROSS_SERIES_CACHE.get(f"map:{ep_slug}")
        if cached_mapping:
            c_prov = cached_mapping.get('provider')
            c_slug = cached_mapping.get('slug')
            try:
                if c_prov == 'dramacix':
                    v_url, subs = self.dramacix.resolve_episode_stream({'slug': c_slug, 'episode_number': ep_num})
                    if v_url:
                        return finalize_stream(v_url, subs)
                elif c_prov == 'dramadizilerim':
                    v_url, subs = self.dramadizilerim.resolve_episode_stream(f"https://dramadizilerim.com/izle/{c_slug}?s=1&e={ep_num}")
                    if v_url:
                        return finalize_stream(v_url, subs)
            except Exception:
                pass

        # 1. Fallbacks: Cross-Provider Resolution (DramaDizilerim, DramaCix, LiderDrama)
        is_dubbed_series = 'dublaj' in ep_slug.lower() or 'dublaj' in series_title.lower() or 'dub' in ep_slug.lower()
        raw_slug_vars = clean_slug_variations(ep_slug)
        slug_vars = list(raw_slug_vars)
        if is_dubbed_series:
            # Ensure both non-dubbed base slug and dubbed slug variants are present
            for sv in raw_slug_vars:
                dub_sv = f"{sv}-dublajli"
                if dub_sv not in slug_vars:
                    slug_vars.insert(0, dub_sv)
        if ep_slug not in slug_vars:
            slug_vars.insert(0, ep_slug)

        # Primary Fallback: DramaDizilerim (Comprehensive, Unlocked, Fast MP4 + Turkish Subs)
        for sv in slug_vars[:5]:
            try:
                dd_url = f"https://dramadizilerim.com/izle/{sv}?s=1&e={ep_num}"
                v_url, subs = self.dramadizilerim.resolve_episode_stream(dd_url)
                if v_url and str(v_url).startswith('http'):
                    CROSS_SERIES_CACHE[f"map:{ep_slug}"] = {'provider': 'dramadizilerim', 'slug': sv}
                    return finalize_stream(v_url, subs)
            except Exception:
                pass

        # 2. Try clean slug variations on DramaCix (Strict Series Title Verified)
        for sv in slug_vars[:3]:
            try:
                dc_res = self.dramacix.scan_series(sv)
                if dc_res and dc_res.get('episodes') and is_similar_series(series_title, ep_slug, dc_res.get('title', ''), sv):
                    found_ep = next((e for e in dc_res['episodes'] if e.get('episode_number') == ep_num), None)
                    if found_ep:
                        v_url, subs = self.dramacix.resolve_episode_stream(found_ep)
                        if v_url:
                            CROSS_SERIES_CACHE[f"map:{ep_slug}"] = {'provider': 'dramacix', 'slug': sv}
                            return finalize_stream(v_url, subs)
            except Exception:
                pass

        # 3. Try LiderDrama direct slug variations
        for sv in slug_vars[:2]:
            try:
                ld_res = self.liderdrama.scan_series(sv)
                if ld_res and ld_res.get('episodes') and is_similar_series(series_title, ep_slug, ld_res.get('title', ''), sv):
                    found_ep = next((e for e in ld_res['episodes'] if e.get('episode_number') == ep_num), None)
                    if found_ep and found_ep.get('url'):
                        return finalize_stream(found_ep['url'], found_ep.get('subtitles', []))
            except Exception:
                pass

        # 4. Fallback: check direct raw_url (Only if it is a genuine playable video stream)
        if raw_url:
            unwrapped = unwrap_stream_url(str(raw_url))
            if is_valid_stream_url(unwrapped):
                return finalize_stream(unwrapped, episode_data.get('subtitles', []))

        # 5. Final VIP Fallback: Query DramaFlix with VIP token if not resolved yet
        try:
            df_res = self.dramaflix.scan_series(ep_slug)
            if df_res and df_res.get('episodes'):
                found_ep = next((e for e in df_res['episodes'] if e.get('episode_number') == ep_num), None)
                if found_ep and found_ep.get('url') and str(found_ep.get('url')).startswith('http'):
                    return finalize_stream(found_ep['url'], found_ep.get('subtitles', []))
        except Exception:
            pass

        raise ValueError(f"Bölüm {ep_num} video akışı bulunamadı veya kilit açılamadı.")

    def download_subtitle(self, sub_url: str) -> str:
        if not sub_url: return ''
        unwrapped = unwrap_stream_url(sub_url)
        headers = self.get_request_headers_for_url(unwrapped)
        
        # 1. Try curl_cffi with full impersonation, cookies and auth headers
        try:
            from curl_cffi import requests as c_requests
            s = c_requests.Session(impersonate='chrome120')
            r = s.get(unwrapped, headers=headers, timeout=5.0)
            if r.status_code == 200 and r.text and len(r.text.strip()) > 10:
                text = r.text
                if text.startswith('WEBVTT') or '-->' in text:
                    return convert_vtt_to_srt(text)
                return text
        except Exception:
            pass

        # 2. Fallback to standard requests
        for attempt in range(2):
            try:
                r = requests.get(unwrapped, headers=headers, timeout=5.0)
                if r.status_code == 200 and r.text and len(r.text.strip()) > 10:
                    text = r.text
                    if text.startswith('WEBVTT') or '-->' in text:
                        return convert_vtt_to_srt(text)
                    return text
            except Exception:
                time.sleep(0.1)
        return ''

    def download_subtitle_vtt(self, sub_url: str) -> str:
        srt = self.download_subtitle(sub_url)
        return convert_srt_to_vtt(srt) if srt else ''

    def get_request_headers_for_url(self, target_url: str) -> dict:
        h = {
            'User-Agent': REALISTIC_USER_AGENT,
            'Accept': '*/*',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        parsed = urllib.parse.urlparse(target_url)
        domain = parsed.netloc.lower()
        if 'dramaflix' in domain or 'dramakolik' in domain or 'cdn.dramaflix' in domain:
            self.dramaflix.refresh_cdn_ticket()
            h['Referer'] = 'https://dramaflix.net/'
            h['Origin'] = 'https://dramaflix.net'
            cookie_pairs = []
            for k, v in self.dramaflix.cdn_cookies.items():
                cookie_pairs.append(f"{k}={v}")
            active_token = token_vault.get_token('dramaflix') or self.user_cookie
            if active_token:
                c_str = active_token.strip()
                if c_str.startswith('Bearer ') or (len(c_str) > 30 and ';' not in c_str and '=' not in c_str):
                    token = c_str.replace('Bearer ', '').strip()
                    h['Authorization'] = f'Bearer {token}'
                else:
                    for part in c_str.split(';'):
                        if '=' in part:
                            cookie_pairs.append(part.strip())
            if cookie_pairs:
                h['Cookie'] = '; '.join(cookie_pairs)
        elif 'dramacix' in domain or 'narto-drama' in domain or 'mydramawave' in domain:
            h['Referer'] = 'https://dramacix.com/'
            h['Origin'] = 'https://dramacix.com'
        elif 'dramadizilerim' in domain:
            h['Referer'] = 'https://dramadizilerim.com/'
            h['Origin'] = 'https://dramadizilerim.com'
        elif 'crazymaplestudios' in domain or 'reelshort' in domain:
            h['Referer'] = 'https://reelshort.com/'
            h['Origin'] = 'https://reelshort.com'
        elif 'liderdrama' in domain:
            h['Referer'] = 'https://liderdrama.com/'
            h['Origin'] = 'https://liderdrama.com'
        elif 'mydramawave' in domain:
            h['Referer'] = 'https://www.mydramawave.com/'
            h['Origin'] = 'https://www.mydramawave.com'
        else:
            h['Referer'] = f"{parsed.scheme}://{parsed.netloc}/"
            h['Origin'] = f"{parsed.scheme}://{parsed.netloc}"
        return h

    def get_ffmpeg_headers_for_url(self, target_url: str) -> str:
        h = self.get_request_headers_for_url(target_url)
        return "\r\n".join(f"{k}: {v}" for k, v in h.items()) + "\r\n"
