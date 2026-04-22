"""
retention_service.py — Flight Risk & Overqualification Prediction Engine
=========================================================================
A pure Python, deterministic algorithm (no LLM, zero latency, zero cost)
that analyzes candidate career history to predict:
  1. Flight Risk Level (HIGH / MEDIUM / LOW) based on tenure velocity
  2. Overqualification Risk based on title seniority vs job requirements

Inputs come from LinkedIn data scraped by the scraper_agent.
"""

import re
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field



class TenureRecord(BaseModel):
    """Single job tenure record."""
    company: str
    title: str
    tenure_months: int
    is_current: bool


class FlightRiskReport(BaseModel):
    """Complete flight risk analysis report."""
    risk_level: str = Field(description="'HIGH', 'MEDIUM', or 'LOW'")
    avg_tenure_months: float = Field(description="Average months per role")
    total_roles_analyzed: int = Field(description="Number of roles analyzed")
    overqualification_risk: str = Field(description="'overqualified', 'match', or 'underqualified'")
    candidate_seniority_detected: str = Field(description="Detected seniority level from titles")
    tenure_records: List[TenureRecord] = Field(default_factory=list)
    flight_risk_flags: List[str] = Field(default_factory=list, description="Specific risk flags raised")
    narrative: str = Field(description="1-2 sentence HR-ready summary")
    risk_score: float = Field(description="0.0 (no risk) to 1.0 (maximum risk)")




SENIORITY_LEVELS = {
    "executive": ["cto", "ceo", "vp", "vice president", "director", "chief", "head of", "partner"],
    "principal":  ["principal", "staff engineer", "distinguished", "fellow"],
    "senior":     ["senior", "sr.", "sr ", "lead", "architect", "tech lead"],
    "mid":        ["engineer", "developer", "analyst", "specialist", "consultant", "scientist"],
    "junior":     ["junior", "jr.", "jr ", "associate", "trainee", "intern", "graduate"],
}

JOB_REQ_SENIORITY_KEYWORDS = {
    "executive": ["director", "vp", "head of", "chief"],
    "principal":  ["principal", "staff"],
    "senior":     ["senior", "lead", "sr"],
    "mid":        ["mid-level", "mid level", "software engineer", "developer"],
    "junior":     ["junior", "entry level", "fresher", "graduate", "intern"],
}

SENIORITY_RANK = {"junior": 1, "mid": 2, "senior": 3, "principal": 4, "executive": 5}


def _detect_seniority_from_titles(titles: List[str]) -> str:
    """Detect candidate's highest seniority level from all job titles held."""
    highest = "mid"  # default
    highest_rank = SENIORITY_RANK.get("mid", 2)

    for title in titles:
        title_lower = title.lower()
        for level, keywords in SENIORITY_LEVELS.items():
            if any(k in title_lower for k in keywords):
                rank = SENIORITY_RANK.get(level, 2)
                if rank > highest_rank:
                    highest_rank = rank
                    highest = level

    return highest


def _detect_job_req_seniority(job_requirement_text: str) -> str:
    """Detect the target seniority level from the job requirement text."""
    req_lower = job_requirement_text.lower()
    for level, keywords in JOB_REQ_SENIORITY_KEYWORDS.items():
        if any(k in req_lower for k in keywords):
            return level
    return "mid"  # safe default




def _parse_year_month(date_val) -> Optional[tuple]:
    """Extract (year, month) from various date formats (dict, string, int)."""
    if isinstance(date_val, dict):
        return (date_val.get("year", 2024), date_val.get("month", 1))
    if isinstance(date_val, str):
        try:
            # Try "YYYY-MM" or "YYYY"
            parts = date_val.split("-")
            year = int(parts[0])
            month = int(parts[1]) if len(parts) > 1 else 1
            return (year, month)
        except Exception:
            return None
    if isinstance(date_val, int):
        return (date_val, 1)
    return None


def _calculate_tenure_months(starts_at, ends_at) -> int:
    """Calculate tenure in months between two date values."""
    start = _parse_year_month(starts_at)
    if not start:
        return 0

    if ends_at:
        end = _parse_year_month(ends_at)
    else:
        # Current role — use today
        now = datetime.now()
        end = (now.year, now.month)

    if not end:
        end = (2024, 1)

    months = (end[0] - start[0]) * 12 + (end[1] - start[1])
    return max(0, months)




