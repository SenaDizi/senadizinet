from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Query, Response
from fastapi.responses import HTMLResponse, PlainTextResponse, Response as FastAPIResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_
from app.database import get_db
from app.models.user import User, UserRole
from app.models.content import Series, Season, Episode, Category, Actor
from app.models.subscription import SubscriptionPlan, Subscription
from app.models.interaction import Favorite, WatchHistory, WatchProgress
from app.security import get_current_user_optional, get_current_admin
from app.config import settings

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="templates")

def get_base_context(request: Request, db: Session, title: str = "SenaDizi - Profesyonel Dizi Platformu", user: Optional[User] = None):
    if user is None:
        user = get_current_user_optional(request, db)
    
    categories = db.query(Category).filter(Category.is_active == True).order_by(Category.name).all()
    
    return {
        "request": request,
        "site_name": settings.APP_NAME,
        "site_domain": settings.DOMAIN,
        "page_title": title,
        "current_user": user,
        "categories_nav": categories,
        "meta_description": "SenaDizi ile yüksek kalitede, lisanslı ve özel dizi bölümlerini kesintisiz izleyin.",
        "canonical_url": f"{settings.BASE_URL}{request.url.path}"
    }

# --- 1. ANA SAYFA (HOME) ---
@router.get("/", response_class=HTMLResponse)
def home_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    ctx = get_base_context(request, db, "SenaDizi – Sinematik Dizi Platformu", user)

    # Hero / Featured Diziler
    hero_series = db.query(Series).options(
        joinedload(Series.categories),
        joinedload(Series.seasons).joinedload(Season.episodes)
    ).filter(Series.is_featured == True).limit(5).all()

    if not hero_series:
        hero_series = db.query(Series).options(
            joinedload(Series.categories),
            joinedload(Series.seasons)
        ).limit(3).all()

    # Popüler Diziler
    popular_series = db.query(Series).options(
        joinedload(Series.categories)
    ).order_by(desc(Series.view_count)).limit(10).all()

    # Yeni Eklenen Diziler
    new_series = db.query(Series).options(
        joinedload(Series.categories)
    ).order_by(desc(Series.created_at)).limit(10).all()

    # Son Eklenen Bölümler
    recent_episodes = db.query(Episode).options(
        joinedload(Episode.season).joinedload(Season.series)
    ).order_by(desc(Episode.created_at)).limit(8).all()

    # Kategori bazlı listeler (Drama, Aksiyon, Bilim Kurgu, Komedi, Romantik)
    category_rows = []
    featured_cats = ["drama", "aksiyon", "bilim-kurgu", "komedi", "romantik"]
    for cat_slug in featured_cats:
        cat = db.query(Category).filter(Category.slug == cat_slug).first()
        if cat:
            cat_series = db.query(Series).join(Series.categories).filter(Category.id == cat.id).limit(8).all()
            if cat_series:
                category_rows.append({
                    "category": cat,
                    "series": cat_series
                })

    ctx.update({
        "hero_series": hero_series,
        "popular_series": popular_series,
        "new_series": new_series,
        "recent_episodes": recent_episodes,
        "category_rows": category_rows
    })

    return templates.TemplateResponse(request=request, name="index.html", context=ctx)

# --- 2. DİZİLER KATALOĞU ---
@router.get("/diziler", response_class=HTMLResponse)
def catalog_page(
    request: Request,
    kategori: Optional[str] = None,
    sirala: Optional[str] = "yeni",
    db: Session = Depends(get_db)
):
    ctx = get_base_context(request, db, "Tüm Diziler – SenaDizi")
    query = db.query(Series).options(joinedload(Series.categories))

    active_category = None
    if kategori:
        active_category = db.query(Category).filter(Category.slug == kategori).first()
        if active_category:
            query = query.join(Series.categories).filter(Category.id == active_category.id)

    if sirala == "populer":
        query = query.order_by(desc(Series.view_count))
    elif sirala == "puan":
        query = query.order_by(desc(Series.rating))
    elif sirala == "alfabetik":
        query = query.order_by(Series.title)
    else:
        query = query.order_by(desc(Series.created_at))

    all_series = query.all()

    ctx.update({
        "series_list": all_series,
        "active_category": active_category,
        "current_sort": sirala,
        "total_count": len(all_series)
    })
    return templates.TemplateResponse(request=request, name="catalog.html", context=ctx)

