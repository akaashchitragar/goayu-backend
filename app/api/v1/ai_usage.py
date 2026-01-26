from fastapi import APIRouter, HTTPException, status
from app.core.database import get_database
from datetime import datetime, timedelta
from typing import Dict, Any, List
from bson import ObjectId


router = APIRouter()


@router.get("/stats", response_model=Dict[str, Any])
async def get_ai_usage_stats():
    """
    Get AI usage statistics
    """
    try:
        db = get_database()
        
        # Get all AI usage records
        all_usage = list(db.ai_usage.find().sort("created_at", -1))
        
        # Calculate time-based stats
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)
        
        # Aggregate stats
        total_requests = len(all_usage)
        total_tokens = sum(u.get("total_tokens", 0) for u in all_usage)
        total_prompt_tokens = sum(u.get("prompt_tokens", 0) for u in all_usage)
        total_completion_tokens = sum(u.get("completion_tokens", 0) for u in all_usage)
        
        successful_requests = [u for u in all_usage if u.get("success", False)]
        failed_requests = [u for u in all_usage if not u.get("success", True)]
        
        # Today's stats
        today_usage = [u for u in all_usage if u.get("created_at", datetime.min) >= today_start]
        today_requests = len(today_usage)
        today_tokens = sum(u.get("total_tokens", 0) for u in today_usage)
        
        # This week's stats
        week_usage = [u for u in all_usage if u.get("created_at", datetime.min) >= week_start]
        week_requests = len(week_usage)
        week_tokens = sum(u.get("total_tokens", 0) for u in week_usage)
        
        # This month's stats
        month_usage = [u for u in all_usage if u.get("created_at", datetime.min) >= month_start]
        month_requests = len(month_usage)
        month_tokens = sum(u.get("total_tokens", 0) for u in month_usage)
        
        # Average response time
        response_times = [u.get("response_time_ms", 0) for u in successful_requests if u.get("response_time_ms")]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Model usage breakdown
        model_usage = {}
        for u in all_usage:
            model = u.get("model", "unknown")
            if model not in model_usage:
                model_usage[model] = {
                    "requests": 0,
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "avg_response_time_ms": 0,
                    "response_times": []
                }
            model_usage[model]["requests"] += 1
            model_usage[model]["total_tokens"] += u.get("total_tokens", 0)
            model_usage[model]["prompt_tokens"] += u.get("prompt_tokens", 0)
            model_usage[model]["completion_tokens"] += u.get("completion_tokens", 0)
            if u.get("response_time_ms"):
                model_usage[model]["response_times"].append(u.get("response_time_ms"))
        
        # Calculate average response time per model
        for model in model_usage:
            times = model_usage[model].pop("response_times")
            model_usage[model]["avg_response_time_ms"] = sum(times) / len(times) if times else 0
        
        # User usage breakdown (top 10 users by requests)
        user_usage = {}
        for u in all_usage:
            user_email = u.get("user_email") or "Anonymous"
            user_name = u.get("user_name") or ""
            user_id = u.get("user_id") or "anonymous"
            
            if user_email not in user_usage:
                user_usage[user_email] = {
                    "user_id": user_id,
                    "user_name": user_name,
                    "user_email": user_email,
                    "requests": 0,
                    "total_tokens": 0,
                    "successful": 0,
                    "failed": 0
                }
            user_usage[user_email]["requests"] += 1
            user_usage[user_email]["total_tokens"] += u.get("total_tokens", 0)
            if u.get("success", False):
                user_usage[user_email]["successful"] += 1
            else:
                user_usage[user_email]["failed"] += 1
        
        # Sort by requests and get top 10
        top_users = sorted(user_usage.values(), key=lambda x: x["requests"], reverse=True)[:10]
        
        # Daily usage for the last 7 days
        daily_usage = []
        for i in range(7):
            day_start = today_start - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            day_data = [u for u in all_usage if day_start <= u.get("created_at", datetime.min) < day_end]
            daily_usage.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "requests": len(day_data),
                "tokens": sum(u.get("total_tokens", 0) for u in day_data)
            })
        daily_usage.reverse()
        
        # Estimated cost (approximate pricing for Gemini)
        # Gemini 3 Pro: ~$0.00025 per 1K input tokens, ~$0.0005 per 1K output tokens
        estimated_cost = (total_prompt_tokens / 1000 * 0.00025) + (total_completion_tokens / 1000 * 0.0005)
        
        return {
            "summary": {
                "total_requests": total_requests,
                "successful_requests": len(successful_requests),
                "failed_requests": len(failed_requests),
                "success_rate": (len(successful_requests) / total_requests * 100) if total_requests > 0 else 100,
                "total_tokens": total_tokens,
                "total_prompt_tokens": total_prompt_tokens,
                "total_completion_tokens": total_completion_tokens,
                "avg_response_time_ms": round(avg_response_time, 2),
                "estimated_cost_usd": round(estimated_cost, 4),
                "unique_users": len(user_usage)
            },
            "time_based": {
                "today": {"requests": today_requests, "tokens": today_tokens},
                "this_week": {"requests": week_requests, "tokens": week_tokens},
                "this_month": {"requests": month_requests, "tokens": month_tokens}
            },
            "model_usage": model_usage,
            "top_users": top_users,
            "daily_usage": daily_usage
        }
        
    except Exception as e:
        print(f"Error fetching AI usage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching AI usage stats: {str(e)}"
        )


@router.get("/recent", response_model=List[Dict[str, Any]])
async def get_recent_ai_usage(limit: int = 50):
    """
    Get recent AI usage logs with user info
    """
    try:
        db = get_database()
        
        usage_logs = list(
            db.ai_usage.find()
            .sort("created_at", -1)
            .limit(limit)
        )
        
        # Convert ObjectId to string and format data
        for log in usage_logs:
            log["_id"] = str(log["_id"])
            if log.get("created_at"):
                log["created_at"] = log["created_at"].isoformat()
        
        return usage_logs
        
    except Exception as e:
        print(f"Error fetching recent AI usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching recent AI usage: {str(e)}"
        )
