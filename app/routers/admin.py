import json
import re
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from app.database import get_db
from app.models.user import User, UserRole
from app.models.content import Series, Season, Episode, Category, Actor, series_categories, series_actors
from app.models.subscription import SubscriptionPlan, Subscription, Payment
from app.models.system import SiteSetting, AdminLog
from app.schemas.admin import (
    SeriesCreate, SeriesUpdate, SeasonCreate, EpisodeCreate, EpisodeUpdate,
    BulkEpisodesCreate, CategoryCreate, PlanCreate, SiteSettingUpdate
)
from app.security import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["Yönetim Paneli (Admin)"])

def slugify(text: str) -> str:
    text = text.lower().strip()
    tr_map = str.maketrans("çğıöşü", "cgiosu")
    text = text.translate(tr_map)
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text)

def log_admin_action(db: Session, admin: User, action: str, target: str, request: Request):
    ip = request.client.host if request.client else "127.0.0.1"
    log = AdminLog(
        admin_id=admin.id,
        admin_name=admin.username,
        action=action,
        target=target,
        ip_address=ip
    )
    db.add(log)
    db.commit()

# --- 1. DASHBOARD İSTATİSTİKLERİ ---
@router.get("/dashboard-stats")
def get_dashboard_stats(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_series = db.query(Series).count()
    total_seasons = db.query(Season).count()
    total_episodes = db.query(Episode).count()
    total_categories = db.query(Category).count()
    
    # Premium / Ücretli Abonelikler
    active_paid_subs = db.query(Subscription).join(SubscriptionPlan).filter(
        Subscription.status == "active",
        SubscriptionPlan.price > 0
    ).count()

    total_revenue = db.query(func.sum(Payment.amount)).filter(Payment.status == "completed").scalar() or 0.0

    recent_series = db.query(Series).order_by(desc(Series.created_at)).limit(5).all()
    recent_episodes = db.query(Episode).options(
        joinedload(Episode.season).joinedload(Season.series)
    ).order_by(desc(Episode.created_at)).limit(5).all()

    recent_users = db.query(User).order_by(desc(User.created_at)).limit(5).all()

    return {
        "stats": {
            "total_users": total_users,
            "active_users": active_users,
            "total_series": total_series,
            "total_seasons": total_seasons,
            "total_episodes": total_episodes,
            "total_categories": total_categories,
            "active_paid_subs": active_paid_subs,
            "total_revenue": round(total_revenue, 2)
        },
        "recent_series": [
            {
                "id": s.id,
                "title": s.title,
                "slug": s.slug,
                "poster_url": s.poster_url,
                "rating": s.rating,
                "created_at": s.created_at.strftime("%d.%m.%Y %H:%M")
            }
            for s in recent_series
        ],
        "recent_episodes": [
            {
                "id": ep.id,
                "title": ep.title,
                "series_title": ep.season.series.title if ep.season and ep.season.series else "-",
                "season_num": ep.season.season_number if ep.season else 1,
                "episode_num": ep.episode_number,
                "created_at": ep.created_at.strftime("%d.%m.%Y %H:%M")
            }
            for ep in recent_episodes
        ],
        "recent_users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role.value,
                "is_active": u.is_active,
                "created_at": u.created_at.strftime("%d.%m.%Y")
            }
            for u in recent_users
        ]
    }

