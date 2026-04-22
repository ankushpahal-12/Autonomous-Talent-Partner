"""
elo_ranking_service.py — Dynamic Candidate Elo Percentile Ranking
=================================================================
Compares a candidate's final_score against the existing pool of candidates
in the same role category evaluated in the last 90 days, and generates a
human-readable percentile statement.

Example Output:
  "This candidate is in the Top 8% of all Python engineers evaluated this month."

This is a pure Python module — no LLM required.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Model
# ============================================================================

class EloRankingResult(BaseModel):
    """Percentile ranking result for a candidate."""
    final_score: int = Field(description="This candidate's final score (0-100)")
    percentile: float = Field(description="Percentile rank (0-100). Higher is better.")
    rank_in_pool: int = Field(description="Rank position (1 = best)")
    pool_size: int = Field(description="Total candidates in the comparison pool")
    role_category: str = Field(description="Role category used for comparison")
    elo_statement: str = Field(description="Human-readable percentile statement for HR dashboard")
    comparison_window_days: int = Field(default=90)
    pool_avg_score: float = Field(description="Average score in the comparison pool")
    pool_highest_score: int = Field(description="Highest score in the pool")


# ============================================================================
# Role Category Detection (duplicated from lead_agent for self-containment)
# ============================================================================

def _detect_role_category(job_requirement_text: str) -> str:
    """Detect role category from job requirement for comparison pool."""
    job_upper = job_requirement_text.upper()
    if any(k in job_upper for k in ["PYTHON", "BACKEND", "SERVER", "API", "DJANGO", "FLASK", "FASTAPI"]):
        return "Backend"
    elif any(k in job_upper for k in ["ML", "MACHINE LEARNING", "DATA SCIENCE", "AI", "NEURAL", "TENSORFLOW", "PYTORCH"]):
        return "Machine Learning"
    elif any(k in job_upper for k in ["FRONTEND", "REACT", "VUE", "ANGULAR", "UI", "CSS", "JAVASCRIPT"]):
        return "Frontend"
    elif any(k in job_upper for k in ["DEVOPS", "CLOUD", "KUBERNETES", "DOCKER", "CI/CD", "AWS", "TERRAFORM"]):
        return "DevOps"
    elif any(k in job_upper for k in ["ANDROID", "IOS", "FLUTTER", "REACT NATIVE", "MOBILE"]):
        return "Mobile"
    else:
        return "General"


def _percentile_to_statement(percentile: float, role_category: str, pool_size: int) -> str:
    """Convert a percentile rank to a compelling HR-ready statement."""
    if pool_size < 5:
        return (
            f"Insufficient comparison data (only {pool_size} candidates in the '{role_category}' pool). "
            f"A relative ranking will be available once more candidates are evaluated."
        )

    top_pct = round(100 - percentile, 1)

    if top_pct <= 5:
        tier = "exceptional — Top 5%"
        qualifier = "an elite"
    elif top_pct <= 10:
        tier = f"Top {top_pct:.0f}%"
        qualifier = "an outstanding"
    elif top_pct <= 25:
        tier = f"Top {top_pct:.0f}%"
        qualifier = "a strong"
    elif top_pct <= 50:
        tier = f"Top {top_pct:.0f}%"
        qualifier = "an above-average"
    elif top_pct <= 75:
        tier = f"Bottom {100 - top_pct:.0f}%"
        qualifier = "a below-average"
    else:
        tier = f"Bottom {100 - top_pct:.0f}%"
        qualifier = "a weak"

    return (
        f"ELO RANKING: This candidate scored in the {tier} of all {role_category} engineers "
        f"evaluated in the last 90 days (pool size: {pool_size} candidates). "
        f"They are considered {qualifier} applicant relative to all recent submissions."
    )


# ============================================================================
# Main Ranking Function
# ============================================================================

async def calculate_elo_ranking(
    candidate_final_score: int,
    job_requirement_text: str,
    db_collection=None
) -> EloRankingResult:
    """
    Calculates where this candidate ranks among the recent candidate pool.

    Args:
        candidate_final_score: The final integer score (0-100) from the decision chain.
        job_requirement_text: Used to detect role category for fair comparison.
        db_collection: MongoDB candidates collection (motor async). If None, returns a stub.

    Returns:
        EloRankingResult with a percentile statement and ranking metadata.
    """
    role_category = _detect_role_category(job_requirement_text)
    cutoff_date = datetime.utcnow() - timedelta(days=90)

    # --- Stub if no DB connection ---
    if db_collection is None:
        return EloRankingResult(
            final_score=candidate_final_score,
            percentile=50.0,
            rank_in_pool=1,
            pool_size=0,
            role_category=role_category,
            elo_statement="ELO RANKING: No comparison pool available yet. "
                         "Rankings will be generated once more candidates are evaluated.",
            pool_avg_score=0.0,
            pool_highest_score=candidate_final_score
        )

    try:
        # Query all candidates in this role category from the last 90 days
        cursor = db_collection.find(
            {
                "role_category": role_category,
                "created_at": {"$gte": cutoff_date},
                "ai_review.final_decision.final_score": {"$exists": True}
            },
            {"ai_review.final_decision.final_score": 1}
        )

        scores = []
        async for doc in cursor:
            score = doc.get("ai_review", {}).get("final_decision", {}).get("final_score")
            if isinstance(score, (int, float)):
                scores.append(int(score))

        if not scores:
            return EloRankingResult(
                final_score=candidate_final_score,
                percentile=50.0,
                rank_in_pool=1,
                pool_size=0,
                role_category=role_category,
                elo_statement=f"ELO RANKING: No prior {role_category} candidates in the database yet. "
                             f"This candidate is your first benchmark.",
                pool_avg_score=0.0,
                pool_highest_score=candidate_final_score
            )

        # Calculate percentile
        scores_sorted = sorted(scores)
        pool_size = len(scores_sorted)
        beats = sum(1 for s in scores_sorted if candidate_final_score > s)
        percentile = (beats / pool_size) * 100

        # Rank (1 = best)
        rank = pool_size - beats

        pool_avg = sum(scores_sorted) / pool_size
        pool_max = max(scores_sorted)

        statement = _percentile_to_statement(percentile, role_category, pool_size)

        return EloRankingResult(
            final_score=candidate_final_score,
            percentile=round(percentile, 1),
            rank_in_pool=rank,
            pool_size=pool_size,
            role_category=role_category,
            elo_statement=statement,
            pool_avg_score=round(pool_avg, 1),
            pool_highest_score=pool_max
        )

    except Exception as e:
        logger.error(f"EloRankingService error: {e}")
        return EloRankingResult(
            final_score=candidate_final_score,
            percentile=50.0,
            rank_in_pool=1,
            pool_size=0,
            role_category=role_category,
            elo_statement="ELO RANKING: Could not calculate ranking due to a database error.",
            pool_avg_score=0.0,
            pool_highest_score=candidate_final_score
        )
