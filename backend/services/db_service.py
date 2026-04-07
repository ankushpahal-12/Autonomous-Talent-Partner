from app.database.mongodb import get_mongodb, connect_to_mongo

async def _get_collection():
    """Helper to ensure DB connection is active and returns the candidates collection."""
    db = get_mongodb()
    if db is None:
        # DB connection hasn't been established yet (e.g. running outside FastAPI)
        connect_to_mongo()
        db = get_mongodb()
        
    if db is None:
        return None # Failed to connect, gracefully fallback
        
    return db["candidates"]

async def initial_save_candidate(candidate_id: str, gridfs_id: str) -> bool:
    """
    Step 2 from 1.txt: Save initial upload state of the candidate with GridFS ID.
    """
    collection = await _get_collection()
    if collection is None:
        return False
        
    document = {
        "_id": candidate_id,
        "gridfs_id": gridfs_id,
        "status": "uploaded",
        "parsed": False
    }
    
    try:
        # Use upsert to handle if run multiple times
        await collection.update_one(
            {"_id": candidate_id},
            {"$set": document},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Failed to save initial candidate: {e}")
        return False

async def update_candidate_parsed(candidate_id: str, parsed_data: dict) -> bool:
    """
    Step 5 from 1.txt: Update candidate record with the JSON structured data.
    """
    collection = await _get_collection()
    if collection is None:
        return False
        
    document_update = {
        "parsed_data": parsed_data,
        "status": "processed",
        "parsed": True
    }
    
    try:
        await collection.update_one(
            {"_id": candidate_id},
            {"$set": document_update}
        )
        return True
    except Exception as e:
        print(f"Failed to update parsed candidate data: {e}")
        return False

async def get_all_candidates():
    """Retrieve all candidate records from MongoDB."""
    collection = await _get_collection()
    if collection is None:
        return []
    
    candidates = []
    async for doc in collection.find({}):
        candidates.append(doc)
    return candidates

async def get_candidate_by_id(candidate_id: str):
    """Retrieve a single candidate record by ID."""
    collection = await _get_collection()
    if collection is None:
        return None
    
    return await collection.find_one({"_id": candidate_id})

async def update_candidate_decision(candidate_id: str, decision: str, reason: str = ""):
    """
    Step 11 & 15: Save final decision and triggers the next stage.
    """
    collection = await _get_collection()
    if collection is None:
        return False
    
    update_doc = {
        "final_decision": decision,
        "hr_feedback": reason,
        "status": "decided",
        "reviewed_by": "HR"
    }
    
    try:
        await collection.update_one(
            {"_id": candidate_id},
            {"$set": update_doc}
        )
        return True
    except Exception as e:
        print(f"Failed to update decision: {e}")
        return False

async def update_candidate_review(candidate_id: str, agent_reports: dict) -> bool:
    """
    Saves the complete AI multi-agent evaluation reports to MongoDB.
    Works with both the old schema (lead key) and new schema (final_decision key).
    """
    collection = await _get_collection()
    if collection is None:
        return False

    # Support both old schema (lead.overall_match_score) and new schema (final_decision.final_score)
    final_decision = agent_reports.get("final_decision", {})
    lead_fallback = agent_reports.get("lead", {})
    match_score = (
        final_decision.get("final_score")
        or lead_fallback.get("overall_match_score")
        or 0
    )

    status = "rejected" if match_score < 60 else "ai_reviewed"
    
    update_doc = {
        "agent_reports": agent_reports,
        "match_score": match_score,
        "status": status
    }
    
    try:
        await collection.update_one(
            {"_id": candidate_id},
            {"$set": update_doc}
        )
        return True
    except Exception as e:
        print(f"Failed to update candidate review: {e}")
        return False

