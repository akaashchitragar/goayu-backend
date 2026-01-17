from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional
from app.models.auth import OTPRequest, OTPVerify, AuthResponse
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter()


def get_auth_service():
    return AuthService()


def get_user_service():
    return UserService()


@router.post("/check-email")
async def check_email(request: OTPRequest):
    """Check if email exists in database"""
    try:
        user_service = get_user_service()
        user = await user_service.get_user_by_email(request.email)
        
        return {
            "exists": user is not None,
            "email": request.email
        }
    except Exception as e:
        print(f"Error checking email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/send-otp", response_model=AuthResponse)
async def send_otp(request: OTPRequest):
    """Send OTP to email address"""
    try:
        auth_service = get_auth_service()
        success = await auth_service.send_otp(request.email)
        
        if success:
            return AuthResponse(
                success=True,
                message=f"OTP sent to {request.email}. Please check your email."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send OTP"
            )
    except Exception as e:
        print(f"Error sending OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/verify-otp", response_model=AuthResponse)
async def verify_otp(request: OTPVerify):
    """Verify OTP and return authentication token"""
    try:
        auth_service = get_auth_service()
        result = await auth_service.verify_otp(request.email, request.otp)
        
        if result:
            return AuthResponse(
                success=True,
                message="Authentication successful",
                user_id=result["user_id"],
                token=result["token"],
                user=result
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired OTP"
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error verifying OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/verify-token")
async def verify_token(authorization: Optional[str] = Header(None)):
    """Verify JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    auth_service = get_auth_service()
    payload = auth_service.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return {
        "valid": True,
        "user_id": payload.get("user_id"),
        "email": payload.get("email")
    }


@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Logout user (client should delete token)"""
    # In a stateless JWT system, logout is handled client-side
    # But we can log the activity
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
        auth_service = get_auth_service()
        payload = auth_service.verify_token(token)
        
        if payload:
            user_service = auth_service.user_service
            await user_service.log_activity(
                user_id=payload["user_id"],
                activity_type="logout",
                activity_data={"email": payload["email"]}
            )
    
    return {"message": "Logged out successfully"}


@router.post("/cleanup-otps")
async def cleanup_expired_otps():
    """Cleanup expired OTP codes (maintenance endpoint)"""
    auth_service = get_auth_service()
    deleted_count = await auth_service.cleanup_expired_otps()
    return {"message": f"Cleaned up {deleted_count} expired OTPs"}
