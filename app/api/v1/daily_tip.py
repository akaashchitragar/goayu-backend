from fastapi import APIRouter, HTTPException, Query
from app.services.ai_service import AIService
from app.core.database import get_database
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter()
ai_service = AIService()


@router.get("/daily-tip")
async def get_daily_tip(
    dosha: Optional[str] = Query(None, description="User's dominant dosha for personalization"),
    force_refresh: bool = Query(False, description="Force generate a new tip, bypassing cache")
):
    """
    Get the AI-generated daily Ayurvedic wellness tip.
    Tips are cached for the day to avoid excessive API calls.
    Use force_refresh=true to get a new tip.
    """
    try:
        db = get_database()
        today = datetime.utcnow().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        # Check if we have a cached tip for today (skip if force_refresh is true)
        cache_key = f"daily_tip_{dosha}" if dosha else "daily_tip_general"
        
        if db is not None and not force_refresh:
            cached_tip = db.daily_tips_cache.find_one({
                "cache_key": cache_key,
                "date": {"$gte": today_start}
            })
            
            if cached_tip:
                # Return cached tip
                return {
                    "success": True,
                    "tip": {
                        "category": cached_tip.get("category"),
                        "title": cached_tip.get("title"),
                        "tip": cached_tip.get("tip"),
                        "benefit": cached_tip.get("benefit"),
                        "sanskrit_term": cached_tip.get("sanskrit_term"),
                        "best_time": cached_tip.get("best_time"),
                    },
                    "cached": True
                }
        
        # Generate new tip using AI
        tip_data = await ai_service.generate_daily_tip(user_dosha=dosha)
        
        # Cache the tip for today
        if db is not None:
            db.daily_tips_cache.update_one(
                {"cache_key": cache_key, "date": {"$gte": today_start}},
                {
                    "$set": {
                        "cache_key": cache_key,
                        "date": datetime.utcnow(),
                        **tip_data
                    }
                },
                upsert=True
            )
        
        return {
            "success": True,
            "tip": {
                "category": tip_data.get("category"),
                "title": tip_data.get("title"),
                "tip": tip_data.get("tip"),
                "benefit": tip_data.get("benefit"),
                "sanskrit_term": tip_data.get("sanskrit_term"),
                "best_time": tip_data.get("best_time"),
            },
            "cached": False
        }
        
    except Exception as e:
        print(f"Error getting daily tip: {e}")
        # Return a fallback tip on error
        return {
            "success": True,
            "tip": {
                "category": "Morning Routine",
                "title": "Start Fresh",
                "tip": "Begin your day with a glass of warm water and gentle stretching. This simple practice awakens your digestive system and prepares your body for the day ahead.",
                "benefit": "Stimulates Agni (digestive fire) and promotes natural detoxification.",
                "sanskrit_term": "Dinacharya",
                "best_time": "Upon waking",
            },
            "cached": False,
            "fallback": True
        }
