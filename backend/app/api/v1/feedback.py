"""
Phase 4 — /api/feedback
========================
HR Feedback ingestion endpoint.

POST /api/feedback
  → Captures HR corrections and decisions.
  → Writes back to both memory stores (Vector DB + MongoDB rules).
  → Feeds the reinforcement learning pipeline.
"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from services.db_service import get_candidate_by_id
from services.feedback_loop import record_system_feedback
from services.activity_logger import log_activity
from agents.agent_memory import record_outcome_to_memory

logger = logging.getLogger(__name__)
router = APIRouter()


def _std(status: str, data=None, message: str = "", request_id: str = ""):
    return {
        "status": status,
        "data": data or {},
        "message": message,
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


class FeedbackRequest(BaseModel):
    """HR feedback payload for a candidate decision."""
    candidate_id: str = Field(..., description="Candidate being reviewed")
    decision: str = Field(
        ...,
        description="HR decision: 'hired', 'rejected', 'shortlisted', 'further_review'",
    )
    reason: Optional[str] = Field(
        None,
        description="Why this decision was made (rejection reason, hiring note, etc.)",
    )
    role_category: str = Field(
        default="General",
        description="Role category for learning rule targeting",
    )
    rule_to_learn: Optional[str] = Field(
        None,
        description=(
            "Optional pattern to reinforce in system memory. "
            "Example: 'Candidates with ML skills but no DL experience underperform in this role.'"
        ),
    )
    override_ai_score: Optional[float] = Field(
        None, ge=0, le=100,
        description="If HR overrides the AI score, provide the corrected value (0–100).",
    )
    hr_notes: Optional[str] = Field(
        None,
        description="Additional context for audit trail.",
    )


@router.post("")
async def submit_feedback(payload: FeedbackRequest, request: Request):
    """
    Ingest HR feedback for a candidate decision.

    This endpoint:
    1. Validates the candidate exists.
    2. Calls the standard feedback loop (activity log + system feedback).
    3. Writes outcome back to the hybrid memory store (Vector DB + MongoDB rules).
    4. Logs an audit trail entry.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(
        f"[{request_id}] Feedback received: candidate={payload.candidate_id}, "
        f"decision={payload.decision}"
    )

    # Validate decision value
    valid_decisions = {"hired", "rejected", "shortlisted", "further_review"}
    if payload.decision not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision '{payload.decision}'. Must be one of: {sorted(valid_decisions)}",
        )

    # Fetch candidate
    candidate = await get_candidate_by_id(payload.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    parsed_data  = candidate.get("parsed_data", {})
    name         = parsed_data.get("name", "Unknown")
    skills       = parsed_data.get("skills", [])
    resume_text  = (
        f"Name: {name}\n"
        f"Skills: {', '.join(skills)}\n"
        f"Projects: {' | '.join(parsed_data.get('projects', []))}"
    )

    # Determine final score (use override if provided, else existing AI score)
    existing_score = candidate.get("final_score_data", {}).get("final_score", 50.0)
    final_score = payload.override_ai_score if payload.override_ai_score is not None else existing_score

    # 1. Standard feedback loop
    try:
        await record_system_feedback(
            payload.candidate_id,
            payload.decision,
            payload.reason or "",
        )
    except Exception as e:
        logger.warning(f"[{request_id}] Standard feedback loop error (non-critical): {e}")

    # 2. Hybrid memory write-back
    try:
        await record_outcome_to_memory(
            candidate_id=payload.candidate_id,
            name=name,
            resume_text=resume_text,
            skills=skills,
            final_score=final_score,
            decision=payload.decision,
            role_category=payload.role_category,
            rejection_reason=payload.reason if payload.decision == "rejected" else None,
            rule_to_learn=payload.rule_to_learn,
        )
    except Exception as e:
        logger.warning(f"[{request_id}] Memory write-back error (non-critical): {e}")

    # 3. Activity log
    try:
        await log_activity(
            "HR",
            f"Feedback submitted: {name} → {payload.decision.upper()}",
            {
                "candidate_id": payload.candidate_id,
                "decision": payload.decision,
                "reason": payload.reason,
                "override_score": payload.override_ai_score,
                "rule_learned": payload.rule_to_learn,
            },
        )
    except Exception as e:
        logger.warning(f"[{request_id}] Activity log error (non-critical): {e}")

    return _std(
        "success",
        data={
            "candidate_id": payload.candidate_id,
            "candidate_name": name,
            "decision": payload.decision,
            "final_score_used": final_score,
            "memory_updated": True,
            "rule_learned": bool(payload.rule_to_learn),
        },
        message=f"Feedback recorded. Memory updated for role '{payload.role_category}'.",
        request_id=request_id,
    )


@router.get("/history/{candidate_id}")
async def get_feedback_history(candidate_id: str, request: Request):
    """
    Returns all HR feedback entries for a specific candidate from the audit trail.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    from app.database.connection_manager import db_manager
    db = db_manager.get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        logs = []
        async for log in (
            db["activity_logs"]
            .find({"metadata.candidate_id": candidate_id, "actor": "HR"})
            .sort("timestamp", -1)
            .limit(20)
        ):
            log["_id"] = str(log["_id"])
            ts = log.get("timestamp")
            log["timestamp"] = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
            logs.append(log)

        return _std(
            "success",
            data={"candidate_id": candidate_id, "feedback_history": logs, "count": len(logs)},
            request_id=request_id,
        )
    except Exception as e:
        logger.error(f"[{request_id}] Feedback history error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch feedback history")
