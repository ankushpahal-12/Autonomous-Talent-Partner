from fastapi import APIRouter, HTTPException
from app.database.mongodb import get_mongodb

router = APIRouter()

@router.get("/activity")
async def get_system_activity():
    """
    Returns the latest 50 system activities from MongoDB.
    """
    db = get_mongodb()
    if db is None:
        # Graceful fallback: Instead of a 500 error, return empty list
        return []
    
    try:
        activities = []
        async for log in db["activity_logs"].find().sort("timestamp", -1).limit(50):
            log["_id"] = str(log["_id"])
            log["timestamp"] = log["timestamp"].isoformat()
            activities.append(log)
        return activities
    except Exception as e:
        import sys
        sys.stderr.write(f"Database query failed (likely connection timeout): {e}\n")
        return []
