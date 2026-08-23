from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.database import get_db
from app.models.user import User
from app.models.content import Series, Episode, Season
from app.models.interaction import Favorite, WatchHistory, WatchProgress
from app.schemas.series import SeriesOut
from app.security import get_current_user

router = APIRouter(prefix="/api/user", tags=["Kullanıcı Özellikleri (Favori, Geçmiş, İlerleme)"])

class ProgressUpdate(BaseModel):
    episode_id: int
    progress_seconds: float
    duration_seconds: float

# --- FAVORİLER ---
@router.get("/favorites", response_model=List[SeriesOut])
def get_user_favorites(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    favs = db.query(Favorite).filter(Favorite.user_id == user.id).options(
        joinedload(Favorite.series).joinedload(Series.categories)
    ).order_by(desc(Favorite.created_at)).all()

    return [f.series for f in favs if f.series]

@router.post("/favorites/{series_id}")
def toggle_favorite(series_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Dizi bulunamadı.")

    fav = db.query(Favorite).filter(
        Favorite.user_id == user.id,
        Favorite.series_id == series_id
    ).first()

    if fav:
        db.delete(fav)
        db.commit()
        return {"status": "removed", "message": "Favorilerden çıkarıldı."}
    else:
        new_fav = Favorite(user_id=user.id, series_id=series_id)
        db.add(new_fav)
        db.commit()
        return {"status": "added", "message": "Favorilere eklendi."}

@router.get("/favorites/check/{series_id}")
def check_favorite(series_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fav = db.query(Favorite).filter(
        Favorite.user_id == user.id,
        Favorite.series_id == series_id
    ).first()
    return {"is_favorite": fav is not None}

# --- İZLEME GEÇMİŞİ ---
@router.get("/history")
def get_user_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    history_items = db.query(WatchHistory).filter(
        WatchHistory.user_id == user.id
    ).options(
        joinedload(WatchHistory.episode).joinedload(Episode.season).joinedload(Season.series)
    ).order_by(desc(WatchHistory.watched_at)).limit(30).all()

    results = []
    for h in history_items:
        if h.episode and h.episode.season and h.episode.season.series:
            # İlerleme durumunu bul
            prog = db.query(WatchProgress).filter(
                WatchProgress.user_id == user.id,
                WatchProgress.episode_id == h.episode.id
            ).first()

            results.append({
                "history_id": h.id,
                "watched_at": h.watched_at,
                "episode": {
                    "id": h.episode.id,
                    "episode_number": h.episode.episode_number,
                    "title": h.episode.title,
                    "thumbnail_url": h.episode.thumbnail_url,
                    "duration_minutes": h.episode.duration_minutes
                },
                "season": {
                    "season_number": h.episode.season.season_number
                },
                "series": {
                    "title": h.episode.season.series.title,
                    "slug": h.episode.season.series.slug,
                    "poster_url": h.episode.season.series.poster_url
                },
                "progress_seconds": prog.progress_seconds if prog else 0.0,
                "duration_seconds": prog.duration_seconds if prog else 0.0,
                "progress_percent": round((prog.progress_seconds / prog.duration_seconds) * 100, 1) if (prog and prog.duration_seconds > 0) else 0
            })

    return results

@router.delete("/history")
def clear_user_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(WatchHistory).filter(WatchHistory.user_id == user.id).delete()
    db.commit()
    return {"message": "İzleme geçmişi temizlendi."}

# --- İZLEME İLERLEMESİ (RESUME PROGRESS) ---
@router.post("/progress")
def update_watch_progress(data: ProgressUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prog = db.query(WatchProgress).filter(
        WatchProgress.user_id == user.id,
        WatchProgress.episode_id == data.episode_id
    ).first()

    is_done = (data.progress_seconds >= data.duration_seconds * 0.9) if data.duration_seconds > 0 else False

    if prog:
        prog.progress_seconds = data.progress_seconds
        prog.duration_seconds = data.duration_seconds
        prog.is_completed = is_done
        prog.updated_at = datetime.utcnow()
    else:
        prog = WatchProgress(
            user_id=user.id,
            episode_id=data.episode_id,
            progress_seconds=data.progress_seconds,
            duration_seconds=data.duration_seconds,
            is_completed=is_done
        )
        db.add(prog)

    # Ayrıca WatchHistory kaydını ekle veya güncelle
    hist = db.query(WatchHistory).filter(
        WatchHistory.user_id == user.id,
        WatchHistory.episode_id == data.episode_id
    ).first()
    if hist:
        hist.watched_at = datetime.utcnow()
    else:
        hist = WatchHistory(user_id=user.id, episode_id=data.episode_id)
        db.add(hist)

    db.commit()
    return {"status": "saved", "progress_seconds": data.progress_seconds}
