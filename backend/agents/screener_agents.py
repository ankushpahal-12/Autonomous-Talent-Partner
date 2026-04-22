from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from .agent_thinking import (
    ThinkingMode,
    build_cot_prefix,
    build_adaptive_prompt_context,
    run_self_reflection,
    apply_reflection_adjustments,
)

class EducationAnalysis(BaseModel):
    degree_relevance: int = Field(description="1-10 score for degree relevance to job")
    marks_score: int = Field(description="1-10 score based on GPA/Percentage (e.g. >80% = 9, 60-70% = 6)")
    summary: str = Field(description="Brief note on academic performance")

class InternshipAnalysis(BaseModel):
    prestige_tier: Literal["Tier 1 (Global Leaders)", "Tier 2 (Mid-size/Startup)", "Tier 3 (Local)", "None"] = Field(description="Prestige of the internship companies")
    duration_months: int = Field(description="Total internship duration in months")
    role_relevance: int = Field(description="1-10 score for internship role matching job requirements")
    summary: str = Field(description="Brief evaluation of internship quality")

class ScreenerReport(BaseModel):
    visa_status: Literal["eligible", "ineligible", "unknown"] = Field(description="Eligibility based on visa info")
    location_match: Literal["match", "mismatch", "remote_only"] = Field(description="Does candidate location match job location")
    experience_level: Literal["junior", "mid", "senior", "lead"] = Field(description="Estimated seniority level")
    education_score: int = Field(description="1-10 score for education (Marks + Relevance)")
    marks_percentage: float = Field(description="Parsed GPA/Marks as a percentage (0-100)")
    internship_score: int = Field(description="1-100 score for professional internships based on prestige and duration")
    internship_details: InternshipAnalysis
    certification_score: int = Field(description="1-10 score for professional certifications found")
    certifications_found: List[str] = Field(description="List of relevant certifications identified")
    summary: str = Field(description="1-2 sentence summary of hard requirement check")
    passed: bool = Field(description="True if basic criteria are met")
    stability_score: int = Field(description="1-10 score based on job switching frequency (High switching = Low score)", default=7)
    consistency_checks: List[str] = Field(description="Detection of date overlaps or role contradictions", default=[])
    reasoning_trace: str = Field(
        default="",
        description="Brief internal reasoning trace summarising how hard gates and soft factors were evaluated."
    )

async def run_screener_agent(
    resume_text: str,
    job_requirement: str,
    mode: ThinkingMode = ThinkingMode.BALANCED,
    seniority_level: str = "mid",
    past_feedback_summary: Optional[str] = None,
    enable_self_reflection: bool = True,
) -> ScreenerReport:
    """
    Evaluates hard requirements like visas, location, education, and seniority.
    Thinking Mode aware — STRICT applies zero-tolerance on hard gates.
    """
    key = settings.get_key_for_agent(0)  # Unique key for screener (was 3, now 0)
    if not key:
        import logging
        logging.warning("Screener Agent started without a valid API key.")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=key,
        transport="rest",
        temperature=0,
        max_retries=5,
        timeout=60
    )
    structured_llm = llm.with_structured_output(ScreenerReport)

    cot      = build_cot_prefix(mode)
    adaptive = build_adaptive_prompt_context(seniority_level, past_feedback_summary)

    mode_note = {
        ThinkingMode.STRICT:    "STRICT MODE: Apply zero tolerance on hard requirements — "
                                "if visa, location, or minimum experience is not met, flag as failed.",
        ThinkingMode.BALANCED:  "BALANCED MODE: Apply fair checks. Minor location flexibility is acceptable.",
        ThinkingMode.POTENTIAL: "POTENTIAL MODE: Focus on trajectory and overall profile. "
                                "Do not fail candidates for borderline location or experience gaps.",
    }[mode]

    prompt = f"""{cot}
{adaptive}
{mode_note}

You are a Recruitment Screener Agent. Check if a candidate meets the hard requirements
of the job description.

JOB REQUIREMENT:
{job_requirement}

CANDIDATE RESUME:
{resume_text}

Analyze the resume for:
1. Visa status or work authorization (if mentioned).
2. Current location vs required location.
3. Years of experience vs required seniority.
4. EDUCATION: Evaluate degree relevance. Parse HIGHEST MARKS/Percentage (e.g. 85%).
   Scoring: >85% = 9-10, 75-85% = 8, <75% = 6.
5. INTERNSHIPS (STRICT EVALUATION):
   - Tier 1: Global Leaders (Google, Amazon, Microsoft, Top 50 Banks/Consultancies).
   - Tier 2: Reputable Mid-size firms or established startups.
   - Tier 3: Local/Small firms.
   Scoring: Consider Duration (3+ months is ideal) and Role Match.
6. CERTIFICATIONS: Identify job-related professional certifications.
7. STABILITY (BEHAVIORAL):
   - Frequency of job switching.
   - Human cares about this: "Is the candidate stable or do they switch every 6 months?"
8. CONSISTENCY (TRUST):
   - Do dates align or overlap suspiciously?
   - Does the seniority claim match the years of experience?
9. REASONING TRACE: Summarise how you applied the CoT protocol in 3-5 sentences.

Provide a structured report. Highlight PRESTIGE for internships.
"""

    # ── Initial Agent Pass ────────────────────────────────────────────────────
    report: ScreenerReport = await structured_llm.ainvoke(prompt)

    # ── Self-Reflection Pass ──────────────────────────────────────────────────
    if enable_self_reflection:
        review = await run_self_reflection(
            llm_instance=llm,
            initial_output=report,
            resume_text=resume_text,
            job_requirement=job_requirement,
            mode=mode,
        )
        report = apply_reflection_adjustments(report, review)

    return report
