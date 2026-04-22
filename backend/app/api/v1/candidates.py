"""
Candidates API endpoints with improved error handling, validation, and pagination.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Request
from pydantic import BaseModel, Field, validator
import logging
import asyncio
import json
from typing import Optional, List

from mcp_server import process_and_embed_resume
from app.core.websockets import send_event, send_progress, send_notification
from services.db_service import (
    get_all_candidates, 
    get_candidate_by_id, 
    update_candidate_decision, 
    update_candidate_review,
    delete_candidate,
    update_external_intel,
    save_comprehensive_scoring_data,
    save_final_score_with_metadata,
    save_neo4j_analysis_results,
    save_risk_assessment_results,
    archive_previous_score,
    get_complete_evaluation
)
from services.storage_service import save_file_to_gridfs
from services.requirement_service import get_all_requirements
from agents.lead_agent import run_full_candidate_review
from agents.scraper_agent import run_scraper_agent
from services.n8n_trigger import trigger_n8n_selected, trigger_n8n_rejected
from services.feedback_loop import record_system_feedback
from services.activity_logger import log_activity
from services.decision_service import (
    run_enhanced_decision_chain,
    run_comprehensive_analysis
)
from app.database.connection_manager import db_manager
from app.schemas import CandidateDecisionRequest, ResumeUploadResponse, PaginationParams
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# ============================================================================
# Request Validation Models
# ============================================================================

class EnrichCandidateRequest(BaseModel):
    """Request to trigger candidate enrichment."""
    candidate_id: str = Field(..., description="Candidate ID to enrich")

class InterviewScheduleRequest(BaseModel):
    """Request to schedule interview for accepted candidate."""
    interview_date: str = Field(..., description="Interview date (YYYY-MM-DD)")
    interview_time: str = Field(..., description="Interview time (HH:MM)")
    interview_duration: int = Field(default=60, description="Duration in minutes")
    timezone: str = Field(default="EST", description="Candidate's timezone")
    meeting_link: str = Field(..., description="Video conference link")
    interviewer_name: str = Field(..., description="Name of interviewer/hiring manager")
    hr_email: str = Field(..., description="HR team email for notification")

class CandidateRejectionRequest(BaseModel):
    """Request to record candidate rejection."""
    rejection_reason: str = Field(..., description="Brief reason for rejection")
    feedback_summary: str = Field(..., description="Detailed feedback")
    hr_email: str = Field(..., description="HR team email for notification")
    allow_reapply: bool = Field(default=True, description="Can candidate reapply")
    reapply_after_months: int = Field(default=6, description="Months before reapply eligible")

# ============================================================================
# Endpoints
# ============================================================================

@router.get("")
async def list_candidates(
    request: Request,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
):
    """
    Returns paginated list of candidates from MongoDB.
    Supports sorting and pagination for better performance.
    Flattens the response to include parsed_data fields at the top level.
    """
    try:
        request_id = getattr(request.state, "request_id", "unknown")
        
        candidates = await get_all_candidates()
        if not candidates:
            return {
                "status": "success",
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
        
        # Flatten candidate data for frontend
        flattened_candidates = []
        for candidate in candidates:
            parsed_data = candidate.get("parsed_data", {})
            agent_reports = candidate.get("agent_reports", {})
            final_decision = agent_reports.get("final_decision", {})
            ai_report = candidate.get("ai_report", {})
            
            # Extract score breakdown from ai_report or agent_reports
            tech_report = ai_report.get("tech", {}) or agent_reports.get("tech_agent", {})
            screener_report = ai_report.get("screener", {}) or agent_reports.get("screener", {})
            culture_report = ai_report.get("culture", {}) or agent_reports.get("culture_agent", {})
            
            flattened = {
                "candidate_id": candidate.get("_id"),
                "name": parsed_data.get("name", "Unknown"),
                "email": parsed_data.get("email", ""),
                "phone": parsed_data.get("phone", ""),
                "location": parsed_data.get("location", ""),
                "experience_years": parsed_data.get("experience_years", 0),
                "skills": parsed_data.get("skills", []),
                "status": candidate.get("status", "unknown"),
                "hr_decision": candidate.get("hr_decision"),
                "match_score": candidate.get("match_score", 0),
                "aiScore": final_decision.get("final_score") or candidate.get("match_score", 0),
                "enriched": candidate.get("enriched", False),
                # Score breakdowns
                "tech_score": tech_report.get("technical_score", 0) or tech_report.get("score", 0),
                "project_score": tech_report.get("project_score", 0) or screener_report.get("score", 0),
                "aptitude_score": screener_report.get("aptitude_score", 0) or screener_report.get("score", 0),
                "growth_score": culture_report.get("culture_score", 0) or culture_report.get("score", 0),
                # Full reports for detailed analysis
                "ai_report": ai_report,
            }
            flattened_candidates.append(flattened)
        
        # Sorting
        if sort_by and sort_by in ["status", "created_at", "name", "match_score"]:
            reverse = sort_by == "created_at"
            flattened_candidates = sorted(
                flattened_candidates, 
                key=lambda x: x.get(sort_by, ""), 
                reverse=reverse
            )
        
        # Pagination
        total = len(flattened_candidates)
        skip = (page - 1) * page_size
        paginated = flattened_candidates[skip:skip + page_size]
        
        return {
            "status": "success",
            "items": paginated,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        logger.error(f"Error fetching candidates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch candidates")

@router.get("/system-insights")
async def get_system_insights(request: Request):
    """Fetches recent AI learning notes and statistics from feedback logs."""
    try:
        request_id = getattr(request.state, "request_id", "unknown")
        db = db_manager.get_db()
        
        if db is None:
            logger.warning(f"[{request_id}] Database not available for system insights")
            return {"status": "success", "insights": []}
        
        logs = []
        async for log in db["feedback_logs"].find().sort("timestamp", -1).limit(3):
            log["_id"] = str(log["_id"])
            log["timestamp"] = log["timestamp"].isoformat() if hasattr(log.get("timestamp"), "isoformat") else str(log["timestamp"])
            logs.append(log)
        
        return {"status": "success", "insights": logs}
    except Exception as e:
        logger.error(f"Error fetching system insights: {e}")
        return {"status": "success", "insights": []}

@router.get("/{candidate_id}")
async def fetch_candidate(candidate_id: str, request: Request):
    """Fetches full candidate profile including AI reports and metadata."""
    try:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] Fetching candidate: {candidate_id}")
        
        # Validate candidate ID format
        if not candidate_id or len(candidate_id) == 0:
            raise HTTPException(status_code=400, detail="Invalid candidate ID")
        
        candidate = await get_candidate_by_id(candidate_id)
        if not candidate:
            logger.warning(f"[{request_id}] Candidate not found: {candidate_id}")
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Convert ObjectId to string
        if "_id" in candidate:
            candidate["_id"] = str(candidate["_id"])
        
        return {"status": "success", "data": candidate}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching candidate {candidate_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch candidate")

@router.patch("/{candidate_id}/decision")
async def update_decision(candidate_id: str, payload: CandidateDecisionRequest, request: Request):
    """
    Updates the HR decision for a candidate and triggers downstream workflows.
    Validates decision value and properly handles async tasks.
    """
    try:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] Updating decision for {candidate_id}: {payload.decision}")
        
        # Validate inputs
        if not candidate_id or len(candidate_id) == 0:
            raise HTTPException(status_code=400, detail="Candidate ID is required")
        
        success = await update_candidate_decision(candidate_id, payload.decision.value, payload.reason)
        if not success:
            logger.error(f"[{request_id}] Failed to update decision for {candidate_id}")
            raise HTTPException(status_code=500, detail="Failed to update recruitment decision.")
        
        # Fetch candidate for notification
        candidate = await get_candidate_by_id(candidate_id)
        if candidate:
            name = candidate.get("parsed_data", {}).get("name", "Candidate")
            email = candidate.get("parsed_data", {}).get("email", "")
            
            logger.info(f"[{request_id}] {payload.decision.value.upper()}: {name} ({email})")
            
            # Trigger async workflows
            if email:
                if payload.decision.value == "selected":
                    asyncio.create_task(log_activity("HR", f"Candidate selected: {name}", {"id": candidate_id}))
                elif payload.decision.value == "rejected":
                    asyncio.create_task(log_activity("HR", f"Candidate rejected: {name}", {"id": candidate_id, "reason": payload.reason}))
            
            # Trigger feedback loop for learning
            asyncio.create_task(record_system_feedback(candidate_id, payload.decision.value, payload.reason))
        
        return {
            "status": "success",
            "message": f"Candidate marked as {payload.decision.value}",
            "request_id": request_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating decision: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update decision")

@router.post("/upload-resume")
async def upload_resume_endpoint(
    file: UploadFile = File(...), 
    request: Request = None,
    session_id: Optional[str] = Query(None, description="WebSocket session ID for real-time updates")
):
    """
    Handles resume upload, GridFS storage, and parsing pipeline with real-time WebSocket updates.
    Emits events for: CV upload started, CV uploaded, CV parsing started/done, CV embedding started/done, processing complete.
    """
    request_id = getattr(request.state, "request_id", "unknown") if request else "unknown"
    
    try:
        logger.info(f"[{request_id}] Resume upload started: {file.filename}")
        
        # Emit: CV upload started
        if session_id:
            await send_event(session_id, "CV_UPLOAD_STARTED", {
                "filename": file.filename,
                "content_type": file.content_type
            })
            await send_notification(session_id, "info", f"📤 Uploading {file.filename}...")
        
        # Validate file type
        if file.content_type != "application/pdf":
            if session_id:
                await send_notification(session_id, "error", "Only PDF resumes are supported")
            raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")
        
        # Validate file size
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            if session_id:
                await send_notification(session_id, "error", f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB")
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB"
            )
        
        # Emit: CV uploaded successfully
        if session_id:
            await send_event(session_id, "CV_UPLOADED", {
                "filename": file.filename,
                "size_mb": round(file_size_mb, 2)
            })
            await send_notification(session_id, "success", f"✓ {file.filename} uploaded ({round(file_size_mb, 2)} MB)")
        
        # Save to GridFS
        gridfs_id = await save_file_to_gridfs(content, file.filename)
        candidate_id = file.filename.replace(".pdf", "").replace(" ", "_").lower()
        
        logger.info(f"[{request_id}] File saved to GridFS: {gridfs_id}")
        
        # Emit: Parsing started
        if session_id:
            await send_event(session_id, "CV_PARSING_STARTED", {"candidate_id": candidate_id})
            await send_notification(session_id, "info", "🔄 Parsing CV content...")
            await send_progress(session_id, "cv_parsing", 10)
        
        # Log activities
        asyncio.create_task(log_activity("System", f"Resume received: {file.filename}", {"gridfs_id": gridfs_id, "size_mb": round(file_size_mb, 2)}))
        asyncio.create_task(log_activity("AI", f"Starting resume parsing for {candidate_id}"))
        
        # Update progress
        if session_id:
            await send_progress(session_id, "cv_parsing", 40)
        
        # Process and embed resume
        result_json_str = await process_and_embed_resume(candidate_id, gridfs_id)
        
        # Emit: Parsing done, embedding started
        if session_id:
            await send_progress(session_id, "cv_parsing", 100)
            await send_event(session_id, "CV_PARSING_DONE", {"candidate_id": candidate_id})
            await send_notification(session_id, "success", "✓ CV parsing completed")
            
            await send_event(session_id, "CV_EMBEDDING_STARTED", {"candidate_id": candidate_id})
            await send_notification(session_id, "info", "⚡ Generating embeddings...")
            await send_progress(session_id, "cv_embedding", 50)
        
        # Emit: Embedding done
        if session_id:
            await send_progress(session_id, "cv_embedding", 100)
            await send_event(session_id, "CV_EMBEDDING_DONE", {"candidate_id": candidate_id})
            await send_notification(session_id, "success", "✓ Embeddings generated successfully")
        
        # Log completion
        asyncio.create_task(log_activity("AI", f"Resume parsing completed for {candidate_id}"))
        
        logger.info(f"[{request_id}] Resume processing completed for {candidate_id}")
        
        # Parse result to return structured response
        try:
            data = json.loads(result_json_str) if isinstance(result_json_str, str) else result_json_str
        except:
            data = {"raw": result_json_str}
        
        # Emit: Processing complete
        if session_id:
            await send_event(session_id, "CV_PROCESSING_COMPLETE", {
                "candidate_id": candidate_id,
                "gridfs_id": gridfs_id,
                "status": "success"
            })
            await send_notification(session_id, "success", "✓ CV processed and ready for analysis")
        
        return ResumeUploadResponse(
            status="success",
            message="Resume uploaded and processing completed.",
            candidate_id=candidate_id,
            gridfs_id=gridfs_id,
            data=data
        ).model_dump()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Resume processing failed: {e}", exc_info=True)
        if session_id:
            await send_event(session_id, "CV_UPLOAD_ERROR", {"error": str(e)})
            await send_notification(session_id, "error", f"✗ CV processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Resume processing failed: {str(e)}")

async def _perform_ai_review(candidate_id: str, request_id: str = "unknown", session_id: Optional[str] = None):
    """
    Internal helper to run multi-agent review evaluation with comprehensive scoring.
    Builds context from candidate data, gathers requirements, and runs enhanced decision chain.
    Saves all results including comprehensive scoring data, risk assessment, and Neo4j analysis.
    """
    try:
        candidate = await get_candidate_by_id(candidate_id)
        if not candidate:
            logger.warning(f"[{request_id}] Candidate not found for review: {candidate_id}")
            if session_id:
                await send_notification(session_id, "error", "Candidate not found")
            return None

        parsed_data = candidate.get("parsed_data", {})
        external_intel = candidate.get("external_intel")
        
        # Emit: Analysis in progress
        if session_id:
            await send_progress(session_id, "cv_analysis", 10)
        
        # Build resume context
        resume_context = f"""
