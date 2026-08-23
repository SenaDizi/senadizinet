# -*- coding: utf-8 -*-
"""
SenaDizi - Otomatik Sistem Yönetim, Bakım ve Cron Görevleri
------------------------------------------------------------
1. Sistem Sağlık & API Senkronizasyonu
2. CDN & Medya Erişilebilirlik Denetimi
3. Otomatik Önbellek ve Geçici Dosya Temizliği (Disk Alanı Tasarrufu)
4. Otomatik Veritabanı Yedekleme ve 7 Günlük Rotasyon
"""

import os
import sys
import time
import datetime
import shutil
import sqlite3
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "cron.log")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
DB_FILE = os.path.join(BASE_DIR, "senadizinet.db")
TEMP_DIRS = [
    os.path.join(BASE_DIR, "downloads"),
    os.path.join(BASE_DIR, "temp"),
    os.path.join(BASE_DIR, "cache")
]

def log(msg: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {msg}\n"
    try:
        sys.stdout.buffer.write(entry.encode("utf-8", errors="replace"))
        sys.stdout.flush()
    except Exception:
        pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"Log yazma hatasi: {e}")

# ==========================================
# 1. SİSTEM SAĞLIK & API KONTROLÜ
# ==========================================
def task_health_and_api_check():
    log("[GOREV 1] Sistem Saglik ve API Senkronizasyon Kontrolu Baslatildi...")
    if os.path.exists(DB_FILE):
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM series;")
            series_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM episodes;")
            episodes_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users;")
            users_count = cursor.fetchone()[0]
            
            conn.close()
            log(f"   [OK] Veritabani Durumu: {series_count} Dizi, {episodes_count} Bolum, {users_count} Kullanici kayitli.")
        except Exception as e:
            log(f"   [HATA] Veritabani istatistik sorgusu hatasi: {e}")
    else:
        log("   [BILGI] Yerel SQLite veritabani bulunamadi veya uzak PostgreSQL kullaniliyor.")

    endpoints = ["https://senadizi.com/", "http://127.0.0.1:8000/"]
    for url in endpoints:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SenaDizi-Cron-Bot/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    log(f"   [OK] Web Servis Yaniti ({url}): HTTP 200 OK")
                    break
        except Exception:
            pass

# ==========================================
# 2. CDN & BULUT DEPOLAMA ERİŞİM DENETİMİ
# ==========================================
def task_cdn_and_storage_check():
    log("[GOREV 2] CDN ve Bulut Depolama Erisilebilirlik Denetimi...")
    cdn_url = "https://cdn.senadizi.com"
    try:
        req = urllib.request.Request(cdn_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            log(f"   [OK] Cloudflare CDN Uc Noktasi ({cdn_url}): HTTP {resp.status} - Aktif")
    except urllib.error.HTTPError as e:
        log(f"   [OK] Cloudflare CDN Uc Noktasi ({cdn_url}): HTTP {e.code} - Ulasilabilir")
    except Exception as e:
        log(f"   [BILGI] CDN Durumu: {e}")

# ==========================================
# 3. GEÇİCİ DOSYA VE ÖNBELLEK TEMİZLİĞİ
# ==========================================
def task_cleanup_temp_files():
    log("[GOREV 3] Gecici Onbellek ve Indirme Dosyalari Temizleniyor...")
    cleaned_count = 0
    now = time.time()
    max_age_seconds = 24 * 3600  # 24 saatten eski dosyalari temizle

    for temp_dir in TEMP_DIRS:
        if not os.path.exists(temp_dir):
            continue
        try:
            for root, dirs, files in os.walk(temp_dir):
                for f in files:
                    file_path = os.path.join(root, f)
                    try:
                        if os.stat(file_path).st_mtime < now - max_age_seconds:
                            os.remove(file_path)
                            cleaned_count += 1
                    except Exception:
                        pass
        except Exception as e:
            log(f"   [HATA] Dizin temizleme hatasi ({temp_dir}): {e}")

    log(f"   [OK] Temizlik Tamamlandi: {cleaned_count} eski gecici dosya silindi.")

# ==========================================
# 4. VERİTABANI YEDEKLEME VE ROTASYON
# ==========================================
def task_backup_database():
    log("[GOREV 4] Otomatik Veritabani Yedegi Aliniyor...")
    if not os.path.exists(DB_FILE):
        log("   [BILGI] Yedeklenecek yerel senadizinet.db dosyasi bulunamadi.")
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"senadizi_backup_{timestamp}.db")

    try:
        shutil.copy2(DB_FILE, backup_file)
        file_size_kb = os.path.getsize(backup_file) / 1024
        log(f"   [OK] Yeni Veritabani Yedegi Olusturuldu: {os.path.basename(backup_file)} ({file_size_kb:.2f} KB)")

        backups = sorted(
            [os.path.join(BACKUP_DIR, f) for f in os.listdir(BACKUP_DIR) if f.startswith("senadizi_backup_") and f.endswith(".db")],
            key=os.path.getmtime
        )
        
        max_backups = 7
        if len(backups) > max_backups:
            to_delete = backups[:-max_backups]
            for old_backup in to_delete:
                try:
                    os.remove(old_backup)
                    log(f"   [OK] Eski Yedek Rotasyonla Silindi: {os.path.basename(old_backup)}")
                except Exception:
                    pass
    except Exception as e:
        log(f"   [HATA] Veritabani yedekleme hatasi: {e}")

# ==========================================
# ANA ÇALIŞTIRICI
# ==========================================
def run_all_cron_tasks():
    log("==================================================")
    log("SenaDizi Otomasyon & Bakim Cron Islemi Basladi")
    log("==================================================")
    
    task_health_and_api_check()
    task_cdn_and_storage_check()
    task_cleanup_temp_files()
    task_backup_database()
    
    log("==================================================")
    log("Tum Cron ve Bakim Gorevleri Basariyla Tamamlandi")
    log("==================================================\n")

if __name__ == "__main__":
    run_all_cron_tasks()
