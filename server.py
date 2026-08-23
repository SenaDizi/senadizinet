import os
import uvicorn
from app.main import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"🚀 SenaDizi sunucusu başlatılıyor: http://{host}:{port}")
    uvicorn.run("server:app", host=host, port=port, reload=False)
