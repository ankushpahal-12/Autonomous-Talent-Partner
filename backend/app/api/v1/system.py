from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database.mongodb import get_mongodb
from agents.db_chat_agent import ask_database

router = APIRouter()

class ChatRequest(BaseModel):
    query: str

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint for the React frontend to interact with the database chatbot.
    """
    try:
        response = await ask_database(request.query)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_system_metrics():
    """
    Returns system-wide metrics for the Advanced Dashboard.
    """
    db = get_mongodb()
    if db is None:
        # Graceful fallback with empty metrics
        return {
            "total_candidates": 0,
            "total_jobs": 0,
            "avg_time_to_hire": 0,
            "success_rate": 0,
        }
    
    try:
        candidates_count = await db["candidates"].count_documents({})
        jobs_count = await db["jobs"].count_documents({})
        
        # Calculate average final score
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "avg_score": {"$avg": "$final_score_data.final_score"},
                    "hire_count": {
                        "$sum": {
                            "$cond": [
                                {"$eq": ["$final_score_data.decision", "hire"]},
                                1,
                                0
                            ]
                        }
                    }
                }
            }
        ]
        
        result = await db["candidates"].aggregate(pipeline).to_list(1)
        
        if result:
            avg_score = result[0].get("avg_score", 0) or 0
            hire_count = result[0].get("hire_count", 0) or 0
            success_rate = ((hire_count / candidates_count) * 100) if candidates_count > 0 else 0
        else:
            avg_score = 0
            success_rate = 0
        
        return {
            "total_candidates": candidates_count,
            "total_jobs": jobs_count,
            "avg_score": round(avg_score, 1),
            "success_rate": round(success_rate, 1),
        }
    except Exception as e:
        import sys
        sys.stderr.write(f"Failed to fetch system metrics: {e}\n")
        return {
            "total_candidates": 0,
            "total_jobs": 0,
            "avg_score": 0,
            "success_rate": 0,
        }

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
