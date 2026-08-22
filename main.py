# -*- coding: utf-8 -*-
"""
SedaDizi (senadizi.com) - FastAPI Backend Server
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
    title="SedaDizi Platform & API",
    description="SedaDizi Asya Dizi Platformu, Çoklu Kaynak Botu & Webhook API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. ÖNCELİKLİ DOĞRUDAN HTML ROTALARI (TOP-PRIORITY DIRECT ROUTES)
@app.get("/admin.html", response_class=FileResponse)
@app.get("/admin", response_class=FileResponse)
def serve_admin():
    file_path = os.path.join(BASE_DIR, "admin.html")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="admin.html not found")

@app.get("/dmca.html", response_class=FileResponse)
@app.get("/dmca", response_class=FileResponse)
def serve_dmca():
    return FileResponse(os.path.join(BASE_DIR, "dmca.html"), media_type="text/html")

@app.get("/diziler.html", response_class=FileResponse)
@app.get("/diziler", response_class=FileResponse)
def serve_diziler():
    return FileResponse(os.path.join(BASE_DIR, "diziler.html"), media_type="text/html")

@app.get("/dizi-detay.html", response_class=FileResponse)
@app.get("/dizi-detay", response_class=FileResponse)
def serve_dizi_detay():
    return FileResponse(os.path.join(BASE_DIR, "dizi-detay.html"), media_type="text/html")

@app.get("/izle.html", response_class=FileResponse)
@app.get("/izle", response_class=FileResponse)
def serve_izle():
    return FileResponse(os.path.join(BASE_DIR, "izle.html"), media_type="text/html")

@app.get("/abonelik.html", response_class=FileResponse)
@app.get("/abonelik", response_class=FileResponse)
def serve_abonelik():
    return FileResponse(os.path.join(BASE_DIR, "abonelik.html"), media_type="text/html")

@app.get("/giris.html", response_class=FileResponse)
@app.get("/giris", response_class=FileResponse)
def serve_giris():
    return FileResponse(os.path.join(BASE_DIR, "giris.html"), media_type="text/html")

@app.get("/kayit.html", response_class=FileResponse)
@app.get("/kayit", response_class=FileResponse)
def serve_kayit():
    return FileResponse(os.path.join(BASE_DIR, "kayit.html"), media_type="text/html")

# 2. CANLI DİZİ VERİSİ REST API
@app.get("/api/diziler")
def get_diziler():
    if os.path.exists(DIZILER_JSON_PATH):
        try:
            with open(DIZILER_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {"success": True, "data": data}
        except Exception as e:
            return JSONResponse(status_code=500, content={"success": False, "error": str(e)})
    return JSONResponse(status_code=404, content={"success": False, "error": "diziler.json bulunamadı"})

# 3. GÜVENLİ CRON / WEBHOOK ENDPOINT'İ (/api/cron/update-dramas ve /api/cron)
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
            detail="Geçersiz gizli anahtar! (?key=SENADIZI_SECRET kullanınız)"
        )

    bot_path = os.path.join(BASE_DIR, "cron_bot.py")
    try:
        process = subprocess.run(
            ["python", bot_path],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
            timeout=60
        )
        return {
            "success": process.returncode == 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Asya dizileri ve embed kaynaklar güncellendi.",
            "details": {"output": process.stdout.strip(), "error": process.stderr.strip()}
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"Bot çalıştırma hatası: {str(e)}"}
        )

# 4. STATİK ASSETS KLASÖRÜ
assets_dir = os.path.join(BASE_DIR, "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# 5. KÖK DİZİN STATİK DOSYA VE SPA YÖNLENDİRMESİ
@app.get("/")
def serve_index():
    return FileResponse(os.path.join(BASE_DIR, "index.html"), media_type="text/html")

@app.get("/{file_name:path}")
def serve_fallback(file_name: str):
    direct_path = os.path.join(BASE_DIR, file_name)
    if os.path.isfile(direct_path):
        media = "text/html" if file_name.endswith(".html") else None
        return FileResponse(direct_path, media_type=media)
    
    html_path = os.path.join(BASE_DIR, f"{file_name}.html")
    if os.path.isfile(html_path):
        return FileResponse(html_path, media_type="text/html")
    
    return FileResponse(os.path.join(BASE_DIR, "index.html"), media_type="text/html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    print(f"FastAPI Server running on: http://0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