# --- 3. DİZİ DETAY SAYFASI ---
@router.get("/dizi/{slug}", response_class=HTMLResponse)
def series_detail_page(slug: str, request: Request, db: Session = Depends(get_db)):
    series = db.query(Series).options(
        joinedload(Series.categories),
        joinedload(Series.actors),
        joinedload(Series.seasons).joinedload(Season.episodes)
    ).filter(Series.slug == slug).first()

    if not series:
        raise HTTPException(status_code=404, detail="Dizi bulunamadı.")

    user = get_current_user_optional(request, db)
    ctx = get_base_context(request, db, f"{series.title} İzle | SenaDizi", user)

    # Favori kontrolü
    is_fav = False
    if user:
        fav = db.query(Favorite).filter(
            Favorite.user_id == user.id,
            Favorite.series_id == series.id
        ).first()
        is_fav = fav is not None

    # İlgili benzer diziler (aynı kategoriden)
    related_series = []
    if series.categories:
        cat_id = series.categories[0].id
        related_series = db.query(Series).join(Series.categories).filter(
            Category.id == cat_id,
            Series.id != series.id
        ).limit(6).all()

    # İlk oynatılabilir bölüm (Sezon 1 Bölüm 1 veya ilk mevcut bölüm)
    first_episode = None
    if series.seasons and series.seasons[0].episodes:
        first_episode = series.seasons[0].episodes[0]

    ctx.update({
        "series": series,
        "is_favorite": is_fav,
        "related_series": related_series,
        "first_episode": first_episode,
        "meta_description": f"{series.title} dizisini tüm bölümleriyle Full HD kalitesinde SenaDizi'te izleyin. {series.description[:120]}..."
    })

    return templates.TemplateResponse(request=request, name="detail.html", context=ctx)

# --- 4. BÖLÜM VE VİDEO OYNATICI SAYFASI ---
@router.get("/dizi/{slug}/sezon-{season_num}/bolum-{ep_num}", response_class=HTMLResponse)
def player_page(
    slug: str,
    season_num: int,
    ep_num: int,
    request: Request,
    db: Session = Depends(get_db)
):
    series = db.query(Series).options(
        joinedload(Series.categories),
        joinedload(Series.seasons).joinedload(Season.episodes)
    ).filter(Series.slug == slug).first()

    if not series:
        raise HTTPException(status_code=404, detail="Dizi bulunamadı.")

    season = db.query(Season).filter(
        Season.series_id == series.id,
        Season.season_number == season_num
    ).first()

    if not season:
        raise HTTPException(status_code=404, detail="Sezon bulunamadı.")

    episode = db.query(Episode).filter(
        Episode.season_id == season.id,
        Episode.episode_number == ep_num
    ).first()

    if not episode:
        raise HTTPException(status_code=404, detail="Bölüm bulunamadı.")

    user = get_current_user_optional(request, db)
    
    # Premium içerik kontrolü
    is_locked = False
    if not episode.is_free or series.is_premium_only:
        if not user:
            is_locked = True
        else:
            # Aktif ücretli aboneliği var mı kontrol et
            active_sub = db.query(Subscription).join(SubscriptionPlan).filter(
                Subscription.user_id == user.id,
                Subscription.status == "active",
                SubscriptionPlan.price > 0
            ).first()
            if not active_sub and user.role != UserRole.ADMIN:
                is_locked = True

    ctx = get_base_context(
        request,
        db,
        f"{series.title} {season.season_number}. Sezon {episode.episode_number}. Bölüm İzle | SenaDizi",
        user
    )

    # Önceki & Sonraki Bölüm
    prev_ep = db.query(Episode).filter(
        Episode.season_id == season.id,
        Episode.episode_number == ep_num - 1
    ).first()

    next_ep = db.query(Episode).filter(
        Episode.season_id == season.id,
        Episode.episode_number == ep_num + 1
    ).first()

    # Kullanıcının kaldığı süre
    resume_seconds = 0.0
    if user:
        prog = db.query(WatchProgress).filter(
            WatchProgress.user_id == user.id,
            WatchProgress.episode_id == episode.id
        ).first()
        if prog:
            resume_seconds = prog.progress_seconds

    # Tüm sezon bölümleri (oynatıcı menüsü için)
    season_episodes = db.query(Episode).filter(Episode.season_id == season.id).order_by(Episode.episode_number).all()

    ctx.update({
        "series": series,
        "season": season,
        "episode": episode,
        "is_locked": is_locked,
        "prev_ep": prev_ep,
        "next_ep": next_ep,
        "resume_seconds": resume_seconds,
        "season_episodes": season_episodes
    })

    return templates.TemplateResponse(request=request, name="player.html", context=ctx)

