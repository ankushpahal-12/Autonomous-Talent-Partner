"""
Phase 4 — /api/explain
=======================
XAI (Explainable AI) endpoint.

GET /api/explain/{candidate_id}
  → Returns why a candidate was selected or rejected:
    - Score breakdown (per-agent)
    - Agent reasoning traces (Chain-of-Thought)
    - Rule influences (from MongoDB learning rules)
    - Missing skills / skill gaps
    - Debate verdicts (if any)
    - Error correction flags (if any)
"""

import logging
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime

from services.db_service import get_candidate_by_id
from agents.agent_memory import build_memory_context

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


@router.get("/{candidate_id}")
async def explain_candidate_decision(candidate_id: str, request: Request):
    """
    Returns a full XAI explanation of why this candidate was selected, rejected,
    or shortlisted.

    Includes:
    - Score breakdown per agent
    - Reasoning traces (Chain-of-Thought logs)
    - Skill gaps and missing requirements
    - Memory context: similar past candidates + active learning rules
    - Debate verdicts and error correction flags (if present)
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.info(f"[{request_id}] Explain requested for candidate: {candidate_id}")

    candidate = await get_candidate_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    ai_review      = candidate.get("ai_review", {})
    final_score_data = candidate.get("final_score_data", {})
    scoring_data   = candidate.get("comprehensive_scoring", {})
    risk_data      = candidate.get("risk_assessment", {})
    neo4j_data     = candidate.get("neo4j_analysis", {})
    parsed_data    = candidate.get("parsed_data", {})

    if not ai_review and not final_score_data:
        return _std(
            "success",
            data={"candidate_id": candidate_id, "explanation_available": False},
            message="No AI evaluation found for this candidate. Run /api/evaluate first.",
            request_id=request_id,
        )

    # ── Score Breakdown ───────────────────────────────────────────────────────
    score_breakdown = {}
    for agent_key in ["screener", "tech", "culture", "extracurricular", "hackathon", "code_quality"]:
        agent_data = ai_review.get(agent_key, {})
        if not agent_data:
            continue
        # Grab the primary numeric score field for each agent
        score_field_map = {
            "screener":        "stability_score",
            "tech":            "technical_fit_score",
            "culture":         "culture_fit_score",
            "extracurricular": "extracurricular_score",
            "hackathon":       "hackathon_score",
            "code_quality":    "code_quality_score",
        }
        score_breakdown[agent_key] = {
            "score": agent_data.get(score_field_map.get(agent_key, ""), "N/A"),
            "summary": agent_data.get("summary", "No summary available."),
            "reasoning_trace": agent_data.get("reasoning_trace", ""),
        }

    # ── Skill Gaps ────────────────────────────────────────────────────────────
    skill_gaps = neo4j_data.get("skill_gaps", [])
    missing_skills = [
        s.get("skill") for s in skill_gaps if isinstance(s, dict) and s.get("skill")
    ] if skill_gaps else []

    # ── Decision Summary ──────────────────────────────────────────────────────
    decision        = final_score_data.get("decision") or candidate.get("status", "unknown")
    final_score     = final_score_data.get("final_score")
    confidence      = final_score_data.get("confidence")
    explanation_text = final_score_data.get("explanation", "No explanation available.")

    # ── Memory Context: Similar Candidates + Rules ────────────────────────────
    memory_context_data = {}
    try:
        resume_text = (
            f"Skills: {', '.join(parsed_data.get('skills', []))}\n"
            f"Projects: {' | '.join(parsed_data.get('projects', []))}"
        )
        role_category = scoring_data.get("role_category", "General")
        memory_ctx = await build_memory_context(
            resume_text=resume_text,
            role_category=role_category,
            k_similar=3,
            rules_limit=3,
        )
        memory_context_data = {
            "similar_past_candidates": [
                {
                    "name": c.name,
                    "decision": c.decision,
                    "final_score": c.final_score,
                    "similarity": round(c.similarity_score, 4),
                    "rejection_reason": c.rejection_reason,
                }
                for c in memory_ctx.similar_past_candidates
            ],
            "active_rules": [
                {
                    "pattern": r.pattern,
                    "confidence": round(r.confidence, 2),
                }
                for r in memory_ctx.learned_rules
            ],
        }
    except Exception as e:
        logger.warning(f"[{request_id}] Memory context for explain failed (non-critical): {e}")
        memory_context_data = {"error": "Memory context unavailable."}

    # ── Red Flags + Risk ──────────────────────────────────────────────────────
    red_flags   = scoring_data.get("consistency_analysis", {}).get("red_flags", [])
    risk_score  = risk_data.get("overall_risk_score")
    flag_hr     = risk_data.get("flag_for_human_review", False)

    explanation_payload = {
        "candidate_id":   candidate_id,
        "candidate_name": parsed_data.get("name", "Unknown"),
        "decision":       decision,
        "final_score":    final_score,
        "confidence":     confidence,
        "explanation":    explanation_text,
        "thinking_mode":  ai_review.get("thinking_mode", "unknown"),
        "seniority_level":ai_review.get("seniority_level", "unknown"),
        "memory_injected":ai_review.get("memory_injected", False),
        "score_breakdown": score_breakdown,
        "missing_skills":  missing_skills,
        "red_flags":       red_flags,
        "risk_score":      risk_score,
        "flag_for_human_review": flag_hr,
        "memory_context":  memory_context_data,
        "neo4j_insights": {
            "skill_relationships": neo4j_data.get("skill_relationships", {}),
            "transferable_skills": neo4j_data.get("transferable_skills", []),
            "career_path_fit":     neo4j_data.get("career_path_fit"),
        },
    }

    logger.info(f"[{request_id}] Explanation built for {candidate_id}: decision={decision}")

    return _std(
        "success",
        data=explanation_payload,
        message="Explanation generated successfully.",
        request_id=request_id,
    )
