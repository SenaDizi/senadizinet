import os
import sys
import uvicorn
from app.config import settings
from app.seed import seed_database

def print_banner(host, port):
    print("=" * 70)
    print("🎬  S E N A   D İ Z İ N E T  –  PROFESYONEL DİZİ PLATFORMU  🎬")
    print("=" * 70)
    print(f"📌 Bağlantı Noktası (Host / Port): http://{host}:{port}")
    print(f"🛠️  Yönetim Paneli:                http://{host}:{port}/admin")
    print("-" * 70)
    print(f"🔑 Admin: {settings.DEFAULT_ADMIN_EMAIL} | Şifre: {settings.DEFAULT_ADMIN_PASSWORD}")
    print("=" * 70)
    print("🚀 Sunucu başlatılıyor...")

if __name__ == "__main__":
    seed_database()
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", settings.PORT))
    print_banner(host, port)
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
