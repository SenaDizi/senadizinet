from typing import List, Optional
from pydantic import BaseModel

class SeriesCreate(BaseModel):
    title: str
    slug: Optional[str] = None
    description: str
    poster_url: str
    banner_url: Optional[str] = None
    release_year: int = 2026
    country: str = "Türkiye"
    director: Optional[str] = None
    rating: float = 8.5
    status: str = "Devam Ediyor"
    is_featured: bool = False
    is_popular: bool = False
    is_premium_only: bool = False
    category_ids: List[int] = []
    actor_names: List[str] = []

class SeriesUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None
    banner_url: Optional[str] = None
    release_year: Optional[int] = None
    country: Optional[str] = None
    director: Optional[str] = None
    rating: Optional[float] = None
    status: Optional[str] = None
    is_featured: Optional[bool] = None
    is_popular: Optional[bool] = None
    is_premium_only: Optional[bool] = None
    category_ids: Optional[List[int]] = None
    actor_names: Optional[List[str]] = None

class SeasonCreate(BaseModel):
    series_id: int
    season_number: int
    title: Optional[str] = None
    description: Optional[str] = None

class EpisodeCreate(BaseModel):
    season_id: int
    episode_number: int
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_url: str
    duration_minutes: int = 45
    is_free: bool = True

class EpisodeUpdate(BaseModel):
    episode_number: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    is_free: Optional[bool] = None

class BulkEpisodesCreate(BaseModel):
    season_id: int
    start_number: int = 1
    count: int = 10
    title_pattern: str = "{number}. Bölüm" # Örn: "{number}. Bölüm"
    video_url_pattern: str = "" # Örn: "https://cdn.example.com/videos/ep{number}.mp4"
    duration_minutes: int = 45
    is_free: bool = True

class CategoryCreate(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = "fa-film"

class PlanCreate(BaseModel):
    name: str
    slug: str
    price: float
    currency: str = "TRY"
    billing_period: str = "monthly"
    description: Optional[str] = None
    features: List[str] = []
    is_popular: bool = False
    is_active: bool = True

class SiteSettingUpdate(BaseModel):
    site_name: Optional[str] = None
    site_description: Optional[str] = None
    logo_text: Optional[str] = None
    primary_color: Optional[str] = None
    contact_email: Optional[str] = None
    social_twitter: Optional[str] = None
    social_instagram: Optional[str] = None
    social_youtube: Optional[str] = None
