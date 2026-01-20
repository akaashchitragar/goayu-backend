from fastapi import APIRouter, HTTPException, Header, Request
from typing import Optional, List
from app.models.user import User, UserCreate, UserUpdate, UserResponse, UserActivity
from app.services.user_service import UserService

router = APIRouter()

def get_user_service():
    return UserService()


@router.post("/users/", response_model=UserResponse)
async def create_user(user_data: UserCreate):
    """Create a new user"""
    try:
        user_service = get_user_service()
        user = await user_service.create_user(user_data)
        return UserResponse(**user.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get user by ID"""
    user_service = get_user_service()
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user.model_dump())


@router.get("/users/clerk/{clerk_id}", response_model=UserResponse)
async def get_user_by_clerk_id(clerk_id: str):
    """Get user by Clerk ID"""
    user_service = get_user_service()
    user = await user_service.get_user_by_clerk_id(clerk_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user.model_dump())


@router.get("/users/email/{email}", response_model=UserResponse)
async def get_user_by_email(email: str):
    """Get user by email"""
    user_service = get_user_service()
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user.model_dump())


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, update_data: UserUpdate):
    """Update user information"""
    user_service = get_user_service()
    user = await user_service.update_user(user_id, update_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user.model_dump())


@router.get("/users/{user_id}/questionnaires")
async def get_user_questionnaires(user_id: str):
    """Get all questionnaires for a user"""
    from app.core.database import get_database
    from bson import ObjectId
    
    user_service = get_user_service()
    questionnaire_ids = await user_service.get_user_questionnaires(user_id)
    
    # Fetch full questionnaire data
    db = get_database()
    questionnaires_collection = db["questionnaires"]
    questionnaires = []
    
    for qid in questionnaire_ids:
        try:
            # Try to find by ObjectId first
            questionnaire = questionnaires_collection.find_one({"_id": ObjectId(qid)})
            if questionnaire:
                # Convert ObjectId to string for JSON serialization
                questionnaire["_id"] = str(questionnaire["_id"])
                questionnaires.append(questionnaire)
        except Exception as e:
            print(f"Error fetching questionnaire {qid}: {e}")
            continue
    
    return questionnaires


@router.get("/users/{user_id}/consultations")
async def get_user_consultations(user_id: str):
    """Get all consultations for a user"""
    from app.core.database import get_database
    from bson import ObjectId
    
    user_service = get_user_service()
    consultation_ids = await user_service.get_user_consultations(user_id)
    
    # Fetch full consultation data
    db = get_database()
    consultations_collection = db["consultations"]
    consultations = []
    
    for cid in consultation_ids:
        try:
            # Try to find by ObjectId first
            consultation = consultations_collection.find_one({"_id": ObjectId(cid)})
            if consultation:
                # Convert ObjectId to string for JSON serialization
                consultation["_id"] = str(consultation["_id"])
                consultations.append(consultation)
        except Exception as e:
            print(f"Error fetching consultation {cid}: {e}")
            continue
    
    return consultations


@router.get("/users/{user_id}/activities")
async def get_user_activities(
    user_id: str,
    limit: int = 50,
    activity_type: Optional[str] = None
):
    """Get user activity log"""
    user_service = get_user_service()
    activities = await user_service.get_user_activities(user_id, limit, activity_type)
    return {"user_id": user_id, "activities": [activity.model_dump() for activity in activities]}


@router.post("/users/{user_id}/sessions")
async def create_session(
    user_id: str,
    clerk_session_id: str,
    request: Request
):
    """Create a new session for user"""
    user_service = get_user_service()
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    session = await user_service.create_session(
        user_id=user_id,
        clerk_session_id=clerk_session_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return {"session_id": session.session_id, "expires_at": session.expires_at}


@router.get("/users/{user_id}/sessions")
async def get_active_sessions(user_id: str):
    """Get all active sessions for a user"""
    user_service = get_user_service()
    sessions = await user_service.get_active_sessions(user_id)
    return {"user_id": user_id, "sessions": [session.model_dump() for session in sessions]}


@router.delete("/sessions/{session_id}")
async def invalidate_session(session_id: str):
    """Invalidate a session (logout)"""
    user_service = get_user_service()
    success = await user_service.invalidate_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session invalidated successfully"}


@router.delete("/users/{user_id}/sessions")
async def invalidate_all_sessions(user_id: str):
    """Invalidate all sessions for a user (logout from all devices)"""
    user_service = get_user_service()
    await user_service.invalidate_all_user_sessions(user_id)
    return {"message": "All sessions invalidated successfully"}


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(user_id: str):
    """Deactivate a user account"""
    user_service = get_user_service()
    await user_service.deactivate_user(user_id)
    return {"message": "User deactivated successfully"}


@router.post("/users/{user_id}/reactivate")
async def reactivate_user(user_id: str):
    """Reactivate a user account"""
    user_service = get_user_service()
    await user_service.reactivate_user(user_id)
    return {"message": "User reactivated successfully"}


@router.get("/users/")
async def get_all_users(skip: int = 0, limit: int = 100):
    """Get all users (admin endpoint)"""
    user_service = get_user_service()
    users = await user_service.get_all_users(skip, limit)
    total = await user_service.get_user_count()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "users": [UserResponse(**user.model_dump()).model_dump() for user in users]
    }


@router.post("/sessions/cleanup")
async def cleanup_expired_sessions():
    """Cleanup expired sessions (maintenance endpoint)"""
    user_service = get_user_service()
    deleted_count = await user_service.cleanup_expired_sessions()
    return {"message": f"Cleaned up {deleted_count} expired sessions"}
