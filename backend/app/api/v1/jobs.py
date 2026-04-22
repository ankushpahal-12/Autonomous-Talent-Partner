import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse

from ...schemas import JobCreateRequest, JobEditRequest, JobResponse
from services.job_service import (
    create_job,
    get_job,
    edit_job,
    get_ai_suggestions,
    apply_suggestion,
    finalize_job,
    format_job,
    generate_job_embeddings
)

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("", response_model=JobResponse)
async def create_new_job(request: JobCreateRequest, session_id: str = None):
    """
    Step 1: Create a Job Request. 
    Accepts title and optional text. Backend generates UUID and custom display ID.
    Optionally accepts session_id for real-time WebSocket updates.
    """
    if not request.title:
        raise HTTPException(status_code=400, detail="job_title is highly required")
    
    try:
        return await create_job(request, session_id=session_id)
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        if session_id:
            from ...core.websockets import send_notification
            await send_notification(session_id, "error", f"Failed to create job: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create job")

@router.get("/{job_id}")
async def retrieve_job(job_id: str, format: Optional[str] = Query("json", description="json, text, or html")):
    """
    Retrieve job by ID. Supports multi-format output.
    """
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    formatted_content = format_job(job, format)
    if format == "html":
        return HTMLResponse(content=formatted_content)
    elif format == "text":
        return PlainTextResponse(content=formatted_content)
        
    return JSONResponse(content=formatted_content)

