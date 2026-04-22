"""
Jobs List and Management Endpoints
- GET all jobs for HR to manage
- DELETE jobs
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pymongo.errors import PyMongoError

from app.database.mongodb import get_mongodb
from app.schemas import JobResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=List[JobResponse])
async def list_all_jobs(
    status: Optional[str] = Query(None, description="Filter by status: draft, reviewing, finalized, published"),
    skip: int = Query(0, ge=0, description="Number of jobs to skip"),
    limit: int = Query(50, ge=1, le=500, description="Number of jobs to return"),
    sort_by: str = Query("created_at", description="Sort by: created_at, title, status")
):
    """
    Get all jobs with optional filtering and pagination.
    HR can see all jobs created, with option to filter by status.
    """
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
            return []
        
        # Convert MongoDB documents to JobResponse
        result = []
        for job in jobs:
            job.pop("_id", None)  # Remove MongoDB _id field
            result.append(JobResponse(**job))
        
        return result
        
    except PyMongoError as e:
        logger.error(f"Database error fetching jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch jobs from database")
    except Exception as e:
        logger.error(f"Error fetching jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch jobs")


@router.get("/count", response_model=dict)
async def count_jobs(status: Optional[str] = Query(None)):
    """
    Get count of jobs, optionally filtered by status.
    Useful for HR dashboard/analytics.
    """
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
async def delete_job(job_id: str):
    """
    Delete a job permanently.
    HR can delete jobs that are no longer needed.
    
    Restrictions:
    - Cannot delete published jobs (must archive instead)
    """
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
    except PyMongoError as e:
        logger.error(f"Database error deleting job: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete job from database")
    except Exception as e:
        logger.error(f"Error deleting job: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete job")


@router.post("/{job_id}/archive")
async def archive_job(job_id: str):
    """
    Archive a job instead of deleting it.
    Allows HR to keep published jobs but mark them as archived.
    """
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
                    "archived_at": __import__("datetime").datetime.utcnow()
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
