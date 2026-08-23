from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Table, Text
from sqlalchemy.orm import relationship
from app.database import Base

# Many-to-Many tabloları
series_categories = Table(
    "series_categories",
    Base.metadata,
    Column("series_id", Integer, ForeignKey("series.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True)
)

series_actors = Table(
    "series_actors",
    Base.metadata,
    Column("series_id", Integer, ForeignKey("series.id", ondelete="CASCADE"), primary_key=True),
    Column("actor_id", Integer, ForeignKey("actors.id", ondelete="CASCADE"), primary_key=True)
)

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), default="fa-film")
    is_active = Column(Boolean, default=True)

    series = relationship("Series", secondary=series_categories, back_populates="categories")

class Actor(Base):
    __tablename__ = "actors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    photo_url = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)

    series = relationship("Series", secondary=series_actors, back_populates="actors")

class Series(Base):
    __tablename__ = "series"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True, nullable=False)
    slug = Column(String(200), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    poster_url = Column(String(500), nullable=False) # Dikey kapak
    banner_url = Column(String(500), nullable=True) # Yatay hero banner
    release_year = Column(Integer, default=2026)
    country = Column(String(100), default="Türkiye")
    director = Column(String(100), nullable=True)
    rating = Column(Float, default=8.5)
    status = Column(String(50), default="Devam Ediyor") # Devam Ediyor, Tamamlandı, Yakında
    is_featured = Column(Boolean, default=False) # Hero sliderda gösterilsin mi
    is_popular = Column(Boolean, default=False)
    is_premium_only = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    categories = relationship("Category", secondary=series_categories, back_populates="series")
    actors = relationship("Actor", secondary=series_actors, back_populates="series")
    seasons = relationship("Season", back_populates="series", cascade="all, delete-orphan", order_by="Season.season_number")
    favorites = relationship("Favorite", back_populates="series", cascade="all, delete-orphan")

class Season(Base):
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey("series.id", ondelete="CASCADE"), nullable=False)
    season_number = Column(Integer, nullable=False)
    title = Column(String(100), nullable=True) # Örn: "1. Sezon"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    series = relationship("Series", back_populates="seasons")
    episodes = relationship("Episode", back_populates="season", cascade="all, delete-orphan", order_by="Episode.episode_number")

class Episode(Base):
    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, index=True)
    season_id = Column(Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False)
    episode_number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    video_url = Column(String(1000), nullable=False) # MP4 veya HLS m3u8 akışı
    duration_minutes = Column(Integer, default=45)
    release_date = Column(DateTime, default=datetime.utcnow)
    is_free = Column(Boolean, default=True) # Ücretsiz veya Premium
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    season = relationship("Season", back_populates="episodes")
    history = relationship("WatchHistory", back_populates="episode", cascade="all, delete-orphan")
    progress = relationship("WatchProgress", back_populates="episode", cascade="all, delete-orphan")
