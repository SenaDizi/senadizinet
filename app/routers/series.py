from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc
from app.database import get_db
from app.models.content import Series, Season, Episode, Category, Actor
from app.models.interaction import WatchProgress
from app.schemas.series import SeriesOut, SeasonOut, EpisodeOut, CategoryOut, SearchResult
from app.security import get_current_user_optional

router = APIRouter(prefix="/api/series", tags=["Diziler & İçerik"])

@router.get("", response_model=List[SeriesOut])
def get_series_list(
    category_slug: Optional[str] = None,
    featured: Optional[bool] = None,
    popular: Optional[bool] = None,
    sort: Optional[str] = Query("newest", pattern="^(newest|popular|rating|title)$"),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Series).options(
        joinedload(Series.categories),
        joinedload(Series.actors),
        joinedload(Series.seasons).joinedload(Season.episodes)
    )

    if category_slug:
        query = query.join(Series.categories).filter(Category.slug == category_slug)

    if featured is not None:
        query = query.filter(Series.is_featured == featured)

    if popular is not None:
        query = query.filter(Series.is_popular == popular)

    if sort == "newest":
        query = query.order_by(desc(Series.created_at))
    elif sort == "popular":
        query = query.order_by(desc(Series.view_count))
    elif sort == "rating":
        query = query.order_by(desc(Series.rating))
    elif sort == "title":
        query = query.order_by(Series.title)

    return query.offset(offset).limit(limit).all()

@router.get("/search", response_model=SearchResult)
def search_series(q: str = Query(..., min_length=1), limit: int = 20, db: Session = Depends(get_db)):
    term = f"%{q.strip().lower()}%"
    
    # 1. Başlık, açıklama, yönetmen veya ülkeye göre ara
    series = db.query(Series).options(
        joinedload(Series.categories),
        joinedload(Series.actors)
    ).filter(
        or_(
            Series.title.ilike(term),
            Series.description.ilike(term),
            Series.director.ilike(term),
            Series.country.ilike(term)
        )
    ).limit(limit).all()

    # 2. Kategorilere göre
    categories = db.query(Category).filter(Category.name.ilike(term)).limit(5).all()

    # 3. Oyunculara göre
    actors = db.query(Actor).filter(Actor.name.ilike(term)).limit(5).all()

    return {
        "series": series,
        "categories": categories,
        "actors": actors
    }

@router.get("/{slug}", response_model=SeriesOut)
def get_series_detail(slug: str, db: Session = Depends(get_db)):
    series = db.query(Series).options(
        joinedload(Series.categories),
        joinedload(Series.actors),
        joinedload(Series.seasons).joinedload(Season.episodes)
    ).filter(Series.slug == slug).first()

    if not series:
        raise HTTPException(status_code=404, detail="Dizi bulunamadı.")

    # İzlenme sayısını 1 artır
    series.view_count += 1
    db.commit()

    return series

@router.get("/{slug}/seasons/{season_num}/episodes/{ep_num}")
def get_episode_detail(
    slug: str,
    season_num: int,
    ep_num: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user_optional)
):
    series = db.query(Series).filter(Series.slug == slug).first()
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

    # İzlenme sayısını artır
    episode.view_count += 1
    db.commit()

    # Önceki ve sonraki bölüm
    prev_ep = db.query(Episode).filter(
        Episode.season_id == season.id,
        Episode.episode_number == ep_num - 1
    ).first()

    next_ep = db.query(Episode).filter(
        Episode.season_id == season.id,
        Episode.episode_number == ep_num + 1
    ).first()

    # Kullanıcının kaldığı saniye
    resume_seconds = 0.0
    if user:
        progress = db.query(WatchProgress).filter(
            WatchProgress.user_id == user.id,
            WatchProgress.episode_id == episode.id
        ).first()
        if progress:
            resume_seconds = progress.progress_seconds

    # Tüm bölümlerin listesi (oynatıcı içi liste için)
    all_episodes = db.query(Episode).filter(Episode.season_id == season.id).order_by(Episode.episode_number).all()

    return {
        "series": {
            "id": series.id,
            "title": series.title,
            "slug": series.slug,
            "poster_url": series.poster_url
        },
        "season": {
            "id": season.id,
            "season_number": season.season_number,
            "title": season.title
        },
        "episode": {
            "id": episode.id,
            "episode_number": episode.episode_number,
            "title": episode.title,
            "description": episode.description,
            "video_url": episode.video_url,
            "thumbnail_url": episode.thumbnail_url,
            "duration_minutes": episode.duration_minutes,
            "is_free": episode.is_free
        },
        "resume_seconds": resume_seconds,
        "has_prev": prev_ep is not None,
        "prev_ep_num": prev_ep.episode_number if prev_ep else None,
        "has_next": next_ep is not None,
        "next_ep_num": next_ep.episode_number if next_ep else None,
        "season_episodes": [
            {
                "id": ep.id,
                "episode_number": ep.episode_number,
                "title": ep.title,
                "duration_minutes": ep.duration_minutes,
                "thumbnail_url": ep.thumbnail_url,
                "is_current": ep.id == episode.id
            }
            for ep in all_episodes
        ]
    }
