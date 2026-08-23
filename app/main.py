from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine
from app.seed import seed_database
from app.routers import (
    auth_router,
    series_router,
    categories_router,
    user_router,
    sub_router,
    admin_router,
    views_router
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Veritabanı tablolarını ve seed verilerini otomatik yükle
    seed_database()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="SenaDizi - Profesyonel Dizi & Video Akış Platformu",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Statik Dosyalar ve Jinja2 Şablonları
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# API ve Web View Yönlendiricileri
app.include_router(auth_router)
app.include_router(series_router)
app.include_router(categories_router)
app.include_router(user_router)
app.include_router(sub_router)
app.include_router(admin_router)
app.include_router(views_router)

# Hata Sayfaları (404, 403, 500)
@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=404, content={"detail": "İstenen kaynak bulunamadı."})
    return templates.TemplateResponse(request=request, name="errors/404.html", context={"request": request, "site_name": settings.APP_NAME, "page_title": "404 - Sayfa Bulunamadı"}, status_code=404)

@app.exception_handler(403)
async def custom_403_handler(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=403, content={"detail": "Bu alana erişim yetkiniz yok."})
    return templates.TemplateResponse(request=request, name="errors/403.html", context={"request": request, "site_name": settings.APP_NAME, "page_title": "403 - Erişim Engellendi"}, status_code=403)

@app.exception_handler(500)
async def custom_500_handler(request: Request, exc):
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=500, content={"detail": "Sunucu hatası meydana geldi."})
    return templates.TemplateResponse(request=request, name="errors/500.html", context={"request": request, "site_name": settings.APP_NAME, "page_title": "500 - Sunucu Hatası"}, status_code=500)
