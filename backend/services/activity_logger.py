import sys
from datetime import datetime
from app.database.mongodb import get_mongodb
from typing import Optional, Any

async def log_activity(event_type: str, description: str, metadata: Optional[Any] = None):
    """
    Saves a system event to the activity_logs collection.
    
    event_type: 'AI', 'HR', 'System', 'Automation', 'Error'
    """
    db = get_mongodb()
    if db is None:
        sys.stderr.write(f"FAILED TO LOG: {description} (Database not connected)\n")
        return

    log_entry = {
        "event_type": event_type,
        "description": description,
        "timestamp": datetime.utcnow(),
        "metadata": metadata
    }
    
    try:
        await db["activity_logs"].insert_one(log_entry)
    except Exception as e:
        sys.stderr.write(f"ERROR logging activity: {e}\n")