def analyze_flight_risk(
    linkedin_data: Optional[dict],
    job_requirement_text: str = ""
) -> FlightRiskReport:
    """
    Analyzes LinkedIn experience data to predict candidate flight risk.

    Args:
        linkedin_data: LinkedIn profile dict from scraper_agent.scrape_linkedin_profile()
        job_requirement_text: The job description text (for overqualification check)

    Returns:
        FlightRiskReport with risk level, flags, and HR narrative
    """

    # --- No LinkedIn data available ---
    if not linkedin_data or linkedin_data.get("status") != "ok":
        return FlightRiskReport(
            risk_level="UNKNOWN",
            avg_tenure_months=0,
            total_roles_analyzed=0,
            overqualification_risk="unknown",
            candidate_seniority_detected="unknown",
            narrative="No LinkedIn data available. Flight risk could not be assessed.",
            risk_score=0.3  # mild default penalty for missing data
        )

    experience = linkedin_data.get("experience", [])
    if not experience:
        return FlightRiskReport(
            risk_level="UNKNOWN",
            avg_tenure_months=0,
            total_roles_analyzed=0,
            overqualification_risk="unknown",
            candidate_seniority_detected="unknown",
            narrative="LinkedIn profile found but no job history was extracted.",
            risk_score=0.3
        )

    # --- Step 1: Calculate tenure records ---
    tenure_records = []
    titles_held = []

    for exp in experience:
        title = exp.get("title", "Unknown Role")
        company = exp.get("company", "Unknown Company")
        starts_at = exp.get("starts_at")
        ends_at = exp.get("ends_at")
        is_current = ends_at is None

        months = _calculate_tenure_months(starts_at, ends_at)
        titles_held.append(title)

        tenure_records.append(TenureRecord(
            company=company,
            title=title,
            tenure_months=months,
            is_current=is_current
        ))

    # --- Step 2: Flight Risk Calculation ---
    valid_tenures = [r.tenure_months for r in tenure_records if r.tenure_months > 0]
    avg_tenure = sum(valid_tenures) / len(valid_tenures) if valid_tenures else 0

    flight_risk_flags = []
    risk_score = 0.0

    # Core tenure-based scoring
    if avg_tenure < 8:
        risk_level = "HIGH"
        risk_score = 0.85
        flight_risk_flags.append(f"CRITICAL: Average job tenure is only {avg_tenure:.0f} months — strong job-hopper signal.")
    elif avg_tenure < 14:
        risk_level = "HIGH"
        risk_score = 0.70
        flight_risk_flags.append(f"Average tenure of {avg_tenure:.0f} months is below the 14-month stability threshold.")
    elif avg_tenure < 24:
        risk_level = "MEDIUM"
        risk_score = 0.40
        flight_risk_flags.append(f"Average tenure of {avg_tenure:.0f} months suggests mild instability.")
    else:
        risk_level = "LOW"
        risk_score = 0.10

    # Check for recent rapid switching (last 2 roles under 12 months)
    recent_roles = tenure_records[:2]
    if all(r.tenure_months < 12 for r in recent_roles) and len(recent_roles) == 2:
        risk_score = min(1.0, risk_score + 0.15)
        flight_risk_flags.append("PATTERN: Last 2 roles both lasted under 12 months — escalating switch velocity.")
        if risk_level == "MEDIUM":
            risk_level = "HIGH"

    # --- Step 3: Overqualification Detection ---
    candidate_seniority = _detect_seniority_from_titles(titles_held)
    job_seniority = _detect_job_req_seniority(job_requirement_text)

    candidate_rank = SENIORITY_RANK.get(candidate_seniority, 2)
    job_rank = SENIORITY_RANK.get(job_seniority, 2)

    if candidate_rank >= job_rank + 2:
        overqualification_risk = "overqualified"
        risk_score = min(1.0, risk_score + 0.20)
        flight_risk_flags.append(
            f"OVERQUALIFICATION: Candidate appears to be '{candidate_seniority}' level applying for a '{job_seniority}' role. "
            f"High likelihood of leaving once a better-fitting offer emerges."
        )
    elif candidate_rank < job_rank - 1:
        overqualification_risk = "underqualified"
    else:
        overqualification_risk = "match"

    # --- Step 4: Generate HR Narrative ---
    if risk_level == "HIGH":
        narrative = (
            f"HIGH FLIGHT RISK: Candidate has an average tenure of {avg_tenure:.0f} months per role "
            f"across {len(tenure_records)} positions. This pattern suggests a high probability of early departure. "
            f"Recommend asking behavioral retention questions in interview."
        )
    elif risk_level == "MEDIUM":
        narrative = (
            f"MEDIUM FLIGHT RISK: Average tenure of {avg_tenure:.0f} months is below ideal. "
            f"Candidate shows some stability but warrants a retention conversation during the offer stage."
        )
    else:
        narrative = (
            f"LOW FLIGHT RISK: Candidate demonstrates strong tenure averaging {avg_tenure:.0f} months per role. "
            f"Retention risk is minimal based on career history."
        )

    if overqualification_risk == "overqualified":
        narrative += f" Note: Candidate may be overqualified (detected '{candidate_seniority}' vs target '{job_seniority}')."

    return FlightRiskReport(
        risk_level=risk_level,
        avg_tenure_months=round(avg_tenure, 1),
        total_roles_analyzed=len(tenure_records),
        overqualification_risk=overqualification_risk,
        candidate_seniority_detected=candidate_seniority,
        tenure_records=tenure_records,
        flight_risk_flags=flight_risk_flags,
        narrative=narrative,
        risk_score=round(min(1.0, risk_score), 2)
    )
