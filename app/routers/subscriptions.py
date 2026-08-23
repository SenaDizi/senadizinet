import json
import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.subscription import SubscriptionPlan, Subscription, Payment
from app.security import get_current_user

router = APIRouter(prefix="/api/subscriptions", tags=["Abonelik & Ödemeler"])

class SubscribeRequest(BaseModel):
    plan_slug: str

@router.get("/plans")
def get_subscription_plans(db: Session = Depends(get_db)):
    plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).order_by(SubscriptionPlan.price).all()
    result = []
    for p in plans:
        features = []
        try:
            features = json.loads(p.features_json) if p.features_json else []
        except Exception:
            features = []
        result.append({
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "price": p.price,
            "currency": p.currency,
            "billing_period": p.billing_period,
            "description": p.description,
            "features": features,
            "is_popular": p.is_popular
        })
    return result

@router.post("/checkout")
def create_subscription_checkout(data: SubscribeRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.slug == data.plan_slug,
        SubscriptionPlan.is_active == True
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="Seçilen abonelik planı bulunamadı.")

    # Simüle edilmiş / Webhook uyumlu ödeme kaydı ve abonelik aktivasyonu
    tx_id = f"TX-{uuid.uuid4().hex[:12].upper()}"
    payment = Payment(
        user_id=user.id,
        plan_id=plan.id,
        transaction_id=tx_id,
        amount=plan.price,
        currency=plan.currency,
        provider="demo",
        status="completed"
    )
    db.add(payment)

    # Kullanıcının mevcut aktif aboneliğini güncelle veya oluştur
    existing_sub = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == "active"
    ).first()

    days = 30 if plan.billing_period == "monthly" else (365 if plan.billing_period == "yearly" else 3650)
    end_date = datetime.utcnow() + timedelta(days=days)

    if existing_sub:
        existing_sub.plan_id = plan.id
        existing_sub.end_date = end_date
        existing_sub.status = "active"
    else:
        new_sub = Subscription(
            user_id=user.id,
            plan_id=plan.id,
            status="active",
            start_date=datetime.utcnow(),
            end_date=end_date
        )
        db.add(new_sub)

    db.commit()

    return {
        "success": True,
        "message": f"{plan.name} aboneliğiniz başarıyla başlatıldı!",
        "transaction_id": tx_id,
        "plan_name": plan.name,
        "expires_at": end_date.strftime("%d.%m.%Y")
    }

@router.post("/webhook")
async def payment_webhook(request: Request, db: Session = Depends(get_db)):
    # Stripe / Iyzico / PayTR Webhook altyapısı
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    event_type = payload.get("event") or payload.get("type", "payment_succeeded")
    tx_id = payload.get("transaction_id") or payload.get("id")
    user_email = payload.get("customer_email")

    if user_email and tx_id:
        user = db.query(User).filter(User.email == user_email.lower()).first()
        if user:
            # İşlem kaydı ve abonelik güncellemesi
            payment = Payment(
                user_id=user.id,
                transaction_id=tx_id,
                amount=payload.get("amount", 0.0),
                currency=payload.get("currency", "TRY"),
                provider="webhook",
                status="completed"
            )
            db.add(payment)
            db.commit()

    return {"received": True, "event": event_type}