@router.put("/edit/{job_id}", response_model=JobResponse)
async def edit_job_endpoint(job_id: str, request: JobEditRequest):
    """
    HR edits the JD. Updates description/requirements and increments version history.
    Cannot edit if finalized.
    """
    try:
        return await edit_job(job_id, request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to edit job")

@router.post("/suggestions/{job_id}")
async def job_suggestions(job_id: str, session_id: str = None):
    """
    Triggers AI engine to return suggestions for the current JD.
    Optionally accepts session_id for real-time WebSocket updates.
    """
    try:
        return await get_ai_suggestions(job_id, session_id=session_id)
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        if session_id:
            from ...core.websockets import send_notification
            await send_notification(session_id, "error", "Failed to generate suggestions")
        raise HTTPException(status_code=500, detail="Failed to generate AI suggestions")

@router.post("/apply-suggestions/{job_id}/{suggestion_id}", response_model=JobResponse)
async def apply_job_suggestion(job_id: str, suggestion_id: str, session_id: str = None):
    """
    Applies an AI suggestion to the JD.
    Optionally accepts session_id for real-time WebSocket updates.
    """
    try:
        return await apply_suggestion(job_id, suggestion_id, session_id=session_id)
    except Exception as e:
        logger.error(f"Error applying suggestion: {e}")
        if session_id:
            from ...core.websockets import send_notification
            await send_notification(session_id, "error", "Failed to apply suggestion")
        raise HTTPException(status_code=500, detail="Failed to apply suggestion")

@router.post("/finalize/{job_id}", response_model=JobResponse)
async def finalize_job_endpoint(job_id: str, session_id: str = None):
    """
    Locks the Job. It enters the 'finalized' state and cannot be edited.
    Also generates vector embeddings for semantic search.
    Optionally accepts session_id for real-time WebSocket updates.
    """
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    try:
        # Finalize the job
        finalized_job = await finalize_job(job_id, session_id=session_id)
        
        # Generate embeddings for semantic search
        try:
            await generate_job_embeddings(job_id, finalized_job, session_id=session_id)
            logger.info(f"Successfully generated embeddings for job {job_id}")
        except Exception as emb_err:
            logger.error(f"Error generating embeddings for job {job_id}: {emb_err}")
            if session_id:
                from ...core.websockets import send_notification
                await send_notification(session_id, "warning", "Job finalized but embedding generation had issues")
        
        return finalized_job
    except Exception as e:
        logger.error(f"Error finalizing job: {e}")
        if session_id:
            from ...core.websockets import send_notification
            await send_notification(session_id, "error", "Failed to finalize job")
        raise HTTPException(status_code=500, detail="Failed to finalize job")

@router.post("/publish/{job_id}", response_model=JobResponse)
async def publish_job_endpoint(job_id: str, session_id: str = None):
    """
    Publish a finalized job to make it active for candidate matching.
    Can only publish jobs that have been finalized.
    """
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        from services.job_service import publish_job
        return await publish_job(job_id, session_id=session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error publishing job: {e}")
        if session_id:
            from ...core.websockets import send_notification
            await send_notification(session_id, "error", "Failed to publish job")
        raise HTTPException(status_code=500, detail="Failed to publish job")

@router.post("/embeddings/{job_id}")
async def generate_embeddings_endpoint(job_id: str):
    """
    Manually trigger embedding generation for a job.
    Called after job finalization to create vector embeddings for semantic search.
    """
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    try:
        await generate_job_embeddings(job_id, job)
        return {
            "status": "success",
            "message": "Vector embeddings generated successfully",
            "job_id": job_id
        }
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate embeddings: {str(e)}")

@router.get("")
async def list_all_jobs(
    status: Optional[str] = Query(None, description="Filter by status: draft, reviewing, finalized, published"),
    skip: int = Query(0, ge=0, description="Number of jobs to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of jobs to return"),
    sort_by: str = Query("created_at", description="Sort by: created_at, title, status")
):
    """
    Get all jobs with optional filtering and pagination.
    HR can see all jobs created, with option to filter by status.
    
    Query Parameters:
    - status: Filter by job status (draft, reviewing, finalized, published)
    - skip: Number of jobs to skip for pagination (default 0)
    - limit: Number of jobs to return (default 50, max 500)
    - sort_by: Field to sort by (created_at, title, status)
    """
    from ...database.mongodb import get_mongodb
    
    db = get_mongodb()
    
    try:
        # Build filter
        filter_query = {}
        if status:
            filter_query["status"] = status.lower()
        
        # Build sort
        sort_order = -1 if sort_by == "created_at" else 1
        sort_field = sort_by if sort_by in ["created_at", "title", "status"] else "created_at"
        
        # Query database
        jobs = await db["jobs"].find(filter_query).sort(sort_field, sort_order).skip(skip).limit(limit).to_list(None)
        
        if not jobs:
            return {
                "total": 0,
                "skip": skip,
                "limit": limit,
                "jobs": []
            }
        
        # Convert MongoDB documents to proper format
        result_jobs = []
        for job in jobs:
            job_data = dict(job)
            job_data.pop("_id", None)  # Remove MongoDB _id field
            result_jobs.append(job_data)
        
        # Get total count for pagination info
        total = await db["jobs"].count_documents(filter_query)
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "jobs": result_jobs
        }
        
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch jobs")

@router.get("/count")
async def count_jobs(status: Optional[str] = Query(None, description="Filter by status")):
    """
    Get count of jobs, optionally filtered by status.
    Useful for HR dashboard/analytics.
    
    Returns count of all jobs or filtered by status.
    """
    from ...database.mongodb import get_mongodb
    
    db = get_mongodb()
    
    try:
        filter_query = {}
        if status:
            filter_query["status"] = status.lower()
        
        total = await db["jobs"].count_documents(filter_query)
        
        return {
            "total": total,
            "status": status or "all"
        }
    except Exception as e:
        logger.error(f"Error counting jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to count jobs")

@router.delete("/{job_id}")
async def delete_job_endpoint(job_id: str):
    """
    Delete a job permanently.
    HR can delete jobs that are no longer needed.
    
    Restrictions:
    - Cannot delete published jobs (must archive instead)
    
    Returns: Success message with job details
    """
    from ...database.mongodb import get_mongodb
    from datetime import datetime
    
    db = get_mongodb()
    
    try:
        # Get the job first
        job = await db["jobs"].find_one({"_id": job_id})
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Don't allow deleting published jobs
        if job.get("status") == "published":
            raise HTTPException(
                status_code=400,
                detail="Cannot delete published jobs. Archive the job instead if needed."
            )
        
        # Delete the job
        result = await db["jobs"].delete_one({"_id": job_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Job not found")
        
        logger.info(f"Job {job_id} deleted successfully")
        
        return {
            "status": "success",
            "message": f"Job {job.get('display_id')} deleted successfully",
            "job_id": job_id,
            "job_title": job.get("title")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete job")

@router.post("/{job_id}/archive")
async def archive_job_endpoint(job_id: str):
    """
    Archive a job instead of deleting it.
    Allows HR to keep published jobs but mark them as archived/inactive.
    
    Returns: Success message confirming archival
    """
    from ...database.mongodb import get_mongodb
    from datetime import datetime
    
    db = get_mongodb()
    
    try:
        job = await db["jobs"].find_one({"_id": job_id})
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Update job status to archived
        result = await db["jobs"].update_one(
            {"_id": job_id},
            {
                "$set": {
                    "status": "archived",
                    "is_active": False,
                    "archived_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Job not found")
        
        logger.info(f"Job {job_id} archived successfully")
        
        return {
            "status": "success",
            "message": f"Job {job.get('display_id')} archived successfully",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving job: {e}")
        raise HTTPException(status_code=500, detail="Failed to archive job")