Name: {parsed_data.get('name')}
Skills: {', '.join(parsed_data.get('skills', []))}
Soft Skills: {', '.join(parsed_data.get('soft_skills', []))}
Education: {json.dumps(parsed_data.get('education', []), indent=2)}
Certifications: {', '.join(parsed_data.get('certifications', []))}
Projects: {' | '.join(parsed_data.get('projects', []))}
Extracurricular: {', '.join(parsed_data.get('extracurricular_activities', []))}
Hackathons: {', '.join(parsed_data.get('hackathons', []))}
Experience Years: {parsed_data.get('experience_years', 0)}
        """.strip()
        
        # Get requirements context
        requirements = await get_all_requirements()
        req_text = "Software Engineer Role"
        req_id = None
        if requirements:
            first_req = requirements[0]
            req_text = first_req.get("extracted_text") or first_req.get("title", "Software Engineer Role")
            req_id = first_req.get("_id")

        # Run multi-agent review
        logger.info(f"[{request_id}] Running AI review for {candidate_id}")
        report = await run_full_candidate_review(
            resume_context,
            req_text,
            requirement_id=req_id,
            external_intel=external_intel,
            parsed_data=parsed_data
        )
        
        # Emit: Multi-agent review completed
        if session_id:
            await send_progress(session_id, "cv_analysis", 40)
            await send_event(session_id, "CV_REVIEW_SCREENING_STARTED", {"stage": "screening"})
            await send_notification(session_id, "info", "📋 Screening phase completed")
        
        # Serialize report — include all Phase 1 & 2 cognitive metadata
        report_dict = {
            "screener":          report.screener.model_dump(),
            "tech":              report.tech.model_dump(),
            "culture":           report.culture.model_dump(),
            "extracurricular":   report.extracurricular.model_dump() if report.extracurricular else None,
            "hackathon":         report.hackathon.model_dump() if report.hackathon else None,
            "code_quality":      report.code_quality.model_dump() if report.code_quality else None,
            "rag_reasoning":     report.rag_reasoning,
            "external_intel":    report.external_intel,
            "final_decision":    report.final_decision,
            "rejection_feedback":report.rejection_feedback,
            # Phase 2: Cognitive metadata — used by /api/explain and /api/analytics
            "thinking_mode":     report.thinking_mode,
            "seniority_level":   report.seniority_level,
            "memory_injected":   report.memory_injected,
            "debate_verdict":    report.debate_verdict,
            "error_correction":  report.error_correction,
        }
        
        await update_candidate_review(candidate_id, report_dict)
        logger.info(f"[{request_id}] AI review completed for {candidate_id}")
        
        # Emit: Review phase completed
        if session_id:
            await send_progress(session_id, "cv_analysis", 60)
            await send_event(session_id, "CV_REVIEW_COMPLETED", {"stage": "review"})
            await send_notification(session_id, "info", "✓ AI review phase completed")
        
        # ============================================================================
        # COMPREHENSIVE SCORING WITH ENHANCED DECISION CHAIN
        # ============================================================================
        
        try:
            logger.info(f"[{request_id}] Running enhanced decision chain for {candidate_id}")
            
            # Convert reports to string format for decision chain
            screener_str = json.dumps(report.screener.model_dump())
            tech_str = json.dumps(report.tech.model_dump())
            culture_str = json.dumps(report.culture.model_dump())
            extracurr_str = json.dumps(report.extracurricular.model_dump()) if report.extracurricular else None
            hackathon_str = json.dumps(report.hackathon.model_dump()) if report.hackathon else None
            code_quality_str = json.dumps(report.code_quality.model_dump()) if report.code_quality else None
            external_intel_str = json.dumps(external_intel) if external_intel else None
            
            # Run comprehensive analysis first to get all insights
            logger.info(f"[{request_id}] Running comprehensive analysis for {candidate_id}")
            comprehensive_analysis = await run_comprehensive_analysis(
                screener_str, tech_str, culture_str, req_text,
                external_intel_str, extracurr_str, hackathon_str, code_quality_str
            )
            
            # Save Neo4j analysis results
            neo4j_results = {
                "skill_relationships": comprehensive_analysis.neo4j_insights.get("skill_relationships", {}),
                "transferable_skills": comprehensive_analysis.neo4j_insights.get("transferable_skills", []),
                "skill_gaps": comprehensive_analysis.neo4j_insights.get("skill_gaps", []),
                "career_path_fit": comprehensive_analysis.neo4j_insights.get("career_path_fit"),
                "seniority_gap": comprehensive_analysis.neo4j_insights.get("seniority_gap", 0),
                "domain_specialization": comprehensive_analysis.neo4j_insights.get("domain_specialization"),
                "learning_curve": comprehensive_analysis.neo4j_insights.get("learning_curve")
            }
            await save_neo4j_analysis_results(candidate_id, neo4j_results)
            logger.info(f"[{request_id}] Saved Neo4j analysis for {candidate_id}")
            
            # Save risk assessment results
            risk_data = {
                "overall_risk_score": comprehensive_analysis.risk_assessment.overall_risk_score,
                "skill_gap_risk": comprehensive_analysis.risk_assessment.skill_gap_risk,
                "experience_risk": comprehensive_analysis.risk_assessment.experience_risk,
                "consistency_risk": comprehensive_analysis.risk_assessment.consistency_risk,
                "red_flags_count": comprehensive_analysis.risk_assessment.red_flags_count,
                "red_flags": comprehensive_analysis.consistency_analysis.red_flags,
                "confidence_adjustment": comprehensive_analysis.risk_assessment.confidence_adjustment
            }
            await save_risk_assessment_results(candidate_id, risk_data)
            logger.info(f"[{request_id}] Saved risk assessment for {candidate_id}")
            
            # Run enhanced decision chain with comprehensive insights
            logger.info(f"[{request_id}] Running enhanced decision chain for {candidate_id}")
            decision_result = await run_enhanced_decision_chain(
                screener_str, tech_str, culture_str, req_text,
                external_intel_str, extracurr_str, hackathon_str, code_quality_str
            )
            
            # Prepare comprehensive scoring data
            scoring_data = {
                "data_aggregation": {
                    "all_skills": comprehensive_analysis.data_aggregation.all_skills,
                    "technical_depth": comprehensive_analysis.data_aggregation.technical_depth,
                    "experience_years": comprehensive_analysis.data_aggregation.experience_years,
                    "role_fit": comprehensive_analysis.data_aggregation.role_fit,
                    "culture_alignment": comprehensive_analysis.data_aggregation.culture_alignment,
                    "code_quality": comprehensive_analysis.data_aggregation.code_quality,
                    "external_verification": comprehensive_analysis.data_aggregation.external_verification
                },
                "consistency_analysis": {
                    "timeline_consistent": comprehensive_analysis.consistency_analysis.timeline_consistent,
                    "skill_consistency": comprehensive_analysis.consistency_analysis.skill_consistency,
                    "experience_level_match": comprehensive_analysis.consistency_analysis.experience_level_match,
                    "title_progression_logical": comprehensive_analysis.consistency_analysis.title_progression_logical,
                    "inconsistencies": comprehensive_analysis.consistency_analysis.inconsistencies,
                    "red_flags": comprehensive_analysis.consistency_analysis.red_flags
                },
                "neo4j_insights": neo4j_results,
                "risk_assessment": {
                    "overall_risk_score": comprehensive_analysis.risk_assessment.overall_risk_score,
                    "skill_gap_risk": comprehensive_analysis.risk_assessment.skill_gap_risk,
                    "experience_risk": comprehensive_analysis.risk_assessment.experience_risk,
                    "consistency_risk": comprehensive_analysis.risk_assessment.consistency_risk,
                    "red_flags_count": comprehensive_analysis.risk_assessment.red_flags_count
                },
                "comparative_analysis": {
                    "must_have_skills_coverage": comprehensive_analysis.comparative_analysis.must_have_skills_coverage,
                    "nice_to_have_skills_coverage": comprehensive_analysis.comparative_analysis.nice_to_have_skills_coverage,
                    "experience_seniority_match": comprehensive_analysis.comparative_analysis.experience_seniority_match,
                    "learning_potential": comprehensive_analysis.comparative_analysis.learning_potential,
                    "overqualified_risk": comprehensive_analysis.comparative_analysis.overqualified_risk,
                    "growth_trajectory": comprehensive_analysis.comparative_analysis.growth_trajectory
                },
                "confidence_factors": comprehensive_analysis.confidence_factors,
                "final_recommendation": comprehensive_analysis.final_recommendation
            }
            
            # Save comprehensive scoring data
            await save_comprehensive_scoring_data(candidate_id, scoring_data)
            logger.info(f"[{request_id}] Saved comprehensive scoring data for {candidate_id}")
            
            # Save final score with metadata
            final_score = decision_result.get("final_score", 0)
            category_scores = decision_result.get("category_scores", {})
            confidence = decision_result.get("meta_confidence_score", 0.5)
            decision = decision_result.get("decision", "further_interview")
            explanation = decision_result.get("explanation", "")
            risk_score = comprehensive_analysis.risk_assessment.overall_risk_score
            
            # Archive previous score if exists
            current_score = await get_complete_evaluation(candidate_id)
            if current_score and current_score.get("final_score_data"):
                await archive_previous_score(candidate_id, current_score["final_score_data"])
            
            await save_final_score_with_metadata(
                candidate_id, final_score, category_scores, confidence, 
                decision, explanation, risk_score
            )
            logger.info(f"[{request_id}] Saved final score for {candidate_id}: {final_score}/100 - {decision}")
            
            # Emit: Analysis completed
            if session_id:
                await send_progress(session_id, "cv_analysis", 95)
                await send_event(session_id, "CV_ANALYSIS_COMPLETED", {
                    "candidate_id": candidate_id,
                    "final_score": final_score,
                    "decision": decision,
                    "confidence": confidence
                })
                await send_notification(session_id, "success", f"✓ Analysis complete: Score {final_score}/100 ({decision})")
            
            await log_activity("AI", f"Comprehensive scoring completed for {candidate_id}", {
                "final_score": final_score,
                "decision": decision,
                "confidence": confidence,
                "risk_score": risk_score
            })
            
            # Return enhanced report with decision
            report_dict["enhanced_decision"] = decision_result
            report_dict["comprehensive_analysis"] = {
                "data_aggregation": scoring_data["data_aggregation"],
                "consistency_analysis": scoring_data["consistency_analysis"],
                "neo4j_insights": scoring_data["neo4j_insights"],
                "risk_assessment": scoring_data["risk_assessment"],
                "comparative_analysis": scoring_data["comparative_analysis"],
                "confidence_factors": scoring_data["confidence_factors"]
            }
            
            return report_dict
            
        except Exception as e:
            logger.warning(f"[{request_id}] Enhanced decision chain failed, continuing with standard review: {e}")
            await log_activity("AI", f"Decision chain error for {candidate_id}", {"error": str(e)})
            # Continue with standard results even if enhanced decision fails
            return report_dict
        
    except Exception as e:
        logger.error(f"[{request_id}] AI review failed for {candidate_id}: {e}", exc_info=True)
        return None

@router.post("/{candidate_id}/review")
async def review_candidate(
    candidate_id: str, 
    request: Request,
    session_id: Optional[str] = Query(None, description="WebSocket session ID for real-time updates")
):
    """Triggers the AI multi-agent evaluation pipeline for a candidate with real-time WebSocket updates."""
    try:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] Review triggered for {candidate_id}")
        
        # Emit: Analysis started
        if session_id:
            await send_event(session_id, "CV_ANALYSIS_STARTED", {"candidate_id": candidate_id})
            await send_notification(session_id, "info", "🤖 Starting AI analysis...")
            await send_progress(session_id, "cv_analysis", 5)
        
        asyncio.create_task(log_activity("AI", f"Multi-agent review started for {candidate_id}"))
        asyncio.create_task(_perform_ai_review(candidate_id, request_id, session_id))
        
        return {
            "status": "success",
            "message": "AI review triggered. Results will be available shortly.",
            "request_id": request_id
        }
    except Exception as e:
        logger.error(f"Error triggering review: {e}", exc_info=True)
        if session_id:
            await send_event(session_id, "CV_ANALYSIS_ERROR", {"error": str(e)})
            await send_notification(session_id, "error", f"✗ Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to trigger review")

@router.delete("/{candidate_id}")
async def remove_candidate(candidate_id: str, request: Request):
    """Permanently deletes a candidate record from MongoDB."""
    try:
        request_id = getattr(request.state, "request_id", "unknown")
        success = await delete_candidate(candidate_id)
        if not success:
            raise HTTPException(status_code=404, detail="Candidate not found or already deleted.")
        
        asyncio.create_task(log_activity("HR", f"Candidate deleted: {candidate_id}"))
        return {"status": "success", "message": "Candidate deleted", "request_id": request_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting candidate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete candidate")

@router.post("/{candidate_id}/enrich")
async def enrich_candidate(candidate_id: str, request: Request):
    """
    Triggers external data enrichment (GitHub, LinkedIn) and auto re-scores candidate.
    """
    try:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] Enrichment triggered for {candidate_id}")
        
        candidate = await get_candidate_by_id(candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        parsed_data = candidate.get("parsed_data", {})
        if not parsed_data:
            raise HTTPException(status_code=400, detail="Candidate must have parsed resume data first")

        async def _run_enrichment_and_rescore():
            try:
                # Run scraper agent
                logger.info(f"[{request_id}] Running scraper agent for {candidate_id}")
                intel = await run_scraper_agent(candidate_id, parsed_data)
                await update_external_intel(candidate_id, intel)
                
                await log_activity("AI", f"External enrichment completed for {candidate_id}", {
                    "github": bool(intel.get('github')),
                    "linkedin": bool(intel.get('linkedin_url'))
                })
                
                # Auto re-score
                logger.info(f"[{request_id}] Auto re-scoring after enrichment for {candidate_id}")
                await log_activity("AI", f"Auto-scoring triggered for {candidate_id}")
                await _perform_ai_review(candidate_id, request_id)
                
            except Exception as e:
                logger.error(f"[{request_id}] Enrichment pipeline failed: {e}", exc_info=True)
                await log_activity("AI", f"Enrichment failed for {candidate_id}", {"error": str(e)})

        asyncio.create_task(_run_enrichment_and_rescore())
        
        return {
            "status": "success",
            "message": "Enrichment started. Results will be available shortly.",
            "request_id": request_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting enrichment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start enrichment")

@router.post("/{candidate_id}/interview-scheduled")
async def schedule_interview(candidate_id: str, payload: InterviewScheduleRequest, request: Request):
    """
    Records interview scheduling for accepted candidate.
    Called by n8n workflow after acceptance decision.
    Updates candidate status and logs interview details.
    """
    try:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] Recording interview schedule for {candidate_id}")
        
        # Validate candidate exists
        candidate = await get_candidate_by_id(candidate_id)
        if not candidate:
            logger.warning(f"[{request_id}] Candidate not found: {candidate_id}")
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Prepare update data
        interview_data = {
            "status": "interview_scheduled",
            "interview_date": payload.interview_date,
            "interview_time": payload.interview_time,
            "interview_duration": payload.interview_duration,
            "timezone": payload.timezone,
            "meeting_link": payload.meeting_link,
            "interviewer_name": payload.interviewer_name,
            "notification_sent": True,
            "notification_timestamp": __import__("datetime").datetime.utcnow().isoformat()
        }
        
        # Update in database
        db = db_manager.get_db()
        if db is None:
            logger.error(f"[{request_id}] Database not available")
            raise HTTPException(status_code=500, detail="Database unavailable")
        
        result = await db["candidates"].update_one(
            {"_id": candidate_id},
            {
                "$set": interview_data,
                "$push": {
                    "status_history": {
                        "status": "interview_scheduled",
                        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                        "metadata": {
                            "interview_date": payload.interview_date,
                            "interviewer": payload.interviewer_name
                        }
                    }
                }
            }
        )
        
        if result.matched_count == 0:
            logger.warning(f"[{request_id}] Could not update candidate: {candidate_id}")
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Log activity
        candidate_name = candidate.get("parsed_data", {}).get("name", "Unknown")
        asyncio.create_task(log_activity("HR", f"Interview scheduled: {candidate_name}", {
            "candidate_id": candidate_id,
            "interview_date": payload.interview_date,
            "interview_time": payload.interview_time,
            "interviewer": payload.interviewer_name,
            "meeting_link": payload.meeting_link
        }))
        
        return {
            "status": "success",
            "message": "Interview scheduled successfully",
            "data": {
                "candidate_id": candidate_id,
                "status": "interview_scheduled",
                "interview_date": payload.interview_date,
                "interview_time": payload.interview_time,
                "meeting_link": payload.meeting_link
            },
            "request_id": request_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error scheduling interview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to schedule interview")

@router.post("/{candidate_id}/rejection")
async def reject_candidate(candidate_id: str, payload: CandidateRejectionRequest, request: Request):
    """
    Records candidate rejection with feedback.
    Called by n8n workflow after rejection decision.
    Updates candidate status and logs rejection details.
    """
    try:
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"[{request_id}] Recording rejection for {candidate_id}")
        
        # Validate candidate exists
        candidate = await get_candidate_by_id(candidate_id)
        if not candidate:
            logger.warning(f"[{request_id}] Candidate not found: {candidate_id}")
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Prepare rejection data
        rejection_data = {
            "status": "rejected",
            "rejection_reason": payload.rejection_reason,
            "feedback_summary": payload.feedback_summary,
            "allow_reapply": payload.allow_reapply,
            "reapply_after_months": payload.reapply_after_months,
            "notification_sent": True,
            "notification_timestamp": __import__("datetime").datetime.utcnow().isoformat()
        }
        
        # Calculate reapply eligibility if allowed
        if payload.allow_reapply:
            from datetime import datetime, timedelta
            reapply_date = datetime.utcnow() + timedelta(days=payload.reapply_after_months * 30)
            rejection_data["reapply_eligible_date"] = reapply_date.isoformat()
        
        # Update in database
        db = db_manager.get_db()
        if db is None:
            logger.error(f"[{request_id}] Database not available")
            raise HTTPException(status_code=500, detail="Database unavailable")
        
        result = await db["candidates"].update_one(
            {"_id": candidate_id},
            {
                "$set": rejection_data,
                "$push": {
                    "status_history": {
                        "status": "rejected",
                        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
                        "metadata": {
                            "reason": payload.rejection_reason,
                            "allow_reapply": payload.allow_reapply
                        }
                    }
                }
            }
        )
        
        if result.matched_count == 0:
            logger.warning(f"[{request_id}] Could not update candidate: {candidate_id}")
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Log activity
        candidate_name = candidate.get("parsed_data", {}).get("name", "Unknown")
        asyncio.create_task(log_activity("HR", f"Candidate rejected: {candidate_name}", {
            "candidate_id": candidate_id,
            "rejection_reason": payload.rejection_reason,
            "allow_reapply": payload.allow_reapply,
            "reapply_after_months": payload.reapply_after_months
        }))
        
        return {
            "status": "success",
            "message": "Rejection recorded successfully",
            "data": {
                "candidate_id": candidate_id,
                "status": "rejected",
                "rejection_reason": payload.rejection_reason,
                "allow_reapply": payload.allow_reapply,
                "reapply_after_months": payload.reapply_after_months
            },
            "request_id": request_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Error rejecting candidate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to record rejection")
