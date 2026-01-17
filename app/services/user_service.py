from datetime import datetime, timedelta
from typing import Optional, List
from app.core.database import get_database
from app.models.user import User, UserCreate, UserUpdate, Session, UserActivity


class UserService:
    """Service for managing users and sessions"""
    
    def __init__(self):
        self.db = get_database()
        self.users_collection = self.db["users"]
        self.sessions_collection = self.db["sessions"]
        self.activities_collection = self.db["user_activities"]
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        # User indexes
        self.users_collection.create_index("user_id", unique=True)
        self.users_collection.create_index("email", unique=True)
        
        # Session indexes
        self.sessions_collection.create_index("session_id", unique=True)
        self.sessions_collection.create_index("user_id")
        self.sessions_collection.create_index("token")
        self.sessions_collection.create_index("expires_at")
        
        # Activity indexes
        self.activities_collection.create_index("activity_id", unique=True)
        self.activities_collection.create_index("user_id")
        self.activities_collection.create_index("timestamp")
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = self.users_collection.find_one({"email": user_data.email})
        if existing_user:
            return User(**existing_user)
        
        # Create new user
        user = User(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            profile_image=user_data.profile_image,
            blood_group=user_data.blood_group,
            height=user_data.height,
            weight=user_data.weight,
        )
        
        self.users_collection.insert_one(user.model_dump())
        
        # Log activity
        await self.log_activity(
            user_id=user.user_id,
            activity_type="user_created",
            activity_data={"email": user.email}
        )
        
        return user
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by user_id"""
        user_data = self.users_collection.find_one({"user_id": user_id})
        if user_data:
            return User(**user_data)
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        user_data = self.users_collection.find_one({"email": email})
        if user_data:
            return User(**user_data)
        return None
    
    async def update_user(self, user_id: str, update_data: UserUpdate) -> Optional[User]:
        """Update user information"""
        update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
        update_dict["updated_at"] = datetime.utcnow()
        
        result = self.users_collection.update_one(
            {"user_id": user_id},
            {"$set": update_dict}
        )
        
        if result.modified_count > 0:
            return await self.get_user_by_id(user_id)
        return None
    
    async def update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        self.users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"last_login": datetime.utcnow()}}
        )
    
    async def add_questionnaire_to_user(self, user_id: str, questionnaire_id: str):
        """Add questionnaire ID to user's record"""
        self.users_collection.update_one(
            {"user_id": user_id},
            {"$addToSet": {"questionnaire_ids": questionnaire_id}}
        )
    
    async def add_consultation_to_user(self, user_id: str, consultation_id: str):
        """Add consultation ID to user's record"""
        self.users_collection.update_one(
            {"user_id": user_id},
            {"$addToSet": {"consultation_ids": consultation_id}}
        )
    
    async def get_user_questionnaires(self, user_id: str) -> List[str]:
        """Get all questionnaire IDs for a user"""
        user = await self.get_user_by_id(user_id)
        return user.questionnaire_ids if user else []
    
    async def get_user_consultations(self, user_id: str) -> List[str]:
        """Get all consultation IDs for a user"""
        user = await self.get_user_by_id(user_id)
        return user.consultation_ids if user else []
    
    async def create_session(
        self, 
        user_id: str, 
        token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_in_days: int = 30
    ) -> Session:
        """Create a new session"""
        session = Session(
            user_id=user_id,
            token=token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
        )
        
        self.sessions_collection.insert_one(session.model_dump())
        
        # Update last login
        await self.update_last_login(user_id)
        
        # Log activity
        await self.log_activity(
            user_id=user_id,
            activity_type="login",
            activity_data={"session_id": session.session_id},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        session_data = self.sessions_collection.find_one({"session_id": session_id})
        if session_data:
            return Session(**session_data)
        return None
    
    async def get_active_sessions(self, user_id: str) -> List[Session]:
        """Get all active sessions for a user"""
        sessions = self.sessions_collection.find({
            "user_id": user_id,
            "is_active": True,
            "expires_at": {"$gt": datetime.utcnow()}
        })
        return [Session(**session) for session in sessions]
    
    async def update_session_activity(self, session_id: str):
        """Update session's last activity timestamp"""
        self.sessions_collection.update_one(
            {"session_id": session_id},
            {"$set": {"last_activity": datetime.utcnow()}}
        )
    
    async def invalidate_session(self, session_id: str):
        """Invalidate a session"""
        result = self.sessions_collection.update_one(
            {"session_id": session_id},
            {"$set": {"is_active": False}}
        )
        return result.modified_count > 0
    
    async def invalidate_all_user_sessions(self, user_id: str):
        """Invalidate all sessions for a user"""
        self.sessions_collection.update_many(
            {"user_id": user_id},
            {"$set": {"is_active": False}}
        )
    
    async def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        result = self.sessions_collection.delete_many({
            "expires_at": {"$lt": datetime.utcnow()}
        })
        return result.deleted_count
    
    async def log_activity(
        self,
        user_id: str,
        activity_type: str,
        activity_data: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log user activity"""
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            activity_data=activity_data or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.activities_collection.insert_one(activity.model_dump())
    
    async def get_user_activities(
        self, 
        user_id: str, 
        limit: int = 50,
        activity_type: Optional[str] = None
    ) -> List[UserActivity]:
        """Get user activities"""
        query = {"user_id": user_id}
        if activity_type:
            query["activity_type"] = activity_type
        
        activities = self.activities_collection.find(query).sort("timestamp", -1).limit(limit)
        return [UserActivity(**activity) for activity in activities]
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        users = self.users_collection.find().skip(skip).limit(limit)
        return [User(**user) for user in users]
    
    async def get_user_count(self) -> int:
        """Get total number of users"""
        return self.users_collection.count_documents({})
    
    async def deactivate_user(self, user_id: str):
        """Deactivate a user account"""
        self.users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        
        # Invalidate all sessions
        await self.invalidate_all_user_sessions(user_id)
        
        # Log activity
        await self.log_activity(
            user_id=user_id,
            activity_type="user_deactivated"
        )
    
    async def reactivate_user(self, user_id: str):
        """Reactivate a user account"""
        self.users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"is_active": True, "updated_at": datetime.utcnow()}}
        )
        
        # Log activity
        await self.log_activity(
            user_id=user_id,
            activity_type="user_reactivated"
        )
