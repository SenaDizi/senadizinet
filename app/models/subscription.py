from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False) # Örn: Ücretsiz, Premium, VIP Sinema
    slug = Column(String(100), unique=True, index=True, nullable=False)
    price = Column(Float, default=0.0) # 0.0, 79.99 vb.
    currency = Column(String(10), default="TRY")
    billing_period = Column(String(20), default="monthly") # monthly, yearly, lifetime
    description = Column(Text, nullable=True)
    features_json = Column(Text, default="[]") # JSON list of strings
    is_popular = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    subscriptions = relationship("Subscription", back_populates="plan")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    status = Column(String(20), default="active") # active, expired, cancelled
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=True)
    transaction_id = Column(String(100), unique=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="TRY")
    provider = Column(String(50), default="demo") # stripe, iyzico, paytr, demo
    status = Column(String(20), default="completed") # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
