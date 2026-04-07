from fastapi import APIRouter, UploadFile, File, HTTPException
from services.requirement_service import (
    extract_text_from_pdf as req_extract_pdf,
    extract_text_from_docx as req_extract_docx,
    extract_text_from_txt as req_extract_txt,
    extract_text_from_gridfs,
    save_requirement_metadata,
    get_all_requirements,
    delete_requirement
)
from services.vector_parser import embed_job_requirement
from services.storage_service import save_file_to_gridfs
from services.match_service import find_top_candidates_for_job
from services.neo4j_service import kg_service
from app.database.mongodb import get_mongodb
from services.activity_logger import log_activity
import asyncio

router = APIRouter()

@router.get("")
async def list_requirements_endpoint():
    """List all active job requirements."""
    return await get_all_requirements()

@router.delete("/{requirement_id}")
async def remove_requirement(requirement_id: str):
    """Deletes a job requirement from the system."""
    success = await delete_requirement(requirement_id)
    if not success:
        raise HTTPException(status_code=404, detail="Requirement not found or deletion failed.")
    
    asyncio.create_task(log_activity("System", f"Requirement deleted: {requirement_id}"))
    return {"status": "success", "message": "Requirement removed successfully."}

@router.get("/{requirement_id}/matches")
async def get_matches_for_requirement(requirement_id: str):
    """
    Finds the top 5 candidates that best match a specific requirement 
    using semantic search.
    """
    db = get_mongodb()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection failed.")
        
    req = await db["job_requirements"].find_one({"_id": requirement_id})
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found.")
        
    # High-fidelity retrieval: Pull the actual stored full text from MongoDB
    job_text = req.get("extracted_text") or req.get("title", "")
    matches = await find_top_candidates_for_job(job_text, job_id=requirement_id)
    return matches

@router.post("/upload-requirement")
async def upload_requirement_endpoint(file: UploadFile = File(...)):
    """Handles upload, text extraction, and indexing of job requirements."""
    allowed_types = [
        "application/pdf", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain"
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
        
    try:
        content = await file.read()
        gridfs_id = await save_file_to_gridfs(content, file.filename)
        
        try:
            # Real World: Strictly in-memory extraction via GridFS ID
            text = await extract_text_from_gridfs(gridfs_id, file.filename)
                
            req_id = file.filename.replace(" ", "_").lower() + "_" + gridfs_id[:8]
            title = file.filename.rsplit('.', 1)[0]
            
            await save_requirement_metadata(req_id, file.filename, gridfs_id, title, text)
            embed_job_requirement(req_id, title, text)
            
            # Step 12.5: Sync to Neo4j Knowledge Graph
            # Extract skills using Gemini (re-used from match_service)
            from services.match_service import extract_skills_from_job
            extracted_skills = await extract_skills_from_job(text)
            
            # Create (Job)-[:REQUIRES]->(Skill) edges
            kg_service.sync_job_to_graph(
                job_id=req_id,
                title=title,
                required_skills=extracted_skills
            )
            
            asyncio.create_task(log_activity("System", f"Requirement indexed: {title}", {"req_id": req_id}))
            
            # Step 13: Auto-evaluate existing pool for this new role (Re-engagement)
            top_matches = await find_top_candidates_for_job(text, job_id=req_id, k=5)
            
            if top_matches:
                asyncio.create_task(log_activity("AI", f"Auto-evaluation found {len(top_matches)} potential pool matches for {title}"))
            
            db = get_mongodb()
            if db is not None:
                await db["job_requirements"].update_one(
                    {"_id": req_id},
                    {"$set": {"initial_top_matches": top_matches}}
                )
            
            return {
                "status": "success", 
                "message": "Requirement indexed and initial pool matched.", 
                "req_id": req_id,
                "matches_found": len(top_matches)
            }
        except Exception as e:
            raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Requirement upload failed: {str(e)}")
