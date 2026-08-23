from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.subscription import Subscription, SubscriptionPlan
from app.schemas.auth import UserRegister, UserLogin, UserOut, UserProfileUpdate, PasswordChange
from app.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    get_current_user_optional
)

router = APIRouter(prefix="/api/auth", tags=["Kimlik Doğrulama"])

@router.post("/register", response_model=UserOut)
def register(data: UserRegister, response: Response, db: Session = Depends(get_db)):
    # Kullanıcı adı veya e-posta kontrolü
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(status_code=400, detail="Bu e-posta adresi zaten kullanılıyor.")
    if db.query(User).filter(User.username == data.username.lower()).first():
        raise HTTPException(status_code=400, detail="Bu kullanıcı adı zaten alınmış.")

    hashed_pw = get_password_hash(data.password)
    new_user = User(
        username=data.username.lower(),
        email=data.email.lower(),
        full_name=data.full_name or data.username,
        hashed_password=hashed_pw,
        role=UserRole.USER
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Otomatik Ücretsiz Plan aboneliği ekle
    free_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.slug == "ucretsiz").first()
    if free_plan:
        sub = Subscription(
            user_id=new_user.id,
            plan_id=free_plan.id,
            status="active"
        )
        db.add(sub)
        db.commit()

    # JWT Token oluştur ve Cookie'ye ekle
    token = create_access_token({"sub": str(new_user.id), "role": new_user.role.value})
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=604800, # 7 gün
        samesite="lax"
    )

    return UserOut(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        full_name=new_user.full_name,
        avatar_url=new_user.avatar_url,
        role=new_user.role.value,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        subscription_status="Aktif",
        subscription_plan="Ücretsiz Plan"
    )

@router.post("/login")
def login(data: UserLogin, response: Response, db: Session = Depends(get_db)):
    query_str = data.email_or_username.strip().lower()
    user = db.query(User).filter(
        (User.email == query_str) | (User.username == query_str)
    ).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Geçersiz e-posta/kullanıcı adı veya şifre.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Hesabınız askıya alınmıştır. Yönetici ile iletişime geçin.")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    response.set_cookie(
        key="access_token",
        value=f"Bearer {token}",
        httponly=True,
        max_age=604800,
        samesite="lax"
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "avatar_url": user.avatar_url
        }
    }

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Başarıyla çıkış yapıldı."}

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    active_sub = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()

    plan_name = active_sub.plan.name if active_sub and active_sub.plan else "Ücretsiz Plan"
    plan_status = "Aktif" if active_sub else "Yok"

    return UserOut(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        role=current_user.role.value,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        subscription_status=plan_status,
        subscription_plan=plan_name
    )

@router.put("/profile")
def update_profile(data: UserProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url
    db.commit()
    return {"message": "Profil başarıyla güncellendi."}

@router.post("/change-password")
def change_password(data: PasswordChange, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mevcut şifreniz hatalı.")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Yeni şifre en az 6 karakter olmalıdır.")

    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"message": "Şifreniz başarıyla değiştirildi."}
