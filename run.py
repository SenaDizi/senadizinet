import os
import sys

# Windows Türkçe terminal (cp1254) utf-8 uyumluluğu
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import uvicorn
from app.config import settings
from app.seed import seed_database

def print_banner(host, port):
    print("=" * 70)
    print("🎬  S E N A D I Z I  –  PROFESYONEL DIZI PLATFORMU  🎬")
    print("=" * 70)
    print(f"📌 Baglanti Adresi (Local):   http://localhost:{port}")
    print(f"📌 Baglanti Adresi (Network): http://{host}:{port}")
    print(f"🛠️  Yonetim Paneli:           http://localhost:{port}/admin")
    print("-" * 70)
    print(f"🔑 Admin: {settings.DEFAULT_ADMIN_EMAIL} | Sifre: {settings.DEFAULT_ADMIN_PASSWORD}")
    print("=" * 70)
    print("🚀 Sunucu baslatiliyor...")

if __name__ == "__main__":
    seed_database()
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", settings.PORT))
    print_banner(host, port)
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