# --- 5. DİĞER KULLANICI SAYFALARI ---
@router.get("/kategoriler", response_class=HTMLResponse)
def categories_page(request: Request, db: Session = Depends(get_db)):
    ctx = get_base_context(request, db, "Kategoriler – SenaDizi")
    categories = db.query(Category).filter(Category.is_active == True).all()
    ctx["all_categories"] = categories
    return templates.TemplateResponse(request=request, name="categories.html", context=ctx)

@router.get("/populer", response_class=HTMLResponse)
def popular_page(request: Request, db: Session = Depends(get_db)):
    ctx = get_base_context(request, db, "En Popüler Diziler – SenaDizi")
    series_list = db.query(Series).order_by(desc(Series.view_count)).limit(30).all()
    ctx["series_list"] = series_list
    ctx["page_heading"] = "En Popüler Diziler"
    return templates.TemplateResponse(request=request, name="catalog.html", context=ctx)

@router.get("/yeni-eklenenler", response_class=HTMLResponse)
def new_releases_page(request: Request, db: Session = Depends(get_db)):
    ctx = get_base_context(request, db, "Yeni Eklenen Diziler – SenaDizi")
    series_list = db.query(Series).order_by(desc(Series.created_at)).limit(30).all()
    ctx["series_list"] = series_list
    ctx["page_heading"] = "Yeni Eklenen Diziler"
    return templates.TemplateResponse(request=request, name="catalog.html", context=ctx)

@router.get("/ara", response_class=HTMLResponse)
def search_page(request: Request, q: Optional[str] = None, db: Session = Depends(get_db)):
    ctx = get_base_context(request, db, f"Arama: {q or ''} – SenaDizi")
    results = []
    if q and q.strip():
        term = f"%{q.strip().lower()}%"
        results = db.query(Series).filter(
            or_(
                Series.title.ilike(term),
                Series.description.ilike(term),
                Series.director.ilike(term)
            )
        ).all()

    ctx.update({
        "query": q or "",
        "results": results,
        "count": len(results)
    })
    return templates.TemplateResponse(request=request, name="search.html", context=ctx)

@router.get("/favoriler", response_class=HTMLResponse)
def favorites_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        return Response(status_code=302, headers={"Location": "/giris?next=/favoriler"})

    ctx = get_base_context(request, db, "Favorilerim – SenaDizi", user)
    favs = db.query(Favorite).filter(Favorite.user_id == user.id).options(
        joinedload(Favorite.series)
    ).order_by(desc(Favorite.created_at)).all()

    ctx["favorites"] = [f.series for f in favs if f.series]
    return templates.TemplateResponse(request=request, name="favorites.html", context=ctx)

