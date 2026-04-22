import uuid
from datetime import datetime
from typing import Dict, Any, List
import json
import random
import string
import logging

from app.database.mongodb import get_mongodb
from app.schemas import JobBase, JobRequirementDetails, JobCreateRequest, JobEditRequest, JobStatusEnum, JobResponse
from app.core.websockets import send_event, send_progress, send_notification
from services.llm_service import get_llm_service

logger = logging.getLogger(__name__)

async def generate_display_id() -> str:
    """Generate a readable custom ID like JOB-2X8K"""
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"JOB-{suffix}"

async def create_job(request: JobCreateRequest, user: str = "HR", session_id: str = None) -> JobResponse:
    db = get_mongodb()
    
    if session_id:
        await send_event(session_id, "JOB_CREATION_STARTED", {"title": request.title, "source": request.source})
    
    description = request.text if request.text else ""
    requirements = {"skills": [], "experience": "", "education": ""}
    
    # If AI mode, use LLM to generate professional job description
    if request.source == "ai_generated":
        llm_service = get_llm_service()
        if session_id:
            await send_progress(session_id, "AI Job Generation", 30)
        
        logger.info(f"Generating job description via LLM for: {request.title}")
        
        try:
            generated = await llm_service.generate_job_description(request.text)
            description = generated.get("description", request.text)
            requirements["skills"] = generated.get("skills", [])
            requirements["experience"] = generated.get("experience_level", "")
            requirements["education"] = generated.get("education", "")
            
            if session_id:
                await send_progress(session_id, "AI Job Generation", 100)
                await send_notification(session_id, "success", "✓ AI generated professional job description!")
        except Exception as e:
            logger.warning(f"LLM generation failed, using raw text: {e}")
            if session_id:
                await send_notification(session_id, "warning", "Using raw description (LLM unavailable)")
    
    job_id = str(uuid.uuid4())
    display_id = await generate_display_id()
    
    job_data = {
        "_id": job_id,
        "job_id": job_id,
        "display_id": display_id,
        "title": request.title,
        "description": description,
        "requirements": requirements,
        "source": request.source,
        "created_by": user,
        "created_at": datetime.utcnow(),
        "version": 1,
        "suggestions": [],
        "status": JobStatusEnum.DRAFT.value,
        "embeddings_generated": False
    }
    
    await db["jobs"].insert_one(job_data)
    
    if session_id:
        await send_event(session_id, "JOB_CREATED", {"job_id": job_id, "display_id": display_id})
        await send_notification(session_id, "success", f"✓ Job '{request.title}' created successfully!")
    
    # Remove _id before returning Pydantic model
    job_data.pop("_id", None)
    return JobResponse(**job_data)

async def get_job(job_id: str) -> JobResponse:
    db = get_mongodb()
    job_data = await db["jobs"].find_one({"_id": job_id})
    if not job_data:
        return None
    
    job_data.pop("_id", None)
    return JobResponse(**job_data)

async def edit_job(job_id: str, edit_request: JobEditRequest) -> JobResponse:
    db = get_mongodb()
    job_data = await db["jobs"].find_one({"_id": job_id})
    
    if not job_data:
        raise ValueError("Job not found")
        
    if job_data["status"] == JobStatusEnum.FINALIZED.value:
        raise ValueError("Cannot edit a finalized job")
        
    update_data = {}
    if edit_request.title is not None:
        update_data["title"] = edit_request.title
    if edit_request.description is not None:
        update_data["description"] = edit_request.description
    if edit_request.requirements is not None:
        update_data["requirements"] = edit_request.requirements.model_dump()
        
    if update_data:
        update_data["version"] = job_data.get("version", 1) + 1
        update_data["status"] = JobStatusEnum.REVIEWING.value
        
        await db["jobs"].update_one(
            {"_id": job_id},
            {"$set": update_data}
        )
        
    return await get_job(job_id)

