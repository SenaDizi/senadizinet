from datetime import datetime
from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    series_id = Column(Integer, ForeignKey("series.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="favorites")
    series = relationship("Series", back_populates="favorites")

class WatchHistory(Base):
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    episode_id = Column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False)
    watched_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="history")
    episode = relationship("Episode", back_populates="history")

class WatchProgress(Base):
    __tablename__ = "watch_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    episode_id = Column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=False)
    progress_seconds = Column(Float, default=0.0)
    duration_seconds = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="progress")
    episode = relationship("Episode", back_populates="progress")
