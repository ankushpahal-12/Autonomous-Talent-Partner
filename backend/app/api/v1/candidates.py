from fastapi import APIRouter, UploadFile, File, HTTPException
from mcp_server import process_and_embed_resume
from services.db_service import (
    get_all_candidates, 
    get_candidate_by_id, 
    update_candidate_decision, 
    update_candidate_review
)
from services.storage_service import save_file_to_gridfs
from services.requirement_service import get_all_requirements
from agents.lead_agent import run_full_candidate_review
from services.n8n_trigger import trigger_n8n_selected, trigger_n8n_rejected
from services.feedback_loop import record_system_feedback
from services.activity_logger import log_activity
from app.database.mongodb import get_mongodb
import asyncio

router = APIRouter()

@router.get("")
async def list_candidates():
    """Returns all candidates from MongoDB."""
    return await get_all_candidates()

@router.get("/system-insights")
async def get_system_insights():
    """Fetches recent AI learning notes and statistics."""
    db = get_mongodb()
    if db is None:
        return []
    
    logs = []
    async for log in db["feedback_logs"].find().sort("timestamp", -1).limit(3):
        log["_id"] = str(log["_id"])
        log["timestamp"] = log["timestamp"].isoformat()
        logs.append(log)
    return logs

@router.get("/{candidate_id}")
async def fetch_candidate(candidate_id: str):
    """Fetches full candidate profile including AI reports."""
    candidate = await get_candidate_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

@router.patch("/{candidate_id}/decision")
async def update_decision(candidate_id: str, payload: dict):
    """Updates the HR decision for a candidate."""
    decision = payload.get("decision")
    reason = payload.get("reason", "")
    success = await update_candidate_decision(candidate_id, decision, reason)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update recruitment decision.")
    
    # Trigger n8n Automation (asynchronously)
    try:
        candidate = await get_candidate_by_id(candidate_id)
        if candidate:
            name = candidate.get("parsed_data", {}).get("name", "Candidate")
            email = candidate.get("parsed_data", {}).get("email", "")
            if email:
                if decision == "selected":
                    # asyncio.create_task(trigger_n8n_selected(name, email))
                    print(f"\n=========================================")
                    print(f"✅ CANDIDATE SELECTED: {name} ({email})")
                    print(f"=========================================\n")
                elif decision == "rejected":
                    # asyncio.create_task(trigger_n8n_rejected(name, email, reason))
                    print(f"\n=========================================")
                    print(f"❌ CANDIDATE REJECTED: {name} ({email})")
                    print(f"   Reason: {reason}")
                    print(f"=========================================\n")
                
                # Trigger AI Feedback Loop (Learning Step)
                asyncio.create_task(record_system_feedback(candidate_id, decision, reason))
                
                # Log Activity
                asyncio.create_task(log_activity("HR", f"Decision: {decision.upper()} for {name}", {"id": candidate_id}))
    except Exception as e:
        print(f"Non-blocking n8n trigger failure: {e}")
        
    return {"status": "success", "message": f"Candidate marked as {decision}"}

@router.post("/upload-resume")
async def upload_resume_endpoint(file: UploadFile = File(...)):
    """Handles resume upload, storage in GridFS, and triggering parsing."""
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")
        
    try:
        content = await file.read()
        gridfs_id = await save_file_to_gridfs(content, file.filename)
        
        try:
            candidate_id = file.filename.replace(".pdf", "").replace(" ", "_").lower()
            
            # Log Activity
            asyncio.create_task(log_activity("System", f"File saved to GridFS: {file.filename}", {"gridfs_id": gridfs_id}))
            asyncio.create_task(log_activity("AI", f"Started parsing resume for {candidate_id}"))
            
            # In-memory processing via GridFS ID
            result_json_str = await process_and_embed_resume(candidate_id, gridfs_id)
            
            asyncio.create_task(log_activity("AI", f"Parsing & Embedding complete for {candidate_id}"))
            
            return {
                "status": "success",
                "message": "Resume uploaded and processing completed.",
                "gridfs_id": gridfs_id,
                "data": result_json_str
            }
        except Exception as e:
            raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume processing failed: {str(e)}")

@router.post("/{candidate_id}/review")
async def review_candidate(candidate_id: str):
    """Triggers the AI multi-agent evaluation pipeline."""
    try:
        candidate = await get_candidate_by_id(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
            
        parsed_data = candidate.get("parsed_data", {})
        resume_context = f"Skills: {', '.join(parsed_data.get('skills', []))}\nProjects: {' | '.join(parsed_data.get('projects', []))}"
        
        requirements = await get_all_requirements()
        req_text = "Software Engineer Role"
        req_id = None
        if requirements:
            first_req = requirements[0]
            req_text = first_req.get("extracted_text") or first_req.get("title", "Software Engineer Role")
            req_id = first_req.get("_id")

        asyncio.create_task(log_activity("AI", f"Multi-Agent review triggered for {candidate_id}"))
        report = await run_full_candidate_review(resume_context, req_text, requirement_id=req_id)
        asyncio.create_task(log_activity("AI", f"Evaluation complete for {candidate_id}"))
        
        # Build a serialisable report dict matching the new CompleteAgentReport schema
        report_dict = {
            "screener": report.screener.model_dump(),
            "tech": report.tech.model_dump(),
            "culture": report.culture.model_dump(),
            "rag_reasoning": report.rag_reasoning,
            "final_decision": report.final_decision,
            "rejection_feedback": report.rejection_feedback,
        }
        
        await update_candidate_review(candidate_id, report_dict)
        return {"status": "success", "report": report_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Review failed: {str(e)}")