async def get_ai_suggestions(job_id: str, session_id: str = None) -> List[Dict[str, Any]]:
    """
    Generate real AI suggestions using LLM analysis of the job description
    """
    db = get_mongodb()
    job_data = await db["jobs"].find_one({"_id": job_id})
    
    if not job_data:
        raise ValueError("Job not found")
    
    if session_id:
        await send_event(session_id, "SUGGESTIONS_GENERATION_STARTED", {"job_id": job_id})
        await send_progress(session_id, "AI Suggestions", 20)
    
    try:
        # Use LLM to generate real suggestions
        llm_service = get_llm_service()
        suggestions_list = await llm_service.generate_job_suggestions(
            job_data.get("title", ""),
            job_data.get("description", "")
        )
        
        if session_id:
            await send_progress(session_id, "AI Suggestions", 70)
        
        # Convert to database format
        suggestions = []
        for idx, sugg in enumerate(suggestions_list):
            suggestion = {
                "id": str(uuid.uuid4()),
                "suggested_text": sugg.get("suggested_text", ""),
                "reason": sugg.get("reason", ""),
                "status": "pending",
                "category": sugg.get("category", "general")
            }
            suggestions.append(suggestion)
        
        # Save suggestions to database
        if suggestions:
            await db["jobs"].update_one(
                {"_id": job_id},
                {"$push": {"suggestions": {"$each": suggestions}}}
            )
        
        if session_id:
            await send_event(session_id, "SUGGESTIONS_GENERATED", {"job_id": job_id, "count": len(suggestions)})
            await send_notification(session_id, "success", f"✓ AI generated {len(suggestions)} suggestions!")
            await send_progress(session_id, "AI Suggestions", 100)
        
        logger.info(f"Generated {len(suggestions)} AI suggestions for job {job_id}")
        return suggestions
    
    except Exception as e:
        logger.error(f"Error generating AI suggestions: {e}")
        if session_id:
            await send_notification(session_id, "error", f"Failed to generate suggestions: {str(e)}")
        return []

async def apply_suggestion(job_id: str, suggestion_id: str, session_id: str = None) -> JobResponse:
    """
    Apply a suggestion by intelligently merging it into the job description
    """
    db = get_mongodb()
    
    # Get job and suggestion
    job_data = await db["jobs"].find_one({"_id": job_id})
    if not job_data:
        raise ValueError("Job not found")
    
    # Find the suggestion
    suggestion = None
    for sugg in job_data.get("suggestions", []):
        if sugg["id"] == suggestion_id:
            suggestion = sugg
            break
    
    if not suggestion:
        raise ValueError("Suggestion not found")
    
    if session_id:
        await send_event(session_id, "SUGGESTION_APPLY_STARTED", {"job_id": job_id, "suggestion_id": suggestion_id})
    
    try:
        # Use LLM to intelligently merge suggestion into description
        llm_service = get_llm_service()
        merged_description = await llm_service.merge_suggestion_into_description(
            job_data.get("description", ""),
            suggestion.get("suggested_text", ""),
            job_data.get("title", "")
        )
        
        # Update job with merged description and mark suggestion as applied
        await db["jobs"].update_one(
            {"_id": job_id},
            {
                "$set": {
                    "description": merged_description,
                    "status": JobStatusEnum.REVIEWING.value
                },
                "$inc": {"version": 1}
            }
        )
        
        # Mark suggestion as applied
        await db["jobs"].update_one(
            {"_id": job_id, "suggestions.id": suggestion_id},
            {"$set": {"suggestions.$.status": "applied"}}
        )
        
        if session_id:
            await send_event(session_id, "SUGGESTION_APPLIED", {"job_id": job_id, "suggestion_id": suggestion_id})
            await send_notification(session_id, "success", "✓ Suggestion integrated into job description!")
        
        logger.info(f"Successfully applied suggestion {suggestion_id} to job {job_id}")
        
    except Exception as e:
        logger.error(f"Error applying suggestion: {e}")
        if session_id:
            await send_notification(session_id, "error", f"Failed to apply suggestion: {str(e)}")
        raise
    
    return await get_job(job_id)

async def finalize_job(job_id: str, session_id: str = None) -> JobResponse:
    db = get_mongodb()
    
    if session_id:
        await send_event(session_id, "JOB_FINALIZATION_STARTED", {"job_id": job_id})
    
    await db["jobs"].update_one(
        {"_id": job_id},
        {"$set": {"status": JobStatusEnum.FINALIZED.value}}
    )
    
    if session_id:
        await send_notification(session_id, "success", "✓ Job finalized and locked!")
    
    return await get_job(job_id)

async def publish_job(job_id: str, session_id: str = None) -> JobResponse:
    """
    Publish a finalized job to make it active for candidate matching.
    """
    db = get_mongodb()
    
    job_data = await db["jobs"].find_one({"_id": job_id})
    if not job_data:
        raise ValueError("Job not found")
    
    if job_data["status"] != JobStatusEnum.FINALIZED.value:
        raise ValueError(f"Cannot publish job with status '{job_data['status']}'. Job must be finalized first.")
    
    if session_id:
        await send_event(session_id, "JOB_PUBLICATION_STARTED", {"job_id": job_id})
    
    await db["jobs"].update_one(
        {"_id": job_id},
        {
            "$set": {
                "status": JobStatusEnum.PUBLISHED.value,
                "published_at": datetime.utcnow(),
                "is_active": True
            }
        }
    )
    
    if session_id:
        await send_event(session_id, "JOB_PUBLISHED", {"job_id": job_id})
        await send_notification(session_id, "success", "✓ Job published successfully! Now active for hiring.")
    
    logger.info(f"Job {job_id} published successfully")
    return await get_job(job_id)

