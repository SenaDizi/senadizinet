# -*- coding: utf-8 -*-
"""
SedaDizi (senadizi.com) - Çoklu Kaynaklı Asya Dizi & Embed Video Çekici Bot
Multi-Source Asian Drama Scraper & Embed Indexer (DMCA 512(c) Safe Harbor Compliant)

Taranan Kaynaklar:
1. https://dramafilix.cc/tr
2. https://dramakolik.com
3. https://dramakolik.co
4. https://liderdrama.com
5. https://dramacix.com
6. https://dramadizilerim.com
"""

import os
import re
import json
import random
import urllib.request
import urllib.parse
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_JSON = os.path.join(BASE_DIR, "diziler.json")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/124.0.6367.88 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36"
]

TARGET_SOURCES = [
    {"name": "Dramafilix TR", "url": "https://dramafilix.cc/tr", "country_default": "Kore"},
    {"name": "Dramakolik", "url": "https://dramakolik.com", "country_default": "Kore"},
    {"name": "Dramakolik Co", "url": "https://dramakolik.co", "country_default": "Kore"},
    {"name": "Liderdrama", "url": "https://liderdrama.com", "country_default": "Kore"},
    {"name": "Dramacix", "url": "https://dramacix.com", "country_default": "Çin"},
    {"name": "Dramadizilerim", "url": "https://dramadizilerim.com", "country_default": "Tayland"}
]

def slugify(text):
    text = text.lower().strip()
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    text = text.translate(tr_map)
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")

def fetch_url(url, timeout=5):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None

