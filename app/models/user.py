from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from app.database import Base

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    avatar_url = Column(String(255), default="/static/img/default-avatar.png")
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    history = relationship("WatchHistory", back_populates="user", cascade="all, delete-orphan")
    progress = relationship("WatchProgress", back_populates="user", cascade="all, delete-orphan")