@router.get("/gecmis", response_class=HTMLResponse)
def history_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        return Response(status_code=302, headers={"Location": "/giris?next=/gecmis"})

    ctx = get_base_context(request, db, "İzleme Geçmişi – SenaDizi", user)
    history_items = db.query(WatchHistory).filter(WatchHistory.user_id == user.id).options(
        joinedload(WatchHistory.episode).joinedload(Episode.season).joinedload(Season.series)
    ).order_by(desc(WatchHistory.watched_at)).all()

    items = []
    for h in history_items:
        if h.episode and h.episode.season and h.episode.season.series:
            prog = db.query(WatchProgress).filter(
                WatchProgress.user_id == user.id,
                WatchProgress.episode_id == h.episode.id
            ).first()
            items.append({
                "history": h,
                "episode": h.episode,
                "season": h.episode.season,
                "series": h.episode.season.series,
                "progress_percent": round((prog.progress_seconds / prog.duration_seconds) * 100, 1) if (prog and prog.duration_seconds > 0) else 0
            })

    ctx["history_items"] = items
    return templates.TemplateResponse(request=request, name="history.html", context=ctx)

@router.get("/profil", response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        return Response(status_code=302, headers={"Location": "/giris?next=/profil"})

    ctx = get_base_context(request, db, "Profilim – SenaDizi", user)
    active_sub = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active"
    ).first()

    ctx["subscription"] = active_sub
    return templates.TemplateResponse(request=request, name="profile.html", context=ctx)

@router.get("/abonelik", response_class=HTMLResponse)
def subscription_page(request: Request, db: Session = Depends(get_db)):
    ctx = get_base_context(request, db, "Abonelik Planları – SenaDizi")
    plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).order_by(SubscriptionPlan.price).all()
    ctx["plans"] = plans
    return templates.TemplateResponse(request=request, name="subscription.html", context=ctx)

