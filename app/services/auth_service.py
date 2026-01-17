import random
import string
from datetime import datetime, timedelta
from typing import Optional
import jwt
from app.core.database import get_database
from app.core.config import settings
from app.models.auth import OTPRecord
from app.models.user import User, UserCreate
from app.services.user_service import UserService
from app.services.email_service import EmailService


class AuthService:
    """Service for OTP-based authentication"""
    
    def __init__(self):
        self.db = get_database()
        self.otp_collection = self.db["otp_codes"]
        self.user_service = UserService()
        
        # Create indexes
        self.otp_collection.create_index("email")
        self.otp_collection.create_index("expires_at")
    
    def generate_otp(self, length: int = 6) -> str:
        """Generate a random OTP code"""
        return ''.join(random.choices(string.digits, k=length))
    
    def generate_token(self, user_id: str, email: str) -> str:
        """Generate JWT token for authenticated user"""
        payload = {
            "user_id": user_id,
            "email": email,
            "exp": datetime.utcnow() + timedelta(days=30),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, settings.BACKEND_URL, algorithm="HS256")
        return token
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, settings.BACKEND_URL, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def send_otp(self, email: str) -> bool:
        """Generate and send OTP to email"""
        # Generate OTP
        otp = self.generate_otp()
        
        # Create OTP record
        otp_record = OTPRecord(
            email=email,
            otp=otp,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            attempts=0,
            verified=False
        )
        
        # Delete any existing OTP for this email
        self.otp_collection.delete_many({"email": email})
        
        # Save new OTP
        self.otp_collection.insert_one(otp_record.model_dump())
        
        # Send email with OTP
        await EmailService.send_otp_email(email, otp)
        
        # Log activity
        user = await self.user_service.get_user_by_email(email)
        if user:
            await self.user_service.log_activity(
                user_id=user.user_id,
                activity_type="otp_requested",
                activity_data={"email": email}
            )
        
        return True
    
    async def verify_otp(self, email: str, otp: str) -> Optional[dict]:
        """Verify OTP and return user data with token"""
        # Find OTP record
        otp_record = self.otp_collection.find_one({
            "email": email,
            "verified": False
        })
        
        if not otp_record:
            return None
        
        # Check if expired
        if datetime.utcnow() > otp_record["expires_at"]:
            self.otp_collection.delete_one({"_id": otp_record["_id"]})
            return None
        
        # Check attempts
        if otp_record["attempts"] >= 5:
            self.otp_collection.delete_one({"_id": otp_record["_id"]})
            return None
        
        # Verify OTP
        if otp_record["otp"] != otp:
            # Increment attempts
            self.otp_collection.update_one(
                {"_id": otp_record["_id"]},
                {"$inc": {"attempts": 1}}
            )
            return None
        
        # OTP is valid - mark as verified
        self.otp_collection.update_one(
            {"_id": otp_record["_id"]},
            {"$set": {"verified": True}}
        )
        
        # Get or create user
        user = await self.user_service.get_user_by_email(email)
        
        if not user:
            # Create new user
            user_data = UserCreate(email=email)
            user = await self.user_service.create_user(user_data)
        
        # Update last login
        await self.user_service.update_last_login(user.user_id)
        
        # Generate token
        token = self.generate_token(user.user_id, email)
        
        # Log activity
        await self.user_service.log_activity(
            user_id=user.user_id,
            activity_type="login_success",
            activity_data={"email": email, "method": "otp"}
        )
        
        # Delete OTP record
        self.otp_collection.delete_one({"_id": otp_record["_id"]})
        
        return {
            "user_id": user.user_id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "blood_group": user.blood_group,
            "height": user.height,
            "weight": user.weight,
            "token": token,
            "created_at": user.created_at.isoformat(),
        }
    
    async def cleanup_expired_otps(self):
        """Remove expired OTP codes"""
        result = self.otp_collection.delete_many({
            "expires_at": {"$lt": datetime.utcnow()}
        })
        return result.deleted_count
