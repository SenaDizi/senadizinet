# -*- coding: utf-8 -*-
"""
SenaDiziNet - Downloader & Video Studio Router
Provides full 24/7 cloud downloader integration at /downloader and /indir.
Features:
- Seamless Cloud Download Manager (downloads episodes in background on Render without worker PC)
- Worker Tunnel Proxy (routes heavy operations to worker PC when PC is online)
- Strict Multi-Browser Client Isolation (via senadizi_client_id)
- Zero-Failure fallback: NEVER throws 503 or "bilgisayar bağlı değil" errors!
"""

import os
import sys
import glob
import json
import time
import socket
import shutil
import queue
import threading
import subprocess
import urllib.parse
from typing import List, Optional
import requests
from fastapi import APIRouter, Request, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

# Path definitions
ROUTER_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(ROUTER_DIR)
PROJECT_ROOT = os.path.dirname(APP_DIR)

DOWNLOADS_DIR = os.path.join(PROJECT_ROOT, "downloads")
VIRAL_DIR = os.path.join(PROJECT_ROOT, "viral_edits")
COVERS_DIR = os.path.join(PROJECT_ROOT, "covers")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
STATIC_DOWNLOADER_DIR = os.path.join(PROJECT_ROOT, "static", "downloader")
CLIENT_REGISTRY_FILE = os.path.join(PROJECT_ROOT, "client_downloads.json")
WORKER_STATE_FILE = os.path.join(PROJECT_ROOT, "worker_state.json")

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(VIRAL_DIR, exist_ok=True)
os.makedirs(COVERS_DIR, exist_ok=True)

# Try local senadizi directory if present (on developer machine)
SENADIZI_LOCAL_DIR = os.path.abspath(os.path.join(PROJECT_ROOT, "..", "senadizi"))
if os.path.exists(SENADIZI_LOCAL_DIR) and SENADIZI_LOCAL_DIR not in sys.path:
    sys.path.insert(0, SENADIZI_LOCAL_DIR)

try:
    from api import SenaDiziAPI, convert_srt_to_vtt
    from downloader import (
        downloader_manager,
        DOWNLOADS_DIR as LOCAL_DOWNLOADS_DIR,
        get_client_downloads_mapping,
        register_client_download,
        unregister_client_download
    )
    from video_editor import video_studio, VIRAL_DIR as LOCAL_VIRAL_DIR, COVERS_DIR as LOCAL_COVERS_DIR
    from tunnel_manager import tunnel_manager
    DOWNLOADS_DIR = LOCAL_DOWNLOADS_DIR
    VIRAL_DIR = LOCAL_VIRAL_DIR
    COVERS_DIR = LOCAL_COVERS_DIR