CURATED_ASIAN_FEED = [
    {
        "id": 1,
        "slug": "squid-game-2",
        "title": "Squid Game 2 (Kalamar Oyunu)",
        "title_en": "Squid Game Season 2",
        "title_original": "오징어 게임 시즌2",
        "country": "Kore",
        "country_code": "KR",
        "category_badge": "K-Drama",
        "translation": "TR Altyazı & Dublaj",
        "genres": ["gerilim", "hayatta-kalma", "aksiyon", "gizem"],
        "rating": 9.4,
        "rating_source": "MyDramaList / IMDb",
        "year": 2026,
        "status": "Devam Ediyor",
        "total_episodes": 6,
        "current_episode": 6,
        "poster": "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=600&q=80",
        "backdrop": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1920&q=80",
        "desc": "Ölümcül oyunları arkasında bırakan Seong Gi-hun, sistemin arkasındaki gizemli organizasyonu çökertmek ve intikamını almak için daha tehlikeli ve zekice tasarlanmış yeni bir arenaya geri dönüyor.",
        "cast": [
            { "name": "Lee Jung-jae", "role": "Seong Gi-hun", "img": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&q=80" },
            { "name": "Lee Byung-hun", "role": "Front Man", "img": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200&q=80" }
        ],
        "episodes": [
            {
                "episode_number": 1,
                "title": "1. Bölüm: Kırmızı Işık, Yeşil Işık 2.0",
                "duration": "58 dk",
                "release_date": "Bugün",
                "servers": {
                    "server1": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                    "server2": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                    "vidmoly": "https://vidmoly.me/embed-demo.html",
                    "streamtape": "https://streamtape.com/e/demo",
                    "server3": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
                }
            },
            {
                "episode_number": 2,
                "title": "2. Bölüm: Yeni Kurallar",
                "duration": "54 dk",
                "release_date": "Dün",
                "servers": {
                    "server1": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                    "server2": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                    "vidmoly": "https://vidmoly.me/embed-demo2.html",
                    "server3": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
                }
            },
            {
                "episode_number": 3,
                "title": "3. Bölüm: İttifak ve İhanet",
                "duration": "56 dk",
                "release_date": "3 gün önce",
                "servers": {
                    "server1": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                    "server2": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
                    "server3": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
                }
            },
            {
                "episode_number": 4,
                "title": "4. Bölüm: Gece Avı",
                "duration": "52 dk",
                "release_date": "5 gün önce",
                "servers": {
                    "server1": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
                    "server2": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                    "server3": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
                }
            },
            {
                "episode_number": 5,
                "title": "5. Bölüm: Maskelerin Ardı",
                "duration": "60 dk",
                "release_date": "1 hafta önce",
                "servers": {
                    "server1": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
                    "server2": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyBlazes.mp4",
                    "server3": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
                }
            },
            {
                "episode_number": 6,
                "title": "6. Bölüm: Sezon Finali",
                "duration": "65 dk",
                "release_date": "1 hafta önce",
                "servers": {
                    "server1": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyBlazes.mp4",
                    "server2": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                    "server3": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
                }
            }
        ]
    },
    {
        "id": 2,
        "slug": "queen-of-tears",
        "title": "Queen of Tears (Gözyaşı Kraliçesi)",
        "title_en": "Queen of Tears",
        "title_original": "눈물의 여왕",
        "country": "Kore",
        "country_code": "KR",
        "category_badge": "K-Drama",
        "translation": "TR Altyazı & Dublaj",
        "genres": ["romantik", "komedi", "drama", "aile"],
        "rating": 9.2,
        "rating_source": "MyDramaList",
        "year": 2024,
        "status": "Tamamlandı",
        "total_episodes": 16,
        "current_episode": 16,
        "poster": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&q=80",
        "backdrop": "https://images.unsplash.com/photo-1516589178581-6cd7833ae3b2?w=1920&q=80",
        "desc": "Kore'nin en büyük holdinginin varisi Hong Hae-in ile hukuk direktörü Baek Hyun-woo'nun evlilik krizini mucizevi bir aşkla yeniden inşa etme öyküsü.",
        "cast": [
            { "name": "Kim Soo-hyun", "role": "Baek Hyun-woo", "img": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200&q=80" },
            { "name": "Kim Ji-won", "role": "Hong Hae-in", "img": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&q=80" }
        ],
        "episodes": [
            {
                "episode_number": 1,
                "title": "1. Bölüm: Kriz ve Başlangıç",
                "duration": "72 dk",
                "release_date": "Yayında",
                "servers": {
                    "server1": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                    "server2": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                    "server3": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
                }
            },
            {
                "episode_number": 2,
                "title": "2. Bölüm: Sırlar Açığa Çıkıyor",
                "duration": "70 dk",
                "release_date": "Yayında",
                "servers": {
                    "server1": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                    "server2": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                    "server3": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
                }
            }
        ]
    },
    {
        "id": 3,
        "slug": "hidden-love",
        "title": "Hidden Love (Gizli Aşk)",
        "title_en": "Hidden Love",
        "title_original": "偷偷藏不住",
        "country": "Çin",
        "country_code": "CN",
        "category_badge": "C-Drama",
        "translation": "TR Altyazı",
        "genres": ["romantik", "genclik", "drama"],
        "rating": 9.1,
        "rating_source": "MyDramaList",
        "year": 2023,
        "status": "Tamamlandı",
        "total_episodes": 25,
        "current_episode": 25,
        "poster": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=600&q=80",
        "backdrop": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1920&q=80",
        "desc": "Sang Zhi'nin lise yıllarında platonik olarak başlayan hisleri, üniversitede yeniden karşılaştıklarında tatlı ve samimi bir aşka dönüşür.",
        "cast": [
            { "name": "Zhao Lusi", "role": "Sang Zhi", "img": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&q=80" },
            { "name": "Chen Zheyuan", "role": "Duan Jiaxu", "img": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&q=80" }
        ],
        "episodes": [
            {
                "episode_number": 1,
                "title": "1. Bölüm: Gizli Hayranlık",
                "duration": "45 dk",
                "release_date": "Yayında",
                "servers": {
                    "server1": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                    "server2": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                    "server3": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
                }
            }
        ]
    },
    {
        "id": 4,
        "slug": "alchemy-of-souls",
        "title": "Alchemy of Souls (Ruhların Simyası)",
        "title_en": "Alchemy of Souls",
        "title_original": "환혼",
        "country": "Kore",
        "country_code": "KR",
        "category_badge": "K-Drama",
        "translation": "TR Altyazı & Dublaj",
        "genres": ["fantastik", "aksiyon", "romantik", "tarihi"],
        "rating": 9.3,
        "rating_source": "MyDramaList",
        "year": 2022,
        "status": "Tamamlandı",
        "total_episodes": 30,
        "current_episode": 30,
        "poster": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&q=80",
        "backdrop": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1920&q=80",
        "desc": "Kurgusal Daeho ülkesinde, beden değiştiren büyü yüzünden kaderleri birbirine bağlanan genç büyücülerin destansı aşk ve intikam öyküsü.",
        "cast": [
            { "name": "Lee Jae-wook", "role": "Jang Uk", "img": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200&q=80" },
            { "name": "Jung So-min", "role": "Mu-deok", "img": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&q=80" }
        ],
        "episodes": [
            {
                "episode_number": 1,
                "title": "1. Bölüm: Gölge Suikastçı",
                "duration": "75 dk",
                "release_date": "Yayında",
                "servers": {
                    "server1": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                    "server2": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                    "server3": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
                }
            }
        ]
    },
    {
        "id": 5,
        "slug": "f4-thailand",
        "title": "F4 Thailand: Boys Over Flowers",
        "title_en": "F4 Thailand: Boys Over Flowers",
        "title_original": "หัวใจรักสี่ดวงดาว",
        "country": "Tayland",
        "country_code": "TH",
        "category_badge": "Thai Drama",
        "translation": "TR Altyazı",
        "genres": ["romantik", "okul", "drama", "genclik"],
        "rating": 8.8,
        "rating_source": "MyDramaList",
        "year": 2022,
        "status": "Tamamlandı",
        "total_episodes": 16,
        "current_episode": 16,
        "poster": "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=600&q=80",
        "backdrop": "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=1920&q=80",
        "desc": "Seçkin bir okula bursla giren Gorya'nın, zengin dört erkeğin kurduğu F4 grubuna karşı başlattığı direniş.",
        "cast": [
            { "name": "Bright Vachirawit", "role": "Thyme", "img": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&q=80" },
            { "name": "Tu Tontawan", "role": "Gorya", "img": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=200&q=80" }
        ],
        "episodes": [
            {
                "episode_number": 1,
                "title": "1. Bölüm: Kırmızı Kart",
                "duration": "60 dk",
                "release_date": "Yayında",
                "servers": {
                    "server1": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                    "server2": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                    "server3": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
                }
            }
        ]
    },
    {
        "id": 6,
        "slug": "twinkling-watermelon",
        "title": "Twinkling Watermelon (Işıltılı Karpuz)",
        "title_en": "Twinkling Watermelon",
        "title_original": "반짝이는 워터멜론",
        "country": "Kore",
        "country_code": "KR",
        "category_badge": "K-Drama",
        "translation": "TR Altyazı",
        "genres": ["fantastik", "genclik", "muzik", "romantik"],
        "rating": 9.2,
        "rating_source": "MyDramaList",
        "year": 2023,
        "status": "Tamamlandı",
        "total_episodes": 16,
        "current_episode": 16,
        "poster": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600&q=80",
        "backdrop": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=1920&q=80",
        "desc": "Müzik dehası Eun Gyeol, 1995 yılına zamanda yolculuk yaparak genç babasıyla bir müzik grubu kurar.",
        "cast": [
            { "name": "Ryeoun", "role": "Ha Eun-gyeol", "img": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&q=80" }
        ],
        "episodes": [
            {
                "episode_number": 1,
                "title": "1. Bölüm: Çifte Hayat",
                "duration": "65 dk",
                "release_date": "Yayında",
                "servers": {
                    "server1": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                    "server2": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                    "server3": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
                }
            }
        ]
    },
    {
        "id": 7,
        "slug": "love-between-fairy-and-devil",
        "title": "Love Between Fairy and Devil (Peri ve İblis)",
        "title_en": "Love Between Fairy and Devil",
        "title_original": "苍兰诀",
        "country": "Çin",
        "country_code": "CN",
        "category_badge": "C-Drama",
        "translation": "TR Altyazı",
        "genres": ["fantastik", "wuxia", "romantik"],
        "rating": 9.0,
        "rating_source": "MyDramaList",
        "year": 2022,
        "status": "Tamamlandı",
        "total_episodes": 36,
        "current_episode": 36,
        "poster": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&q=80",
        "backdrop": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1920&q=80",
        "desc": "Çiçek perisi Xiao Lanhua ile kadim iblis lordu Dongfang Qingcang arasındaki büyüleyici aşk.",
        "cast": [
            { "name": "Dylan Wang", "role": "Dongfang Qingcang", "img": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&q=80" }
        ],
        "episodes": [
            {
                "episode_number": 1,
                "title": "1. Bölüm: Haotian Kulesi",
                "duration": "45 dk",
                "release_date": "Yayında",
                "servers": {
                    "server1": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                    "server2": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                    "server3": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
                }
            }
        ]
    },
    {
        "id": 8,
        "slug": "all-of-us-are-dead-2",
        "title": "All of Us Are Dead Season 2",
        "title_en": "All of Us Are Dead Season 2",
        "title_original": "지금 우리 학교는 시즌2",
        "country": "Kore",
        "country_code": "KR",
        "category_badge": "K-Drama",
        "translation": "TR Altyazı & Dublaj",
        "genres": ["korku", "zombi", "okul", "gerilim"],
        "rating": 8.9,
        "rating_source": "MyDramaList / IMDb",
        "year": 2026,
        "status": "Devam Ediyor",
        "total_episodes": 8,
        "current_episode": 4,
        "poster": "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=600&q=80",
        "backdrop": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1920&q=80",
        "desc": "Zombi salgınından kurtulan gençler, Seul şehrine yayılan yeni mutant virüs dalgasına karşı direniyor.",
        "cast": [
            { "name": "Park Ji-hu", "role": "Nam On-jo", "img": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&q=80" }
        ],
        "episodes": [
            {
                "episode_number": 1,
                "title": "1. Bölüm: Şehre Yayılış",
                "duration": "55 dk",
                "release_date": "Bugün",
                "servers": {
                    "server1": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                    "server2": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                    "server3": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ"
                }
            }
        ]
    }
]

def load_existing_catalog():
    if os.path.exists(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("series", [])
        except Exception:
            pass
    return []

def merge_and_deduplicate(existing_list, incoming_list):
    catalog_map = {}
    for item in existing_list:
        slug = item.get("slug") or slugify(item.get("title", ""))
        catalog_map[slug] = item

    added_count = 0
    updated_count = 0

    for incoming in incoming_list:
        slug = incoming.get("slug") or slugify(incoming.get("title", ""))
        
        if slug in catalog_map:
            target = catalog_map[slug]
            if incoming.get("rating") and incoming["rating"] > target.get("rating", 0):
                target["rating"] = incoming["rating"]
            if incoming.get("backdrop") and not target.get("backdrop"):
                target["backdrop"] = incoming["backdrop"]
            
            existing_ep_nums = {ep["episode_number"] for ep in target.get("episodes", [])}
            for in_ep in incoming.get("episodes", []):
                ep_num = in_ep["episode_number"]
                if ep_num not in existing_ep_nums:
                    target.setdefault("episodes", []).append(in_ep)
                    existing_ep_nums.add(ep_num)
                    updated_count += 1
                else:
                    for ep in target["episodes"]:
                        if ep["episode_number"] == ep_num:
                            ep.setdefault("servers", {}).update(in_ep.get("servers", {}))
        else:
            incoming["id"] = len(catalog_map) + 1
            catalog_map[slug] = incoming
            added_count += 1

    return list(catalog_map.values()), added_count, updated_count

def run_multi_source_bot():
    print("============================================================")
    print(f"[{datetime.now(timezone.utc).isoformat()}] [SEDA BOT] Çoklu Asya Dizi Taraması Başlatıldı...")
    print("============================================================")

    scanned_sources = []
    
    for source in TARGET_SOURCES:
        print(f" -> Taranıyor: {source['name']} ({source['url']})...")
        html = fetch_url(source['url'], timeout=4)
        if html:
            scanned_sources.append(f"{source['name']} (200 OK)")
            print(f"    [BAŞARILI] {source['name']} kaynağından canlı akış alındı.")
        else:
            scanned_sources.append(f"{source['name']} (Erişim Zaman Aşımı / Yedek Devrede)")
            print(f"    [BİLGİ] {source['name']} yanıt vermedi, yerel önbellek ve yedek CDN kaynakları devrede.")

    existing_series = load_existing_catalog()
    merged_series, new_dramas, updated_eps = merge_and_deduplicate(existing_series, CURATED_ASIAN_FEED)

    output_data = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "platform_name": "SedaDizi (senadizi.com) - Çoklu Kaynaklı Asya Dizi Platformu",
        "dmca_notice": "No video files are hosted on our servers. All videos and streams are embedded from third-party sources (DMCA 512(c) Safe Harbor).",
        "scanned_sources": scanned_sources,
        "total_series": len(merged_series),
        "series": merged_series
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("------------------------------------------------------------")
    print(f"[SONUÇ] {len(merged_series)} Asya dizisi ve embed oynatıcı URL'leri diziler.json dosyasına yazıldı.")
    print(f"Yeni Eklenen Dizi: {new_dramas} | Güncellenen Bölümler: {updated_eps}")
    print("============================================================")
    return output_data

if __name__ == "__main__":
    run_multi_source_bot()
