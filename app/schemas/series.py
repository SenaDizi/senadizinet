from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = "fa-film"

    class Config:
        from_attributes = True

class ActorOut(BaseModel):
    id: int
    name: str
    slug: str
    photo_url: Optional[str] = None

    class Config:
        from_attributes = True

class EpisodeOut(BaseModel):
    id: int
    episode_number: int
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_url: str
    duration_minutes: int
    is_free: bool
    view_count: int

    class Config:
        from_attributes = True

class SeasonOut(BaseModel):
    id: int
    season_number: int
    title: Optional[str] = None
    description: Optional[str] = None
    episodes: List[EpisodeOut] = []

    class Config:
        from_attributes = True

class SeriesOut(BaseModel):
    id: int
    title: str
    slug: str
    description: str
    poster_url: str
    banner_url: Optional[str] = None
    release_year: int
    country: str
    director: Optional[str] = None
    rating: float
    status: str
    is_featured: bool
    is_popular: bool
    is_premium_only: bool
    view_count: int
    categories: List[CategoryOut] = []
    actors: List[ActorOut] = []
    seasons: List[SeasonOut] = []

    class Config:
        from_attributes = True

class SearchResult(BaseModel):
    series: List[SeriesOut] = []
    categories: List[CategoryOut] = []
    actors: List[ActorOut] = []
