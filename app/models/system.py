from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base

class SiteSetting(Base):
    __tablename__ = "site_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(String(255), nullable=True)

class AdminLog(Base):
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, nullable=False)
    admin_name = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False) # CREATE_SERIES, UPDATE_EPISODE, etc.
    target = Column(String(200), nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