async def generate_job_embeddings(job_id: str, job_response: JobResponse | Dict[str, Any], session_id: str = None) -> bool:
    """
    Generate vector embeddings for a job description using the vector search service.
    This enables semantic search for matching candidates to jobs.
    
    Args:
        job_id: The ID of the job
        job_response: The job data (can be JobResponse or dict)
        session_id: Optional WebSocket session ID for real-time updates
        
    Returns:
        True if embeddings were generated successfully
    """
    try:
        from services.vector_parser import embed_job_requirement
        
        if session_id:
            await send_event(session_id, "EMBEDDING_GENERATION_STARTED", {"job_id": job_id})
            await send_progress(session_id, "Vector Embeddings", 20)
        
        # Extract data from response
        if isinstance(job_response, JobResponse):
            title = job_response.title
            job_id_field = job_response.job_id
            description = job_response.description
        else:
            title = job_response.get("title", "")
            job_id_field = job_response.get("job_id", job_id)
            description = job_response.get("description", "")
        
        # Combine description with requirements for richer embedding
        full_text = f"Job Title: {title}\n\n{description}"
        
        if isinstance(job_response, dict) and "requirements" in job_response:
            reqs = job_response["requirements"]
            if reqs.get("skills"):
                full_text += f"\n\nRequired Skills: {', '.join(reqs['skills'])}"
            if reqs.get("experience"):
                full_text += f"\n\nExperience: {reqs['experience']}"
            if reqs.get("education"):
                full_text += f"\n\nEducation: {reqs['education']}"
        
        if session_id:
            await send_progress(session_id, "Vector Embeddings", 50)
        
        # Generate embeddings
        success = embed_job_requirement(job_id_field, title, full_text)
        
        if success:
            if session_id:
                await send_progress(session_id, "Vector Embeddings", 75)
            
            # Update job record to mark embeddings as generated
            db = get_mongodb()
            await db["jobs"].update_one(
                {"_id": job_id},
                {"$set": {"embeddings_generated": True, "embeddings_generated_at": datetime.utcnow()}}
            )
            
            if session_id:
                await send_event(session_id, "EMBEDDINGS_GENERATED", {"job_id": job_id})
                await send_notification(session_id, "success", "✓ Vector embeddings generated successfully!")
                await send_progress(session_id, "Vector Embeddings", 100)
            
            logger.info(f"Successfully generated embeddings for job {job_id}")
        
        return success
    except Exception as e:
        if session_id:
            await send_notification(session_id, "error", f"✗ Embedding generation failed: {str(e)}")
            await send_event(session_id, "EMBEDDING_ERROR", {"job_id": job_id, "error": str(e)})
        
        logger.error(f"Error generating embeddings for job {job_id}: {str(e)}")
        raise

def format_job(job_response: JobResponse, format_type: str = "json") -> Any:
    """Multi-format output support (Plain Text, JSON, HTML)"""
    if format_type == "json":
        return job_response.model_dump()
        
    elif format_type == "text":
        text = f"Job Title: {job_response.title}\n"
        text += f"ID: {job_response.display_id}\n\n"
        text += f"Description:\n{job_response.description}\n\n"
        text += "Requirements:\n"
        text += f"  Skills: {', '.join(job_response.requirements.skills) if job_response.requirements.skills else 'N/A'}\n"
        text += f"  Experience: {job_response.requirements.experience if job_response.requirements.experience else 'N/A'}\n"
        return text
        
    elif format_type == "html":
        html = f"<div><h1>{job_response.title}</h1>"
        html += f"<p><strong>ID:</strong> {job_response.display_id}</p>"
        html += f"<h3>Description</h3><p>{job_response.description}</p>"
        html += "<h3>Requirements</h3><ul>"
        html += f"<li><strong>Skills:</strong> {', '.join(job_response.requirements.skills) if job_response.requirements.skills else 'N/A'}</li>"
        html += f"<li><strong>Experience:</strong> {job_response.requirements.experience if job_response.requirements.experience else 'N/A'}</li>"
        html += "</ul></div>"
        return html
        
    return job_response.model_dump()
