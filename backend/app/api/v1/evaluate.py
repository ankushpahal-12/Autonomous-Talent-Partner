"""
Phase 4 — /api/evaluate
========================
Provides AI evaluation trigger endpoints with Thinking Mode support.
Clean, organised namespace separate from /api/candidates.
"""

import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from datetime import datetime

from services.db_service import get_candidate_by_id, update_candidate_review
from services.requirement_service import get_all_requirements
from agents.lead_agent import run_full_candidate_review
from agents.agent_thinking import ThinkingMode
from agents.agent_memory import get_past_feedback_summary
from agents.agent_debate import run_error_correction
from services.activity_logger import log_activity
from app.database.connection_manager import db_manager
import json

logger = logging.getLogger(__name__)
router = APIRouter()


class EvaluateRequest(BaseModel):
    """Request body for triggering AI evaluation."""
    thinking_mode: str = Field(
        default="balanced",
        description="Evaluation mode: 'strict', 'balanced', or 'potential'",
    )
    seniority_level: str = Field(
        default="mid",
        description="Role seniority: 'junior', 'mid', 'senior', or 'lead'",
    )
    role_category: str = Field(
        default="General",
        description="Role category for memory context (e.g. 'Machine Learning', 'Backend')",
    )
    use_memory: bool = Field(
        default=True,
        description="Whether to inject hybrid memory context into agents",
    )


def _std(status: str, data=None, message: str = "", request_id: str = ""):
    """Standardised JSON response envelope."""
    return {
        "status": status,
        "data": data or {},
        "message": message,
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.post("/{candidate_id}")
async def evaluate_candidate(
    candidate_id: str,
    payload: EvaluateRequest,
    request: Request,
):
    """
    Trigger the full multi-agent evaluation pipeline for a candidate.

    Supports Thinking Modes (strict / balanced / potential) and optional
    hybrid memory context injection.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(
        f"[{request_id}] Evaluate triggered: candidate={candidate_id}, "
        f"mode={payload.thinking_mode}, seniority={payload.seniority_level}"
    )

    # Validate thinking mode
    try:
        mode = ThinkingMode(payload.thinking_mode.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid thinking_mode '{payload.thinking_mode}'. Use: strict, balanced, potential",
        )

    candidate = await get_candidate_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    parsed_data = candidate.get("parsed_data", {})
    resume_context = (
        f"Name: {parsed_data.get('name')}\n"
        f"Skills: {', '.join(parsed_data.get('skills', []))}\n"
        f"Projects: {' | '.join(parsed_data.get('projects', []))}\n"
        f"Experience Years: {parsed_data.get('experience_years', 0)}"
    )

    # Fetch requirements
    requirements = await get_all_requirements()
    req_text = "Software Engineer Role"
    req_id = None
    if requirements:
        first_req = requirements[0]
        req_text = first_req.get("extracted_text") or first_req.get("title", req_text)
        req_id = first_req.get("_id")

    # Hybrid memory context
    past_feedback = None
    if payload.use_memory:
        try:
            past_feedback = await get_past_feedback_summary(
                resume_text=resume_context,
                role_category=payload.role_category,
            )
        except Exception as e:
            logger.warning(f"[{request_id}] Memory context fetch failed (non-critical): {e}")

    async def _run():
        try:
            report = await run_full_candidate_review(
                resume_context,
                req_text,
                requirement_id=req_id,
                external_intel=candidate.get("external_intel"),
                parsed_data=parsed_data,
                thinking_mode=mode,
                seniority_level=payload.seniority_level,
                past_feedback_summary=past_feedback,
            )
            report_dict = {
                "screener":       report.screener.model_dump(),
                "tech":           report.tech.model_dump(),
                "culture":        report.culture.model_dump(),
                "extracurricular":report.extracurricular.model_dump() if report.extracurricular else None,
                "hackathon":      report.hackathon.model_dump() if report.hackathon else None,
                "code_quality":   report.code_quality.model_dump() if report.code_quality else None,
                "rag_reasoning":  report.rag_reasoning,
                "final_decision": report.final_decision,
                "thinking_mode":  mode.value,
                "seniority_level":payload.seniority_level,
                "memory_injected": past_feedback is not None,
            }
            await update_candidate_review(candidate_id, report_dict)
            await log_activity("AI", f"Evaluation [{mode.value}] completed for {candidate_id}")
        except Exception as e:
            logger.error(f"[{request_id}] Background evaluation failed: {e}", exc_info=True)

    asyncio.create_task(_run())

    return _std(
        "success",
        data={"candidate_id": candidate_id, "thinking_mode": mode.value},
        message=f"Evaluation queued in [{mode.value.upper()}] mode. Results available shortly.",
        request_id=request_id,
    )


@router.get("/{candidate_id}/status")
async def get_evaluation_status(candidate_id: str, request: Request):
    """Check whether an evaluation result exists for this candidate."""
    request_id = getattr(request.state, "request_id", "unknown")
    candidate = await get_candidate_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    has_review = bool(candidate.get("ai_review"))
    has_score  = bool(candidate.get("final_score_data"))

    return _std(
        "success",
        data={
            "candidate_id": candidate_id,
            "has_ai_review": has_review,
            "has_final_score": has_score,
            "latest_thinking_mode": candidate.get("ai_review", {}).get("thinking_mode", "unknown"),
        },
        request_id=request_id,
    )
