import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# override=False ensures Render's system $PORT and $HOST take precedence
load_dotenv(BASE_DIR / ".env", override=False)

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "SenaDizi")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "senadizinet-secret-key-default-2026")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")) # 7 gün
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./senadizinet.db")
    
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    BASE_URL: str = os.getenv("BASE_URL", "https://senadizi.com")
    DOMAIN: str = os.getenv("DOMAIN", "senadizi.com")
    
    DEFAULT_ADMIN_EMAIL: str = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@senadizi.com")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "SenaDizi2026!")
    DEFAULT_ADMIN_NAME: str = os.getenv("DEFAULT_ADMIN_NAME", "SenaDizi Admin")
    
    CDN_BASE_URL: str = os.getenv("CDN_BASE_URL", "")
    PAYMENT_PROVIDER: str = os.getenv("PAYMENT_PROVIDER", "demo")
    PAYMENT_WEBHOOK_SECRET: str = os.getenv("PAYMENT_WEBHOOK_SECRET", "")

settings = Settings()