@router.get("/giris", response_class=HTMLResponse)
def login_page(request: Request, next: Optional[str] = "/", db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        return Response(status_code=302, headers={"Location": next or "/"})
    ctx = get_base_context(request, db, "Giriş Yap – SenaDizi")
    ctx["next_url"] = next
    return templates.TemplateResponse(request=request, name="login.html", context=ctx)

@router.get("/kayit", response_class=HTMLResponse)
def register_page(request: Request, next: Optional[str] = "/", db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        return Response(status_code=302, headers={"Location": next or "/"})
    ctx = get_base_context(request, db, "Kayıt Ol – SenaDizi")
    ctx["next_url"] = next
    return templates.TemplateResponse(request=request, name="register.html", context=ctx)

# --- 6. KURUMSAL & HUKUKİ SAYFALAR ---
@router.get("/hakkimizda", response_class=HTMLResponse)
def about_page(request: Request, db: Session = Depends(get_db)):
    ctx = get_base_context(request, db, "Hakkımızda – SenaDizi")
    ctx["legal_title"] = "Hakkımızda"
    ctx["legal_type"] = "about"
    return templates.TemplateResponse(request=request, name="legal.html", context=ctx)

@router.get("/iletisim", response_class=HTMLResponse)
def contact_page(request: Request, db: Session = Depends(get_db)):
    ctx = get_base_context(request, db, "İletişim – SenaDizi")
    ctx["legal_title"] = "İletişim"
    ctx["legal_type"] = "contact"
    return templates.TemplateResponse(request=request, name="legal.html", context=ctx)

@router.get("/gizlilik-politikasi", response_class=HTMLResponse)
def privacy_page(request: Request, db: Session = Depends(get_db)):
    ctx = get_base_context(request, db, "Gizlilik Politikası – SenaDizi")
    ctx["legal_title"] = "Gizlilik Politikası"
    ctx["legal_type"] = "privacy"
    return templates.TemplateResponse(request=request, name="legal.html", context=ctx)

@router.get("/kullanim-sartlari", response_class=HTMLResponse)
def terms_page(request: Request, db: Session = Depends(get_db)):
    ctx = get_base_context(request, db, "Kullanım Şartları – SenaDizi")
    ctx["legal_title"] = "Kullanım Şartları"
    ctx["legal_type"] = "terms"
    return templates.TemplateResponse(request=request, name="legal.html", context=ctx)

@router.get("/kvkk", response_class=HTMLResponse)
def kvkk_page(request: Request, db: Session = Depends(get_db)):
    ctx = get_base_context(request, db, "KVKK Aydınlatma Metni – SenaDizi")
    ctx["legal_title"] = "KVKK Aydınlatma Metni"
    ctx["legal_type"] = "kvkk"
    return templates.TemplateResponse(request=request, name="legal.html", context=ctx)

@router.get("/telif-hakki", response_class=HTMLResponse)
def copyright_page(request: Request, db: Session = Depends(get_db)):
    ctx = get_base_context(request, db, "Telif Hakkı ve Lisans Bildirimi – SenaDizi")
    ctx["legal_title"] = "Telif Hakkı ve Lisans Bildirimi"
    ctx["legal_type"] = "copyright"
    return templates.TemplateResponse(request=request, name="legal.html", context=ctx)

# --- 7. ADMIN PANELİ GÖRÜNÜMLERİ ---
@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or user.role != UserRole.ADMIN:
        return Response(status_code=302, headers={"Location": "/giris?next=/admin"})

    ctx = get_base_context(request, db, "Yönetim Paneli – SenaDizi", user)
    return templates.TemplateResponse(request=request, name="admin/dashboard.html", context=ctx)

@router.get("/admin/series", response_class=HTMLResponse)
def admin_series(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or user.role != UserRole.ADMIN:
        return Response(status_code=302, headers={"Location": "/giris?next=/admin/series"})

    ctx = get_base_context(request, db, "Dizi Yönetimi – SenaDizi", user)
    series_list = db.query(Series).options(joinedload(Series.categories)).order_by(desc(Series.created_at)).all()
    categories = db.query(Category).all()
    ctx.update({"series_list": series_list, "categories": categories})
    return templates.TemplateResponse(request=request, name="admin/series.html", context=ctx)

@router.get("/admin/episodes", response_class=HTMLResponse)
def admin_episodes(request: Request, series_id: Optional[int] = None, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or user.role != UserRole.ADMIN:
        return Response(status_code=302, headers={"Location": "/giris?next=/admin/episodes"})

    ctx = get_base_context(request, db, "Bölüm Yönetimi – SenaDizi", user)
    all_series = db.query(Series).order_by(Series.title).all()
    
    selected_series = None
    seasons = []
    if series_id:
        selected_series = db.query(Series).filter(Series.id == series_id).first()
    elif all_series:
        selected_series = all_series[0]

    if selected_series:
        seasons = db.query(Season).filter(Season.series_id == selected_series.id).options(
            joinedload(Season.episodes)
        ).order_by(Season.season_number).all()

    ctx.update({
        "all_series": all_series,
        "selected_series": selected_series,
        "seasons": seasons
    })
    return templates.TemplateResponse(request=request, name="admin/episodes.html", context=ctx)

@router.get("/admin/categories", response_class=HTMLResponse)
def admin_categories(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or user.role != UserRole.ADMIN:
        return Response(status_code=302, headers={"Location": "/giris?next=/admin/categories"})

    ctx = get_base_context(request, db, "Kategori Yönetimi – SenaDizi", user)
    cats = db.query(Category).all()
    ctx["categories"] = cats
    return templates.TemplateResponse(request=request, name="admin/categories.html", context=ctx)

@router.get("/admin/users", response_class=HTMLResponse)
def admin_users(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or user.role != UserRole.ADMIN:
        return Response(status_code=302, headers={"Location": "/giris?next=/admin/users"})

    ctx = get_base_context(request, db, "Kullanıcı Yönetimi – SenaDizi", user)
    users = db.query(User).order_by(desc(User.created_at)).all()
    ctx["users_list"] = users
    return templates.TemplateResponse(request=request, name="admin/users.html", context=ctx)

@router.get("/admin/subscriptions", response_class=HTMLResponse)
def admin_subscriptions(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or user.role != UserRole.ADMIN:
        return Response(status_code=302, headers={"Location": "/giris?next=/admin/subscriptions"})

    ctx = get_base_context(request, db, "Abonelik Yönetimi – SenaDizi", user)
    plans = db.query(SubscriptionPlan).all()
    ctx["plans"] = plans
    return templates.TemplateResponse(request=request, name="admin/subscriptions.html", context=ctx)

@router.get("/admin/analytics", response_class=HTMLResponse)
def admin_analytics(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or user.role != UserRole.ADMIN:
        return Response(status_code=302, headers={"Location": "/giris?next=/admin/analytics"})

    ctx = get_base_context(request, db, "İzlenme & Analiz – SenaDizi", user)
    return templates.TemplateResponse(request=request, name="admin/analytics.html", context=ctx)

@router.get("/admin/manual-import", response_class=HTMLResponse)
def admin_manual_import(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or user.role != UserRole.ADMIN:
        return Response(status_code=302, headers={"Location": "/giris?next=/admin/manual-import"})

    ctx = get_base_context(request, db, "Manuel İçe Aktar – SenaDizi", user)
    all_series = db.query(Series).order_by(Series.title).all()
    ctx["all_series"] = all_series
    return templates.TemplateResponse(request=request, name="admin/manual_import.html", context=ctx)

@router.get("/admin/server-status", response_class=HTMLResponse)
def admin_server_status(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or user.role != UserRole.ADMIN:
        return Response(status_code=302, headers={"Location": "/giris?next=/admin/server-status"})

    ctx = get_base_context(request, db, "Sunucu Durumu – SenaDizi", user)
    return templates.TemplateResponse(request=request, name="admin/server_status.html", context=ctx)

@router.get("/admin/announcements", response_class=HTMLResponse)
def admin_announcements(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or user.role != UserRole.ADMIN:
        return Response(status_code=302, headers={"Location": "/giris?next=/admin/announcements"})

    ctx = get_base_context(request, db, "Duyuru Yönetimi – SenaDizi", user)
    return templates.TemplateResponse(request=request, name="admin/announcements.html", context=ctx)

@router.get("/admin/settings", response_class=HTMLResponse)
def admin_settings(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user or user.role != UserRole.ADMIN:
        return Response(status_code=302, headers={"Location": "/giris?next=/admin/settings"})

    ctx = get_base_context(request, db, "Site Ayarları – SenaDizi", user)
    return templates.TemplateResponse(request=request, name="admin/settings.html", context=ctx)

# --- 8. SEO: SITEMAP & ROBOTS ---
@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    return f"""User-agent: *
Allow: /
Disallow: /admin
Disallow: /api/admin
Disallow: /profil
Disallow: /favoriler
Disallow: /gecmis

Sitemap: {settings.BASE_URL}/sitemap.xml
"""

@router.get("/sitemap.xml", response_class=FastAPIResponse)
def sitemap_xml(db: Session = Depends(get_db)):
    series = db.query(Series).all()
    categories = db.query(Category).all()

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f'  <url><loc>{settings.BASE_URL}/</loc><priority>1.0</priority><changefreq>daily</changefreq></url>',
        f'  <url><loc>{settings.BASE_URL}/diziler</loc><priority>0.9</priority><changefreq>daily</changefreq></url>',
        f'  <url><loc>{settings.BASE_URL}/kategoriler</loc><priority>0.8</priority><changefreq>weekly</changefreq></url>',
        f'  <url><loc>{settings.BASE_URL}/abonelik</loc><priority>0.8</priority><changefreq>monthly</changefreq></url>'
    ]

    for c in categories:
        xml_lines.append(f'  <url><loc>{settings.BASE_URL}/diziler?kategori={c.slug}</loc><priority>0.7</priority></url>')

    for s in series:
        xml_lines.append(f'  <url><loc>{settings.BASE_URL}/dizi/{s.slug}</loc><priority>0.9</priority><changefreq>weekly</changefreq></url>')

    xml_lines.append('</urlset>')
    return FastAPIResponse(content="\n".join(xml_lines), media_type="application/xml")
