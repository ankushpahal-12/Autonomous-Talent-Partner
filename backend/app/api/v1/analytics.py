"""
Phase 4 — /api/analytics
=========================
Analytics engine tracking:
  - Selection / rejection rates
  - Agent accuracy trends
  - Feedback trends and HR override frequency
  - Thinking mode usage distribution
  - Score distributions and risk patterns
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request
from collections import defaultdict

from app.database.connection_manager import db_manager

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


# ─────────────────────────────────────────────────────────────────────────────
# Helper: fetch candidates from DB
# ─────────────────────────────────────────────────────────────────────────────

async def _get_candidates(db, days: int = 30) -> list:
    cutoff = datetime.utcnow() - timedelta(days=days)
    candidates = []
    async for c in db["candidates"].find({"created_at": {"$gte": cutoff}}):
        c["_id"] = str(c["_id"])
        candidates.append(c)
    # Fallback: if no date filter matches, return all
    if not candidates:
        async for c in db["candidates"].find({}):
            c["_id"] = str(c["_id"])
            candidates.append(c)
    return candidates


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/analytics/overview
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/overview")
async def analytics_overview(
    request: Request,
    days: int = Query(30, ge=1, le=365, description="Lookback window in days"),
):
    """
    High-level hiring funnel analytics:
    - Total candidates, selection rate, rejection rate
    - Average AI score
    - Thinking mode distribution
    - Score bucket distribution (0-40, 40-60, 60-80, 80-100)
    """
    request_id = getattr(request.state, "request_id", "unknown")
    db = db_manager.get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        candidates = await _get_candidates(db, days)
        total = len(candidates)

        if total == 0:
            return _std("success", data={"total_candidates": 0, "message": "No data in range"}, request_id=request_id)

        # Decision counts
        decision_counts: dict = defaultdict(int)
        score_buckets = {"0-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}
        mode_counts: dict = defaultdict(int)
        scores = []
        hr_overrides = 0

        for c in candidates:
            status = c.get("status", "pending")
            decision_counts[status] += 1

            # Score
            score = c.get("final_score_data", {}).get("final_score")
            if score is not None:
                scores.append(float(score))
                if score < 40:
                    score_buckets["0-40"] += 1
                elif score < 60:
                    score_buckets["40-60"] += 1
                elif score < 80:
                    score_buckets["60-80"] += 1
                else:
                    score_buckets["80-100"] += 1

            # Thinking mode
            mode = c.get("ai_review", {}).get("thinking_mode", "unknown")
            mode_counts[mode] += 1

            # HR overrides (override_score present)
            if c.get("final_score_data", {}).get("hr_override_score"):
                hr_overrides += 1

        selected = decision_counts.get("selected", 0) + decision_counts.get("hired", 0)
        rejected = decision_counts.get("rejected", 0)
        avg_score = round(sum(scores) / len(scores), 1) if scores else None

        return _std(
            "success",
            data={
                "period_days": days,
                "total_candidates": total,
                "decision_breakdown": dict(decision_counts),
                "selection_rate":  round(selected / total * 100, 1) if total else 0,
                "rejection_rate":  round(rejected / total * 100, 1) if total else 0,
                "avg_final_score": avg_score,
                "score_distribution": score_buckets,
                "thinking_mode_usage": dict(mode_counts),
                "hr_override_count": hr_overrides,
            },
            message=f"Analytics for the last {days} days.",
            request_id=request_id,
        )
    except Exception as e:
        logger.error(f"[{request_id}] Analytics overview error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to compute analytics")


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/analytics/rejection-reasons
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/rejection-reasons")
async def rejection_reasons(
    request: Request,
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Returns the most frequent rejection reasons from HR feedback.
    Useful for identifying systemic patterns (e.g. 'Missing DL skills').
    """
    request_id = getattr(request.state, "request_id", "unknown")
    db = db_manager.get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        reason_counts: dict = defaultdict(int)

        async for c in db["candidates"].find({
            "status": "rejected",
            "rejection_reason": {"$exists": True, "$ne": ""},
        }):
            reason = c.get("rejection_reason", "").strip()
            if reason:
                # Normalise to first 80 chars for grouping
                key = reason[:80]
                reason_counts[key] += 1

        # Also check activity_logs for HR feedback reasons
        async for log in db["activity_logs"].find({
            "actor": "HR",
            "timestamp": {"$gte": cutoff},
            "metadata.reason": {"$exists": True, "$ne": None},
        }).limit(500):
            reason = log.get("metadata", {}).get("reason", "").strip()
            if reason:
                reason_counts[reason[:80]] += 1

        sorted_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

        return _std(
            "success",
            data={
                "period_days": days,
                "top_rejection_reasons": [
                    {"reason": r, "count": c} for r, c in sorted_reasons
                ],
            },
            request_id=request_id,
        )
    except Exception as e:
        logger.error(f"[{request_id}] Rejection reasons error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch rejection reasons")


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/analytics/agent-accuracy
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/agent-accuracy")
async def agent_accuracy(
    request: Request,
    days: int = Query(30, ge=1, le=365),
):
    """
    Computes per-agent score vs. final HR outcome correlation.
    Identifies which agents are most predictive of the final hiring decision.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    db = db_manager.get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        candidates = await _get_candidates(db, days)

        SCORE_FIELDS = {
            "tech_agent":            ("ai_review.tech",            "technical_fit_score"),
            "culture_agent":         ("ai_review.culture",         "culture_fit_score"),
            "screener_agent":        ("ai_review.screener",        "stability_score"),
            "extracurricular_agent": ("ai_review.extracurricular", "extracurricular_score"),
            "hackathon_agent":       ("ai_review.hackathon",       "hackathon_score"),
            "code_quality_agent":    ("ai_review.code_quality",    "code_quality_score"),
        }

        agent_stats: dict = {k: {"align_count": 0, "total": 0, "avg_score": []} for k in SCORE_FIELDS}
        positive_statuses = {"selected", "hired", "shortlisted"}

        for c in candidates:
            final_decision = c.get("status", "pending")
            is_positive    = final_decision in positive_statuses

            for agent_key, (path, score_field) in SCORE_FIELDS.items():
                parts = path.split(".")
                obj = c
                for p in parts:
                    obj = obj.get(p, {}) if isinstance(obj, dict) else {}
                score = obj.get(score_field) if isinstance(obj, dict) else None

                if score is None:
                    continue

                agent_stats[agent_key]["total"] += 1
                agent_stats[agent_key]["avg_score"].append(float(score))

                # Alignment: agent scored >= 6 and HR selected, or < 6 and HR rejected
                predicted_positive = float(score) >= 6
                if predicted_positive == is_positive:
                    agent_stats[agent_key]["align_count"] += 1

        result = {}
        for agent, stats in agent_stats.items():
            total = stats["total"]
            if total == 0:
                continue
            result[agent] = {
                "total_evaluations": total,
                "accuracy_pct": round(stats["align_count"] / total * 100, 1),
                "avg_score": round(sum(stats["avg_score"]) / len(stats["avg_score"]), 2),
            }

        return _std(
            "success",
            data={"period_days": days, "agent_accuracy": result},
            message="Agent accuracy computed vs final HR decisions.",
            request_id=request_id,
        )
    except Exception as e:
        logger.error(f"[{request_id}] Agent accuracy error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to compute agent accuracy")


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/analytics/feedback-trends
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/feedback-trends")
async def feedback_trends(
    request: Request,
    days: int = Query(30, ge=1, le=365),
):
    """
    Returns HR feedback activity trends:
    - Daily decision counts
    - Override frequency (HR changing AI decisions)
    - Rule learning rate (new patterns added to memory)
    """
    request_id = getattr(request.state, "request_id", "unknown")
    db = db_manager.get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        daily: dict = defaultdict(lambda: defaultdict(int))

        async for log in db["activity_logs"].find({
            "actor": "HR",
            "timestamp": {"$gte": cutoff},
        }):
            ts = log.get("timestamp")
            day_key = ts.strftime("%Y-%m-%d") if hasattr(ts, "strftime") else str(ts)[:10]
            metadata = log.get("metadata", {})
            decision = metadata.get("decision", "unknown")
            daily[day_key][decision] += 1
            if metadata.get("override_score") is not None:
                daily[day_key]["hr_override"] += 1
            if metadata.get("rule_learned"):
                daily[day_key]["rule_learned"] += 1

        # Sort by date
        sorted_days = sorted(daily.items())

        return _std(
            "success",
            data={
                "period_days": days,
                "daily_trends": [
                    {"date": d, **dict(counts)} for d, counts in sorted_days
                ],
            },
            request_id=request_id,
        )
    except Exception as e:
        logger.error(f"[{request_id}] Feedback trends error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch feedback trends")


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/analytics/health
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/health")
async def analytics_health(request: Request):
    """Quick health check for the analytics module and its DB connection."""
    request_id = getattr(request.state, "request_id", "unknown")
    db = db_manager.get_db()
    return _std(
        "success",
        data={"db_connected": db is not None},
        message="Analytics engine is operational.",
        request_id=request_id,
    )
