from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email_or_username: str
    password: str

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    subscription_status: Optional[str] = "Ücretsiz"
    subscription_plan: Optional[str] = "Ücretsiz Plan"

    class Config:
        from_attributes = True
