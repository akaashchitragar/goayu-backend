from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class OTPRequest(BaseModel):
    email: EmailStr


class OTPVerify(BaseModel):
    email: EmailStr
    otp: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    user_id: Optional[str] = None
    token: Optional[str] = None
    user: Optional[dict] = None


class OTPRecord(BaseModel):
    email: str
    otp: str
    created_at: datetime
    expires_at: datetime
    attempts: int = 0
    verified: bool = False