# --- 2. DİZİ YÖNETİMİ (SERIES CRUD) ---
@router.post("/series")
def create_series(data: SeriesCreate, request: Request, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    slug = data.slug or slugify(data.title)
    # Slug benzersizlik
    existing = db.query(Series).filter(Series.slug == slug).first()
    if existing:
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

    new_series = Series(
        title=data.title,
        slug=slug,
        description=data.description,
        poster_url=data.poster_url,
        banner_url=data.banner_url or data.poster_url,
        release_year=data.release_year,
        country=data.country,
        director=data.director,
        rating=data.rating,
        status=data.status,
        is_featured=data.is_featured,
        is_popular=data.is_popular,
        is_premium_only=data.is_premium_only
    )

    # Kategorileri bağla
    if data.category_ids:
        cats = db.query(Category).filter(Category.id.in_(data.category_ids)).all()
        new_series.categories = cats

    # Oyuncuları bağla veya oluştur
    if data.actor_names:
        actors_list = []
        for name in data.actor_names:
            clean_name = name.strip()
            if not clean_name:
                continue
            actor_slug = slugify(clean_name)
            act = db.query(Actor).filter(Actor.slug == actor_slug).first()
            if not act:
                act = Actor(name=clean_name, slug=actor_slug)
                db.add(act)
                db.flush()
            actors_list.append(act)
        new_series.actors = actors_list

    db.add(new_series)
    db.commit()
    db.refresh(new_series)

    # Otomatik 1. Sezon oluştur
    default_season = Season(series_id=new_series.id, season_number=1, title="1. Sezon")
    db.add(default_season)
    db.commit()

    log_admin_action(db, admin, "CREATE_SERIES", new_series.title, request)
    return {"message": "Dizi başarıyla oluşturuldu.", "series_id": new_series.id, "slug": new_series.slug}

@router.put("/series/{series_id}")
def update_series(series_id: int, data: SeriesUpdate, request: Request, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Dizi bulunamadı.")

    for field, val in data.dict(exclude_unset=True).items():
        if field not in ["category_ids", "actor_names"]:
            setattr(series, field, val)

    if data.category_ids is not None:
        cats = db.query(Category).filter(Category.id.in_(data.category_ids)).all()
        series.categories = cats

    if data.actor_names is not None:
        actors_list = []
        for name in data.actor_names:
            clean_name = name.strip()
            if not clean_name:
                continue
            actor_slug = slugify(clean_name)
            act = db.query(Actor).filter(Actor.slug == actor_slug).first()
            if not act:
                act = Actor(name=clean_name, slug=actor_slug)
                db.add(act)
                db.flush()
            actors_list.append(act)
        series.actors = actors_list

    series.updated_at = datetime.utcnow()
    db.commit()

    log_admin_action(db, admin, "UPDATE_SERIES", series.title, request)
    return {"message": "Dizi başarıyla güncellendi."}

@router.delete("/series/{series_id}")
def delete_series(series_id: int, request: Request, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Dizi bulunamadı.")

    title = series.title
    db.delete(series)
    db.commit()

    log_admin_action(db, admin, "DELETE_SERIES", title, request)
    return {"message": f"'{title}' dizisi başarıyla silindi."}

# --- 3. SEZON & BÖLÜM YÖNETİMİ (SEASONS & EPISODES CRUD) ---
@router.post("/seasons")
def create_season(data: SeasonCreate, request: Request, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    existing = db.query(Season).filter(
        Season.series_id == data.series_id,
        Season.season_number == data.season_number
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"{data.season_number}. Sezon zaten mevcut.")

    new_season = Season(
        series_id=data.series_id,
        season_number=data.season_number,
        title=data.title or f"{data.season_number}. Sezon",
        description=data.description
    )
    db.add(new_season)
    db.commit()
    db.refresh(new_season)

    log_admin_action(db, admin, "CREATE_SEASON", f"Series #{data.series_id} - S{data.season_number}", request)
    return {"message": "Sezon oluşturuldu.", "season_id": new_season.id}

@router.post("/episodes")
def create_episode(data: EpisodeCreate, request: Request, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    new_ep = Episode(
        season_id=data.season_id,
        episode_number=data.episode_number,
        title=data.title,
        description=data.description,
        thumbnail_url=data.thumbnail_url,
        video_url=data.video_url,
        duration_minutes=data.duration_minutes,
        is_free=data.is_free
    )
    db.add(new_ep)
    db.commit()
    db.refresh(new_ep)

    log_admin_action(db, admin, "CREATE_EPISODE", f"Ep #{data.episode_number} - {data.title}", request)
    return {"message": "Bölüm başarıyla eklendi.", "episode_id": new_ep.id}

@router.post("/episodes/bulk")
def create_bulk_episodes(data: BulkEpisodesCreate, request: Request, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    season = db.query(Season).filter(Season.id == data.season_id).first()
    if not season:
        raise HTTPException(status_code=404, detail="Sezon bulunamadı.")

    created_count = 0
    for i in range(data.count):
        ep_num = data.start_number + i
        # Varsa güncelle yoksa ekle
        ep = db.query(Episode).filter(
            Episode.season_id == data.season_id,
            Episode.episode_number == ep_num
        ).first()

        title = data.title_pattern.replace("{number}", str(ep_num))
        v_url = data.video_url_pattern.replace("{number}", str(ep_num)) if data.video_url_pattern else "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"

        if not ep:
            ep = Episode(
                season_id=data.season_id,
                episode_number=ep_num,
                title=title,
                video_url=v_url,
                duration_minutes=data.duration_minutes,
                is_free=data.is_free
            )
            db.add(ep)
            created_count += 1

    db.commit()
    log_admin_action(db, admin, "BULK_CREATE_EPISODES", f"Season #{data.season_id} - {created_count} episodes", request)
    return {"message": f"{created_count} adet bölüm başarıyla oluşturuldu."}

@router.put("/episodes/{episode_id}")
def update_episode(episode_id: int, data: EpisodeUpdate, request: Request, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    ep = db.query(Episode).filter(Episode.id == episode_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Bölüm bulunamadı.")

    for field, val in data.dict(exclude_unset=True).items():
        setattr(ep, field, val)

    db.commit()
    log_admin_action(db, admin, "UPDATE_EPISODE", ep.title, request)
    return {"message": "Bölüm güncellendi."}

@router.delete("/episodes/{episode_id}")
def delete_episode(episode_id: int, request: Request, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    ep = db.query(Episode).filter(Episode.id == episode_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Bölüm bulunamadı.")

    title = ep.title
    db.delete(ep)
    db.commit()

    log_admin_action(db, admin, "DELETE_EPISODE", title, request)
    return {"message": "Bölüm silindi."}

# --- 4. KATEGORİ YÖNETİMİ ---
@router.post("/categories")
def create_category(data: CategoryCreate, request: Request, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    slug = data.slug or slugify(data.name)
    existing = db.query(Category).filter(Category.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu kategori zaten mevcut.")

    cat = Category(
        name=data.name,
        slug=slug,
        description=data.description,
        icon=data.icon or "fa-film"
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)

    log_admin_action(db, admin, "CREATE_CATEGORY", cat.name, request)
    return {"message": "Kategori oluşturuldu.", "category_id": cat.id}

@router.delete("/categories/{cat_id}")
def delete_category(cat_id: int, request: Request, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Kategori bulunamadı.")
    name = cat.name
    db.delete(cat)
    db.commit()
    log_admin_action(db, admin, "DELETE_CATEGORY", name, request)
    return {"message": f"'{name}' kategorisi silindi."}

# --- 5. KULLANICI YÖNETİMİ ---
@router.get("/users")
def list_users(limit: int = 50, offset: int = 0, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    users = db.query(User).order_by(desc(User.created_at)).offset(offset).limit(limit).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "is_active": u.is_active,
            "created_at": u.created_at.strftime("%d.%m.%Y %H:%M")
        }
        for u in users
    ]

@router.post("/users/{user_id}/toggle-status")
def toggle_user_status(user_id: int, request: Request, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Kendi yönetici hesabınızı pasif yapamazsınız.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")

    user.is_active = not user.is_active
    db.commit()

    status_str = "Aktif" if user.is_active else "Pasif"
    log_admin_action(db, admin, "TOGGLE_USER_STATUS", f"User #{user.id} -> {status_str}", request)
    return {"message": f"Kullanıcı durumu '{status_str}' yapıldı.", "is_active": user.is_active}

# --- 6. ABONELİK PLANLARI CRUD ---
@router.post("/plans")
def create_plan(data: PlanCreate, request: Request, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    plan = SubscriptionPlan(
        name=data.name,
        slug=data.slug,
        price=data.price,
        currency=data.currency,
        billing_period=data.billing_period,
        description=data.description,
        features_json=json.dumps(data.features, ensure_ascii=False),
        is_popular=data.is_popular,
        is_active=data.is_active
    )
    db.add(plan)
    db.commit()
    log_admin_action(db, admin, "CREATE_PLAN", plan.name, request)
    return {"message": "Plan oluşturuldu."}

# --- 7. SİTE AYARLARI ---
@router.get("/settings")
def get_site_settings(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    settings_records = db.query(SiteSetting).all()
    res = {}
    for s in settings_records:
        res[s.key] = s.value
    return res

@router.post("/settings")
def update_site_settings(data: SiteSettingUpdate, request: Request, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    for k, v in data.dict(exclude_unset=True).items():
        if v is not None:
            setting = db.query(SiteSetting).filter(SiteSetting.key == k).first()
            if setting:
                setting.value = str(v)
            else:
                setting = SiteSetting(key=k, value=str(v))
                db.add(setting)
    db.commit()
    log_admin_action(db, admin, "UPDATE_SETTINGS", "Site configuration updated", request)
    return {"message": "Site ayarları başarıyla güncellendi."}
