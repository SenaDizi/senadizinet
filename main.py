# -*- coding: utf-8 -*-
"""
SedaDizi (senadizi.com) - FastAPI Universal Backend Server
Direct HTML and Static File Routing (No 404 for /admin.html, /dmca.html, etc.)
"""

import os
import json
import subprocess
from datetime import datetime, timezone
from fastapi import FastAPI, Query, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. API: Canlı Dizi Verisi
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

# 2. API: Güvenli Webhook / Cron Tetikleyici
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

# 3. Doğrudan Belirlenen HTML Rotaları (Explicit Direct HTML Routes)
@app.get("/admin.html", response_class=FileResponse)
@app.get("/admin", response_class=FileResponse)
def serve_admin():
    return FileResponse(os.path.join(BASE_DIR, "admin.html"), media_type="text/html")

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

@app.get("/diziler.json")
def serve_diziler_json():
    return FileResponse(os.path.join(BASE_DIR, "diziler.json"), media_type="application/json")

@app.get("/manifest.json")
def serve_manifest():
    return FileResponse(os.path.join(BASE_DIR, "manifest.json"), media_type="application/json")

@app.get("/robots.txt")
def serve_robots():
    return FileResponse(os.path.join(BASE_DIR, "robots.txt"), media_type="text/plain")

@app.get("/sitemap.xml")
def serve_sitemap():
    return FileResponse(os.path.join(BASE_DIR, "sitemap.xml"), media_type="application/xml")

# 4. Statik Varlıklar (Assets) Klasörü
assets_dir = os.path.join(BASE_DIR, "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# 5. Dinamik Genel Rota (Fallback for any root file or index.html)
@app.get("/{file_name:path}")
def serve_static_or_spa(file_name: str):
    if not file_name or file_name == "/":
        return FileResponse(os.path.join(BASE_DIR, "index.html"), media_type="text/html")
    
    # 1. Dosya birebir varsa
    direct_path = os.path.join(BASE_DIR, file_name)
    if os.path.isfile(direct_path):
        media = "text/html" if file_name.endswith(".html") else None
        return FileResponse(direct_path, media_type=media)
    
    # 2. .html uzantısı eklenince varsa
    html_path = os.path.join(BASE_DIR, f"{file_name}.html")
    if os.path.isfile(html_path):
        return FileResponse(html_path, media_type="text/html")
    
    # 3. SPA Varsayılanı
    return FileResponse(os.path.join(BASE_DIR, "index.html"), media_type="text/html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    print(f"FastAPI Server running on: http://0.0.0.0:{port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
