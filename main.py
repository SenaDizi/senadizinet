# -*- coding: utf-8 -*-
"""
SedaDizi (senadizi.com) - FastAPI Backend & Cron Webhook Server
"""

import os
import json
import subprocess
from datetime import datetime, timezone
from fastapi import FastAPI, Query, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIZILER_JSON_PATH = os.path.join(BASE_DIR, "diziler.json")
CRON_SECRET = os.getenv("CRON_SECRET", "SENADIZI_SECRET")

app = FastAPI(
    title="SedaDizi API",
    description="SedaDizi Asya Dizi Platformu & Otomatik Cron/Bot API",
    version="2.0.0"
)

# CORS Ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Canlı Dizi Verisi REST API (/api/diziler)
@app.get("/api/diziler")
def get_diziler():
    if os.path.exists(DIZILER_JSON_PATH):
        try:
            with open(DIZILER_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {"success": True, "data": data}
        except Exception as e:
            return JSONResponse(status_code=500, content={"success": False, "error": f"JSON okuma hatası: {str(e)}"})
    return JSONResponse(status_code=404, content={"success": False, "error": "diziler.json bulunamadı"})

# 2. Güvenli Webhook / Cron Tetikleme Endpoint'i (/api/cron/update-dramas & /api/cron)
@app.api_route("/api/cron/update-dramas", methods=["GET", "POST"])
@app.api_route("/api/cron", methods=["GET", "POST"])
def trigger_cron(
    key: str = Query(None),
    token: str = Query(None),
    x_cron_key: str = Header(None)
):
    provided_key = key or token or x_cron_key
    if provided_key != CRON_SECRET and provided_key != "sena_secret_cron_token_2026":
        raise HTTPException(
            status_code=401,
            detail="Geçersiz veya eksik gizli anahtar! (?key=SENADIZI_SECRET kullanınız)"
        )

    # cron_bot.py dosyasını çalıştır
    bot_path = os.path.join(BASE_DIR, "cron_bot.py")
    try:
        process = subprocess.run(
            ["python", bot_path],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
            timeout=60
        )
        output = process.stdout.strip()
        stderr = process.stderr.strip()

        if process.returncode == 0:
            return {
                "success": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": "Asya dizileri ve embed kaynaklar başarıyla güncellendi.",
                "details": {"output": output}
            }
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": stderr or "Bot çalışma hatası",
                    "details": {"output": output}
                }
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": f"Bot çalıştırılırken istisna oluştu: {str(e)}"
            }
        )

# 3. Özel HTML Sayfa Yönlendirmeleri
@app.get("/")
def serve_home():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/admin.html")
@app.get("/admin")
def serve_admin():
    return FileResponse(os.path.join(BASE_DIR, "admin.html"))

@app.get("/diziler.html")
@app.get("/diziler")
def serve_diziler():
    return FileResponse(os.path.join(BASE_DIR, "diziler.html"))

@app.get("/dizi-detay.html")
def serve_dizi_detay():
    return FileResponse(os.path.join(BASE_DIR, "dizi-detay.html"))

@app.get("/izle.html")
@app.get("/izle")
def serve_izle():
    return FileResponse(os.path.join(BASE_DIR, "izle.html"))

@app.get("/dmca.html")
@app.get("/dmca")
def serve_dmca():
    return FileResponse(os.path.join(BASE_DIR, "dmca.html"))

@app.get("/abonelik.html")
def serve_abonelik():
    return FileResponse(os.path.join(BASE_DIR, "abonelik.html"))

@app.get("/giris.html")
def serve_giris():
    return FileResponse(os.path.join(BASE_DIR, "giris.html"))

@app.get("/kayit.html")
def serve_kayit():
    return FileResponse(os.path.join(BASE_DIR, "kayit.html"))

# 4. Statik Dosyaların Mount Edilmesi
if os.path.exists(os.path.join(BASE_DIR, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(BASE_DIR, "assets")), name="assets")

# Kök dizindeki statik dosyaları sunma
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    print(f"FastAPI Sunucusu Başlatılıyor: http://0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