except Exception as e:
    downloader_manager = None
    video_studio = None
    tunnel_manager = None
    try:
        from app.downloader_api import SenaDiziAPI, convert_srt_to_vtt
    except Exception:
        SenaDiziAPI = None
        convert_srt_to_vtt = None

    def get_client_downloads_mapping() -> dict:
        if os.path.exists(CLIENT_REGISTRY_FILE):
            try:
                with open(CLIENT_REGISTRY_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
        return {}

    def register_client_download(client_id: str, filename: str):
        if not client_id or not filename:
            return
        try:
            mapping = get_client_downloads_mapping()
            files = mapping.setdefault(str(client_id).strip(), [])
            clean_fn = os.path.basename(filename)
            if clean_fn not in files:
                files.append(clean_fn)
            with open(CLIENT_REGISTRY_FILE, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def unregister_client_download(client_id: str, filename: str):
        if not filename:
            return
        try:
            clean_fn = os.path.basename(filename)
            mapping = get_client_downloads_mapping()
            if client_id and str(client_id).strip() in mapping:
                mapping[str(client_id).strip()] = [f for f in mapping[str(client_id).strip()] if f != clean_fn]
            else:
                for cid in mapping:
                    mapping[cid] = [f for f in mapping[cid] if f != clean_fn]
            with open(CLIENT_REGISTRY_FILE, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

def get_ffmpeg_binary():
    p = shutil.which("ffmpeg")
    if p: return p
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    candidates = [
        os.path.join(PROJECT_ROOT, "..", "bin", "ffmpeg.exe"),
        os.path.join(PROJECT_ROOT, "..", "senadizi", "bin", "ffmpeg.exe"),
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None

# ==============================================================================
# Cloud Download Manager (Executes downloads directly on Render 24/7)
# ==============================================================================
class CloudDownloadTask:
    def __init__(self, task_id, series_slug, series_title, episodes, is_merged, client_id, user_cookie=None):
        self.task_id = task_id
        self.series_slug = series_slug or "dizi"
        self.series_title = series_title or series_slug
        self.episodes = episodes or []
        self.is_merged = is_merged
        self.client_id = client_id
        self.user_cookie = user_cookie
        self.status = "queued"
        self.progress = 0
        self.speed = "Bulutta Hazırlanıyor..."
        self.eta = ""
        self.filename = ""
        self.error = None
        self.created_at = time.time()

class CloudDownloadManager:
    def __init__(self):
        self.tasks = {}
        self.lock = threading.Lock()
        self.task_queue = queue.Queue()
        self.worker = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker.start()

    def queue_download(self, series_slug, episode, user_cookie=None, client_id=None):
        ep_num = episode.get("episode_number") or 1
        task_id = f"cloud_{int(time.time()*1000)}_{ep_num}"
        task = CloudDownloadTask(
            task_id=task_id,
            series_slug=series_slug,
            series_title=episode.get("series_title") or series_slug,
            episodes=[episode],
            is_merged=False,
            client_id=client_id,
            user_cookie=user_cookie
        )
        with self.lock:
            self.tasks[task_id] = task
        self.task_queue.put(task)
        return task_id

    def queue_merged_download(self, series_slug, series_title, episodes, user_cookie=None, client_id=None):
        def extract_num(ep):
            try:
                num = ep.get("episode_number")
                if num is not None and str(num).isdigit():
                    return int(num)
                m = re.search(r'(\d+)', str(ep.get("title") or ""))
                if m:
                    return int(m.group(1))
            except Exception:
                pass
            return 0
        sorted_episodes = sorted(episodes or [], key=extract_num)
        task_id = f"cloud_merge_{int(time.time()*1000)}"
        task = CloudDownloadTask(
            task_id=task_id,
            series_slug=series_slug,
            series_title=series_title,
            episodes=sorted_episodes,
            is_merged=True,
            client_id=client_id,
            user_cookie=user_cookie
        )
        with self.lock:
            self.tasks[task_id] = task
        self.task_queue.put(task)
        return task_id

    def get_status_all(self, client_id=None):
        with self.lock:
            result = {}
            for tid, t in self.tasks.items():
                if client_id and t.client_id and str(t.client_id) != str(client_id):
                    continue
                result[tid] = {
                    "task_id": tid,
                    "status": t.status,
                    "progress": t.progress,
                    "speed": t.speed,
                    "eta": t.eta,
                    "filename": t.filename,
                    "title": t.series_title,
                    "error": t.error,
                    "series_slug": t.series_slug
                }
            return result

    def cancel_task(self, task_id):
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = "cancelled"

    def clear_status(self, client_id=None):
        with self.lock:
            to_del = [tid for tid, t in self.tasks.items() if (not client_id or str(t.client_id) == str(client_id)) and t.status in ["completed", "cancelled", "error"]]
            for tid in to_del:
                del self.tasks[tid]

    def _worker_loop(self):
        while True:
            try:
                task = self.task_queue.get()
                if not task:
                    break
                self._process_task(task)
            except Exception as e:
                print(f"[CloudDownloader] Task error: {e}")
            finally:
                self.task_queue.task_done()

    def _process_task(self, task: CloudDownloadTask):
        task.status = "downloading"
        task.progress = 5
        task.speed = "Akış Çözümleniyor..."

        if not SenaDiziAPI:
            task.status = "error"
            task.error = "API motoru hazır değil"
            return

        api = SenaDiziAPI(user_cookie=task.user_cookie)
        downloaded_files = []
        total_eps = len(task.episodes) or 1

        for idx, ep in enumerate(task.episodes):
            if task.status == "cancelled":
                return

            ep_num = ep.get("episode_number") or (idx + 1)
            task.speed = f"Bölüm {ep_num}/{total_eps} İndiriliyor..."

            v_url, subs = api.resolve_episode_stream(ep, series_slug=task.series_slug)
            if not v_url:
                continue

            clean_series_name = "".join(c for c in task.series_slug if c.isalnum() or c in "-_").strip() or "dizi"
            out_fn = f"{clean_series_name}_Bolum_{ep_num:02d}.mp4"
            out_path = os.path.join(DOWNLOADS_DIR, out_fn)

            weight = int(85 / total_eps)
            base_p = int((idx / total_eps) * 85)
            self._download_stream_to_file(v_url, out_path, task, base_progress=base_p, weight=weight)
            downloaded_files.append(out_path)

            if subs:
                sub_fn = f"{clean_series_name}_Bolum_{ep_num:02d}.vtt"
                sub_path = os.path.join(DOWNLOADS_DIR, sub_fn)
                try:
                    if isinstance(subs, str) and subs.startswith("http"):
                        sr = requests.get(subs, timeout=10)
                        if sr.status_code == 200:
                            with open(sub_path, "wb") as sf:
                                sf.write(sr.content)
                    elif isinstance(subs, list) and len(subs) > 0 and isinstance(subs[0], dict) and subs[0].get("url"):
                        sr = requests.get(subs[0]["url"], timeout=10)
                        if sr.status_code == 200:
                            with open(sub_path, "wb") as sf:
                                sf.write(sr.content)
                except Exception:
                    pass

            if not task.is_merged:
                register_client_download(task.client_id, out_fn)

        if task.status == "cancelled":
            return

        if task.is_merged and len(downloaded_files) > 0:
            task.speed = "Tek Parça Birleştiriliyor..."
            task.progress = 90
            clean_series_name = "".join(c for c in task.series_slug if c.isalnum() or c in "-_").strip() or "dizi"
            merged_fn = f"{clean_series_name}_Tek_Parca.mp4"
            merged_path = os.path.join(DOWNLOADS_DIR, merged_fn)

            self._merge_files(downloaded_files, merged_path)
            register_client_download(task.client_id, merged_fn)
            task.filename = merged_fn
        elif len(downloaded_files) > 0:
            task.filename = os.path.basename(downloaded_files[0])

        task.progress = 100
        task.speed = "Tamamlandı"
        task.status = "completed"

    def _download_stream_to_file(self, url: str, target_path: str, task: CloudDownloadTask, base_progress=0, weight=80):
        if ".m3u8" in url or "playlist.m3u8" in url:
            ffmpeg_bin = get_ffmpeg_binary()
            if ffmpeg_bin:
                cmd = [
                    ffmpeg_bin, "-y",
                    "-user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "-i", url,
                    "-c", "copy",
                    "-bsf:a", "aac_adtstoasc",
                    "-fflags", "+genpts",
                    "-avoid_negative_ts", "make_zero",
                    "-movflags", "+faststart",
                    target_path
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=240)
                task.progress = base_progress + weight
                return

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        with requests.get(url, headers=headers, stream=True, timeout=25) as r:
            r.raise_for_status()
            total_size = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(target_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=512 * 1024):
                    if task.status == "cancelled":
                        return
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            frac = min(1.0, downloaded / total_size)
                            task.progress = int(base_progress + (frac * weight))

    def _merge_files(self, input_files: list, output_path: str):
        ffmpeg_bin = get_ffmpeg_binary()
        list_file = output_path + ".txt"
        try:
            with open(list_file, "w", encoding="utf-8") as f:
                for p in input_files:
                    safe_p = os.path.abspath(p).replace("\\", "/").replace("'", "'\\''")
                    f.write(f"file '{safe_p}'\n")

            if ffmpeg_bin:
                cmd = [
                    ffmpeg_bin, "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", list_file,
                    "-c", "copy",
                    "-fflags", "+genpts",
                    "-avoid_negative_ts", "make_zero",
                    "-movflags", "+faststart",
                    output_path
                ]
                res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=240)
                if res.returncode != 0 or not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                    cmd_fb = [
                        ffmpeg_bin, "-y",
                        "-f", "concat",
                        "-safe", "0",
                        "-i", list_file,
                        "-c:v", "copy",
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-ar", "48000",
                        "-ac", "2",
                        "-af", "aresample=async=1000:min_hard_comp=0.05:first_pts=0",
                        "-fflags", "+genpts",
                        "-avoid_negative_ts", "make_zero",
                        "-movflags", "+faststart",
                        output_path
                    ]
                    subprocess.run(cmd_fb, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
            else:
                with open(output_path, "wb") as out_f:
                    for p in input_files:
                        with open(p, "rb") as in_f:
                            shutil.copyfileobj(in_f, out_f)
        finally:
            if os.path.exists(list_file):
                try: os.remove(list_file)
                except Exception: pass

cloud_downloader = CloudDownloadManager()

# Worker state tracking (to proxy jobs to local PC when PC is online)
def get_worker_state() -> dict:
    if os.path.exists(WORKER_STATE_FILE):
        try:
            with open(WORKER_STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {'url': None, 'last_heartbeat': 0, 'status': 'offline'}

def save_worker_state(url: str):
    state = {
        'url': url.rstrip('/'),
        'last_heartbeat': time.time(),
        'status': 'online'
    }
    try:
        with open(WORKER_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    return state

def is_worker_active():
    state = get_worker_state()
    url = state.get('url')
    last_hb = state.get('last_heartbeat', 0)
    if url and (time.time() - last_hb < 180):
        return True, url
    return False, None

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def get_hostname():
    try:
        return socket.gethostname().lower()
    except Exception:
        return 'localhost'

router = APIRouter(tags=['Downloader & Video Studio'])

class TunnelRegisterRequest(BaseModel):
    tunnel_url: Optional[str] = None
    url: Optional[str] = None

class ScanRequest(BaseModel):
    url: str
    cookie: Optional[str] = None

class DownloadRequest(BaseModel):
    series_slug: Optional[str] = None
    series_title: Optional[str] = None
    episode: Optional[dict] = None
    episodes: Optional[List[dict]] = None
    cookie: Optional[str] = None
    merged: Optional[bool] = False
    merge: Optional[bool] = False
    client_id: Optional[str] = None

class CancelRequest(BaseModel):
    task_id: str

class DeleteFilesRequest(BaseModel):
    filenames: List[str]
    client_id: Optional[str] = None

class ViralRequest(BaseModel):
    video_filename: str
    clip_mode: Optional[str] = 'full'
    bg_type: Optional[str] = 'subway'
    burn_subs: Optional[bool] = True
    mirror: Optional[bool] = True
    speedup: Optional[bool] = True
    split_ratio: Optional[int] = 65

class PromoRequest(BaseModel):
    covers: List[str]
    bg_type: Optional[str] = 'subway'
    split_ratio: Optional[int] = 65
    collage_mode: Optional[bool] = False

@router.get('/indir', response_class=HTMLResponse)
@router.get('/indir/', response_class=HTMLResponse)
@router.get('/downloader', response_class=HTMLResponse)
@router.get('/downloader/', response_class=HTMLResponse)
def get_downloader_ui():
    candidates = [
        os.path.join(STATIC_DOWNLOADER_DIR, 'index.html'),
        os.path.join(SENADIZI_LOCAL_DIR, 'static', 'index.html'),
        os.path.join(PROJECT_ROOT, 'static', 'downloader', 'index.html')
    ]
    for cand in candidates:
        if os.path.exists(cand):
            with open(cand, 'r', encoding='utf-8') as f:
                return HTMLResponse(content=f.read())
    return HTMLResponse(content='<h1>SenaDizi Downloader Arayuzu Yuklenemedi</h1>', status_code=500)

@router.post('/indir/api/tunnel/register')
@router.post('/downloader/api/tunnel/register')
@router.post('/api/tunnel/register')
def api_tunnel_register(req: TunnelRegisterRequest):
    url = req.tunnel_url or req.url
    if not url:
        return JSONResponse({'success': False, 'msg': 'tunnel_url zorunludur'}, status_code=400)
    state = save_worker_state(url)
    return {'success': True, 'state': state}

@router.get('/indir/api/tunnel/status')
@router.get('/downloader/api/tunnel/status')
@router.get('/api/tunnel/status')
def api_tunnel_status():
    active, worker_url = is_worker_active()
    state = get_worker_state()
    return {
        'success': True,
        'online': active,
        'worker_url': worker_url if active else None,
        'last_seen': state.get('last_heartbeat'),
        'time_ago': int(time.time() - state.get('last_heartbeat', 0)) if state.get('last_heartbeat') else None
    }

@router.get('/indir/api/ip')
@router.get('/downloader/api/ip')
@router.get('/api/ip')
def get_ip(request: Request):
    ip = get_local_ip()
    host = get_hostname()
    pub_url = tunnel_manager.get_public_url() if tunnel_manager else None
    active, worker_url = is_worker_active()
    if not pub_url and active:
        pub_url = worker_url

    port = request.url.port or 8000
    local_url = f'http://{ip}:{port}/downloader'
    permanent_url = 'https://senadizinet.onrender.com/downloader'
    tunnel_url = f'{pub_url}/downloader' if pub_url else permanent_url

    return {
        'ip': ip,
        'hostname': host,
        'port': port,
        'app_name': 'senadizi/downloader',
        'local_url': local_url,
        'permanent_url': permanent_url,
        'tunnel_url': tunnel_url,
        'global_url': permanent_url,
        'public_tunnel': pub_url,
        'worker_online': active,
        'worker_url': worker_url,
        'direct_url': permanent_url,
        'host_url': f'http://{host}:{port}/downloader',
        'qr_url': permanent_url,
        'is_global': True,
        'tunnel_type': 'Cloudflare/Render'
    }

@router.post('/indir/api/scan')
@router.post('/downloader/api/scan')
@router.post('/api/scan')
def api_scan(req: ScanRequest):
    if SenaDiziAPI:
        try:
            api = SenaDiziAPI(user_cookie=req.cookie)
            result = api.scan_series(req.url, user_cookie=req.cookie)
            if result and result.get('episodes'):
                series_meta = {
                    'title': result.get('title') or 'Dizi',
                    'slug': result.get('slug') or 'dizi',
                    'description': result.get('description') or f"{result.get('title')} Turkce Altyazili Kisa Dizi",
                    'cover_image': result.get('cover_image') or result.get('cover') or '',
                    'platform': result.get('platform') or 'NetShort',
                    'total_episodes': result.get('total_episodes') or len(result.get('episodes', []))
                }
                return JSONResponse({
                    'success': True,
                    'series': series_meta,
                    'episodes': result.get('episodes', []),
                    'title': series_meta['title'],
                    'slug': series_meta['slug'],
                    'cover': series_meta['cover_image'],
                    'platform': series_meta['platform'],
                    'total_episodes': series_meta['total_episodes']
                })
        except Exception as e:
            print(f'[Downloader Scan local notice] {e}')

    active, worker_url = is_worker_active()
    if active and worker_url:
        try:
            resp = requests.post(f'{worker_url}/api/scan', json=req.dict(), timeout=25.0)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f'[Downloader Scan proxy error] {e}')

    return JSONResponse({'success': False, 'msg': 'Dizi bulunamadi veya bolumler listelenemedi.'}, status_code=400)

@router.post('/indir/api/download')
@router.post('/downloader/api/download')
@router.post('/api/download')
@router.post('/indir/api/download/queue')
@router.post('/downloader/api/download/queue')
@router.post('/api/download/queue')
def api_download(req: DownloadRequest, request: Request):
    cid = req.client_id or request.headers.get('X-Client-ID') or request.cookies.get('senadizi_client_id')
    req.client_id = cid

    # 1. Local PC manager (if running on PC directly)
    if downloader_manager:
        try:
            is_merged = req.merged or req.merge or False
            slug = req.series_slug or (req.episodes[0].get('slug') if req.episodes else 'dizi')
            title = req.series_title or slug
            if is_merged:
                task_id = downloader_manager.queue_merged_download(
                    series_slug=slug,
                    series_title=title,
                    episodes=req.episodes or [],
                    user_cookie=req.cookie,
                    client_id=cid
                )
                return {'success': True, 'ok': True, 'task_id': task_id}
            elif req.episodes:
                task_ids = []
                for ep in req.episodes:
                    tid = downloader_manager.queue_download(
                        series_slug=slug,
                        episode=ep,
                        user_cookie=req.cookie,
                        client_id=cid
                    )
                    task_ids.append(tid)
                return {'success': True, 'ok': True, 'task_ids': task_ids, 'task_id': task_ids[0] if task_ids else None}
            else:
                task_id = downloader_manager.queue_download(
                    series_slug=slug,
                    episode=req.episode or {},
                    user_cookie=req.cookie,
                    client_id=cid
                )
                return {'success': True, 'ok': True, 'task_id': task_id}
        except Exception as e:
            return JSONResponse({'success': False, 'msg': str(e), 'error': str(e)}, status_code=400)

    # 2. Worker PC Proxy (if PC worker is active)
    active, worker_url = is_worker_active()
    if active and worker_url:
        try:
            payload = req.model_dump() if hasattr(req, 'model_dump') else req.dict()
            headers = {'X-Client-ID': str(cid or '')}
            resp = requests.post(f'{worker_url}/api/download', json=payload, headers=headers, timeout=15.0)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f'[Cloud Proxy Error, falling back to CloudDownloader] {e}')

    # 3. 24/7 Cloud Downloader fallback (NO ERROR! Downloads directly in cloud)
    is_merged = req.merged or req.merge or False
    slug = req.series_slug or (req.episodes[0].get('slug') if req.episodes else 'dizi')
    title = req.series_title or slug

    if is_merged:
        task_id = cloud_downloader.queue_merged_download(
            series_slug=slug,
            series_title=title,
            episodes=req.episodes or [],
            user_cookie=req.cookie,
            client_id=cid
        )
        return {'success': True, 'ok': True, 'task_id': task_id}
    elif req.episodes:
        task_ids = []
        for ep in req.episodes:
            tid = cloud_downloader.queue_download(
                series_slug=slug,
                episode=ep,
                user_cookie=req.cookie,
                client_id=cid
            )
            task_ids.append(tid)
        return {'success': True, 'ok': True, 'task_ids': task_ids, 'task_id': task_ids[0] if task_ids else None}
    else:
        task_id = cloud_downloader.queue_download(
            series_slug=slug,
            episode=req.episode or {},
            user_cookie=req.cookie,
            client_id=cid
        )
        return {'success': True, 'ok': True, 'task_id': task_id}

@router.post('/indir/api/download/merged')
@router.post('/downloader/api/download/merged')
@router.post('/api/download/merged')
def api_download_merged(req: DownloadRequest, request: Request):
    req.merged = True
    return api_download(req, request)

@router.get('/indir/api/status')
@router.get('/downloader/api/status')
@router.get('/api/status')
def api_status(request: Request, client_id: Optional[str] = None):
    cid = client_id or request.headers.get('X-Client-ID') or request.cookies.get('senadizi_client_id')
    if downloader_manager:
        return downloader_manager.get_status_all(client_id=cid)

    active, worker_url = is_worker_active()
    if active and worker_url:
        try:
            headers = {'X-Client-ID': str(cid or '')}
            resp = requests.get(f'{worker_url}/api/status?client_id={urllib.parse.quote(str(cid or ""))}', headers=headers, timeout=5.0)
            if resp.status_code == 200:
                worker_tasks = resp.json()
                # Merge with any cloud tasks
                cloud_tasks = cloud_downloader.get_status_all(client_id=cid)
                worker_tasks.update(cloud_tasks)
                return worker_tasks
        except Exception:
            pass

    return cloud_downloader.get_status_all(client_id=cid)

@router.post('/indir/api/download/cancel/{task_id}')
@router.post('/downloader/api/download/cancel/{task_id}')
@router.post('/indir/api/download/cancel')
@router.post('/downloader/api/download/cancel')
@router.post('/api/download/cancel')
def api_cancel(task_id: Optional[str] = None, req: Optional[CancelRequest] = None):
    tid = task_id or (req.task_id if req else None)
    if tid:
        if downloader_manager:
            downloader_manager.cancel_task(tid)
        cloud_downloader.cancel_task(tid)
        active, worker_url = is_worker_active()
        if active and worker_url and not downloader_manager:
            try:
                requests.post(f'{worker_url}/api/download/cancel/{tid}', timeout=3)
            except Exception:
                pass
    return {'ok': True, 'success': True}

@router.post('/indir/api/status/clear')
@router.post('/downloader/api/status/clear')
@router.post('/api/status/clear')
def api_clear_status(request: Request, client_id: Optional[str] = None):
    cid = client_id or request.headers.get('X-Client-ID') or request.cookies.get('senadizi_client_id')
    if downloader_manager:
        downloader_manager.clear_status(client_id=cid)
    cloud_downloader.clear_status(client_id=cid)
    active, worker_url = is_worker_active()
    if active and worker_url and not downloader_manager:
        try:
            requests.post(f'{worker_url}/api/status/clear', headers={'X-Client-ID': str(cid or '')}, timeout=3)
        except Exception:
            pass
    return {'ok': True, 'success': True}

@router.get('/indir/api/downloads/list')
@router.get('/downloader/api/downloads/list')
@router.get('/api/downloads/list')
def api_list_downloads(request: Request, client_id: Optional[str] = None):
    cid = client_id or request.headers.get('X-Client-ID') or request.cookies.get('senadizi_client_id')

    files = []
    seen = set()

    # 1. Fetch from worker if active
    active, worker_url = is_worker_active()
    if active and worker_url and not downloader_manager:
        try:
            headers = {'X-Client-ID': str(cid or '')}
            resp = requests.get(f'{worker_url}/api/downloads/list?client_id={urllib.parse.quote(str(cid or ""))}', headers=headers, timeout=6.0)
            if resp.status_code == 200:
                worker_data = resp.json()
                for f in worker_data.get('files', []):
                    fn = f.get('filename')
                    if fn and fn not in seen:
                        seen.add(fn)
                        files.append(f)
        except Exception:
            pass

    # 2. Add local/cloud downloads
    mapping = get_client_downloads_mapping()
    allowed_files = None
    if cid and cid not in ['all', 'admin']:
        allowed_files = set(mapping.get(str(cid).strip(), []))

    all_paths = glob.glob(os.path.join(DOWNLOADS_DIR, '*.mp4')) + glob.glob(os.path.join(VIRAL_DIR, '*.mp4'))
    all_paths.sort(key=os.path.getmtime, reverse=True)

    for p in all_paths:
        fn = os.path.basename(p)
        if fn in seen:
            continue
        seen.add(fn)
        if allowed_files is not None and fn not in allowed_files:
            continue

        sz = os.path.getsize(p)
        base_name = fn.rsplit('.', 1)[0]
        has_sub = any(os.path.exists(os.path.join(os.path.dirname(p), f'{base_name}{ext}')) for ext in ['.srt', '.tr.srt', '.vtt'])

        files.append({
            'filename': fn,
            'size': sz,
            'size_mb': round(sz / (1024 * 1024), 1),
            'mtime': os.path.getmtime(p),
            'url': f'/downloader/api/downloads/file/{fn}',
            'has_subtitle': has_sub,
            'subtitle_url': f'/downloader/api/downloads/subtitle/{fn}' if has_sub else None
        })

    return JSONResponse({'success': True, 'files': files, 'count': len(files)})

def stream_file_with_range(req: Request, target_path: str, default_filename: str):
    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail='Dosya bulunamadi')

    file_size = os.path.getsize(target_path)
    media_type = 'video/mp4'
    if default_filename.endswith('.srt'):
        media_type = 'text/plain; charset=utf-8'
    elif default_filename.endswith('.vtt'):
        media_type = 'text/vtt; charset=utf-8'

    is_download = req.query_params.get('download') == '1' or req.query_params.get('dl') == '1'
    safe_fn = default_filename.replace('"', '').replace('\n', '').replace('\r', '')
    encoded_fn = urllib.parse.quote(safe_fn)
    disp_type = 'attachment' if is_download else 'inline'
    content_disposition = f"{disp_type}; filename=\"{safe_fn}\"; filename*=UTF-8''{encoded_fn}"

    range_header = req.headers.get('range')
    if not range_header:
        headers = {
            'Accept-Ranges': 'bytes',
            'Content-Length': str(file_size),
            'Cache-Control': 'public, max-age=3600',
            'Access-Control-Allow-Origin': '*',
            'Content-Disposition': content_disposition
        }
        return FileResponse(target_path, media_type=media_type, headers=headers, filename=safe_fn if is_download else None, content_disposition_type=disp_type)

    try:
        byte_range = range_header.replace('bytes=', '').strip()
        parts = byte_range.split('-')
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else file_size - 1
        if end >= file_size:
            end = file_size - 1
        if start > end:
            start = 0
    except Exception:
        start = 0
        end = file_size - 1

    content_length = end - start + 1

    def iter_file():
        with open(target_path, 'rb') as f:
            f.seek(start)
            remaining = content_length
            chunk_size = 2 * 1024 * 1024  # 2MB chunks for ultra-fast throughput on mobile & PC
            while remaining > 0:
                chunk = f.read(min(chunk_size, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    headers = {
        'Content-Range': f'bytes {start}-{end}/{file_size}',
        'Accept-Ranges': 'bytes',
        'Content-Length': str(content_length),
        'Cache-Control': 'no-cache',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Expose-Headers': 'Content-Range, Accept-Ranges, Content-Length',
        'Content-Disposition': content_disposition
    }
    return StreamingResponse(iter_file(), status_code=206, media_type=media_type, headers=headers)

@router.get('/indir/api/downloads/file/{filename}')
@router.get('/downloader/api/downloads/file/{filename}')
@router.get('/api/downloads/file/{filename}')
@router.get('/indir/downloads/{filename}')
@router.get('/downloader/downloads/{filename}')
def api_get_downloaded_file(filename: str, request: Request):
    clean_fn = urllib.parse.unquote(filename).strip()
    p1 = os.path.join(DOWNLOADS_DIR, clean_fn)
    p2 = os.path.join(VIRAL_DIR, clean_fn)
    target = p1 if os.path.exists(p1) else (p2 if os.path.exists(p2) else None)
    if target:
        return stream_file_with_range(request, target, clean_fn)

    active, worker_url = is_worker_active()
    if active and worker_url:
        target_url = f'{worker_url}/indir/api/downloads/file/{urllib.parse.quote(clean_fn)}'
        if request.query_params:
            target_url += f'?{request.query_params}'
        try:
            req_headers = {}
            if 'range' in request.headers:
                req_headers['range'] = request.headers['range']
            r = requests.get(target_url, headers=req_headers, stream=True, timeout=20)
            resp_headers = {k: v for k, v in r.headers.items() if k.lower() in ['content-range', 'accept-ranges', 'content-length', 'content-type', 'content-disposition']}
            return StreamingResponse(r.iter_content(chunk_size=1024*1024*2), status_code=r.status_code, headers=resp_headers)
        except Exception:
            pass

    raise HTTPException(status_code=404, detail='Dosya bulunamadi')

@router.get('/indir/api/downloads/subtitle/{filename:path}')
@router.get('/downloader/api/downloads/subtitle/{filename:path}')
@router.get('/api/downloads/subtitle/{filename:path}')
def api_get_downloaded_subtitle(filename: str):
    clean_fn = urllib.parse.unquote(filename).strip()
    base_name = clean_fn.rsplit('.', 1)[0] if '.' in clean_fn else clean_fn
    candidates = [
        os.path.join(DOWNLOADS_DIR, f'{base_name}.vtt'),
        os.path.join(DOWNLOADS_DIR, f'{base_name}.tr.srt'),
        os.path.join(DOWNLOADS_DIR, f'{base_name}.srt'),
        os.path.join(DOWNLOADS_DIR, clean_fn),
        os.path.join(VIRAL_DIR, f'{base_name}.vtt'),
        os.path.join(VIRAL_DIR, f'{base_name}.tr.srt'),
        os.path.join(VIRAL_DIR, f'{base_name}.srt'),
        os.path.join(VIRAL_DIR, clean_fn),
    ]
    for cand in candidates:
        if os.path.exists(cand) and os.path.isfile(cand) and os.path.getsize(cand) > 0:
            if cand.endswith('.vtt'):
                try:
                    with open(cand, 'r', encoding='utf-8', errors='ignore') as f:
                        vtt_text = f.read()
                    if not vtt_text.startswith('WEBVTT'):
                        vtt_text = "WEBVTT\n\n" + vtt_text
                    return Response(content=vtt_text, media_type='text/vtt; charset=utf-8', headers={'Cache-Control': 'no-cache', 'Access-Control-Allow-Origin': '*'})
                except Exception: pass
            else:
                try:
                    with open(cand, 'r', encoding='utf-8', errors='ignore') as f:
                        srt_text = f.read()
                    vtt_text = convert_srt_to_vtt(srt_text) if convert_srt_to_vtt else "WEBVTT\n\n"
                    return Response(content=vtt_text, media_type='text/vtt; charset=utf-8', headers={'Cache-Control': 'no-cache', 'Access-Control-Allow-Origin': '*'})
                except Exception: pass

    active, worker_url = is_worker_active()
    if active and worker_url:
        try:
            r = requests.get(f'{worker_url}/indir/api/downloads/subtitle/{urllib.parse.quote(clean_fn)}', timeout=5)
            if r.status_code == 200:
                return Response(content=r.content, media_type='text/vtt; charset=utf-8', headers={'Cache-Control': 'no-cache', 'Access-Control-Allow-Origin': '*'})
        except Exception: pass

    return Response(content="WEBVTT\n\n", media_type='text/vtt; charset=utf-8', headers={'Cache-Control': 'no-cache', 'Access-Control-Allow-Origin': '*'})

@router.post('/indir/api/downloads/delete')
@router.post('/downloader/api/downloads/delete')
@router.post('/api/downloads/delete')
def api_delete_downloads(req: DeleteFilesRequest, request: Request):
    cid = req.client_id or request.headers.get('X-Client-ID') or request.cookies.get('senadizi_client_id')
    deleted = []
    for fn in req.filenames:
        unregister_client_download(cid, fn)
        p1 = os.path.join(DOWNLOADS_DIR, fn)
        p2 = os.path.join(VIRAL_DIR, fn)
        for target in [p1, p2]:
            if os.path.exists(target):
                try:
                    os.remove(target)
                    deleted.append(fn)
                except Exception: pass
        for sub_ext in ['.srt', '.tr.srt', '.vtt']:
            sub1 = p1.rsplit('.', 1)[0] + sub_ext
            sub2 = p2.rsplit('.', 1)[0] + sub_ext
            for s in [sub1, sub2]:
                if os.path.exists(s):
                    try: os.remove(s)
                    except Exception: pass

    active, worker_url = is_worker_active()
    if active and worker_url and not downloader_manager:
        try:
            requests.post(f'{worker_url}/api/downloads/delete', json={'filenames': req.filenames}, headers={'X-Client-ID': str(cid or '')}, timeout=5)
        except Exception: pass

    return {'success': True, 'ok': True, 'deleted': deleted}

@router.post('/indir/api/viral/generate')
@router.post('/downloader/api/viral/generate')
@router.post('/api/viral/generate')
def api_viral_generate(req: ViralRequest):
    if not video_studio:
        return JSONResponse({'success': False, 'msg': 'Video Studio aktif degil.'}, status_code=500)
    data = req.model_dump() if hasattr(req, 'model_dump') else req.dict()
    task_id = video_studio.queue_viral_generation(data)
    return {'success': True, 'ok': True, 'task_id': task_id}

@router.get('/indir/api/viral/status/{task_id}')
@router.get('/downloader/api/viral/status/{task_id}')
@router.get('/api/viral/status/{task_id}')
def api_viral_status(task_id: str):
    if not video_studio:
        return {'status': 'Bulunamadi', 'progress': 0}
    st = video_studio.get_task_status(task_id)
    return st or {'status': 'Bulunamadi', 'progress': 0}

@router.post('/indir/api/viral/cancel/{task_id}')
@router.post('/downloader/api/viral/cancel/{task_id}')
@router.post('/api/viral/cancel/{task_id}')
def api_viral_cancel_path(task_id: str):
    if video_studio:
        video_studio.cancel_task(task_id)
    return {'success': True, 'ok': True}

@router.post('/indir/api/viral/upload')
@router.post('/downloader/api/viral/upload')
@router.post('/api/viral/upload')
async def api_viral_upload(file: UploadFile = File(...)):
    safe_fn = f'upload_{int(time.time())}_{file.filename}'
    save_path = os.path.join(DOWNLOADS_DIR, safe_fn)
    with open(save_path, 'wb') as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {'success': True, 'ok': True, 'filename': safe_fn}

@router.get('/indir/api/promo/covers')
@router.get('/downloader/api/promo/covers')
@router.get('/api/promo/covers')
def api_promo_covers():
    if not video_studio:
        return {'covers': [], 'total': 0}
    covers = video_studio.list_covers()
    return {'covers': covers, 'total': len(covers)}

@router.post('/indir/api/promo/sync_covers')
@router.post('/downloader/api/promo/sync_covers')
@router.post('/api/promo/sync_covers')
def api_promo_sync_covers():
    if not video_studio:
        return JSONResponse({'success': False, 'msg': 'Video Studio aktif degil.'}, status_code=500)
    task_id = video_studio.sync_covers()
    return {'success': True, 'ok': True, 'task_id': task_id}

@router.get('/indir/api/promo/status/{task_id}')
@router.get('/downloader/api/promo/status/{task_id}')
@router.get('/api/promo/status/{task_id}')
def api_promo_status(task_id: str):
    if not video_studio:
        return {'status': 'Bulunamadi', 'progress': 0}
    st = video_studio.get_task_status(task_id)
    return st or {'status': 'Bulunamadi', 'progress': 0}

@router.post('/indir/api/promo/generate')
@router.post('/downloader/api/promo/generate')
@router.post('/api/promo/generate')
def api_promo_generate(req: PromoRequest):
    if not video_studio:
        return JSONResponse({'success': False, 'msg': 'Video Studio aktif degil.'}, status_code=500)
    data = req.model_dump() if hasattr(req, 'model_dump') else req.dict()
    task_id = video_studio.queue_promo_generation(data)
    return {'success': True, 'ok': True, 'task_id': task_id}

@router.get('/indir/api/tokens')
@router.get('/downloader/api/tokens')
@router.get('/api/tokens')
def api_get_tokens():
    try:
        from api import token_vault
        return {
            'success': True,
            'tokens': token_vault.data,
            'active_token': token_vault.get_token('dramaflix'),
            'status': 'active'
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
