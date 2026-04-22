"""
Culture Agent — upgraded with Thinking Modes, Chain-of-Thought, and Self-Reflection.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from app.core.config import settings
from .agent_thinking import (
    ThinkingMode,
    build_cot_prefix,
    build_adaptive_prompt_context,
    run_self_reflection,
    apply_reflection_adjustments,
)


class CultureReport(BaseModel):
    communication_style: Literal["clear", "concise", "detailed", "verbose"] = Field(description="Dominant communication style")
    leadership_potential: bool = Field(description="Evidence of leadership or ownership")
    collaborative_tone: int = Field(description="1-10 score for collaborative work")
    soft_skills: List[str] = Field(description="List of soft skills found (e.g. Communication, Empathy, Leadership)", default=[])
    soft_skills_score: int = Field(description="1-10 score for soft skills depth. If no soft skills are mentioned, score is 1.")
    summary: str = Field(description="Analysis of soft skills and culture fit")
    culture_fit_score: int = Field(description="1-10 overall culture fit (weighted)")
    adaptability_score: int = Field(description="1-10 score for adaptability and learning curve", default=5)
    learning_curve_indicators: List[str] = Field(
        description="Examples of rapid career progression or adaptability to new domains", default=[]
    )
    reasoning_trace: str = Field(
        description="Brief trace of how the CoT steps were applied to reach this assessment.",
        default=""
    )


async def run_culture_agent(
    resume_text: str,
    job_requirement: str,
    mode: ThinkingMode = ThinkingMode.BALANCED,
    seniority_level: str = "mid",
    past_feedback_summary: Optional[str] = None,
    enable_self_reflection: bool = True,
) -> CultureReport:
    """
    Evaluates soft skills and culture fit based on the resume content.

    Args:
        resume_text: Full resume text.
        job_requirement: Full job description / requirements string.
        mode: ThinkingMode — STRICT, BALANCED, or POTENTIAL.
        seniority_level: 'junior', 'mid', 'senior', or 'lead'.
        past_feedback_summary: Optional memory context from past similar candidates.
        enable_self_reflection: Whether to run the self-review pass after initial output.

    Returns:
        CultureReport (possibly adjusted by self-reflection).
    """
    key = settings.get_key_for_agent(4)
    if not key:
        import logging
        logging.warning("Culture Agent started without a valid API key.")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=key,
        transport="rest",
        temperature=0.5,
        max_retries=5,
        timeout=60,
    )
    structured_llm = llm.with_structured_output(CultureReport)

    # ── Build Cognitive Prefix ────────────────────────────────────────────────
    cognitive_prefix = build_cot_prefix(mode)
    adaptive_context = build_adaptive_prompt_context(seniority_level, past_feedback_summary)

    prompt = f"""{cognitive_prefix}
{adaptive_context}

You are a Culture Fit and Soft Skills Reviewer.
Analyze the candidate's professional style based on their resume.

JOB REQUIREMENT:
{job_requirement}

CANDIDATE RESUME:
{resume_text}

Evaluate (step-by-step, as per the CoT protocol above):
1. Communication style in project descriptions and written content.
2. Leadership examples (mentoring, leading teams, ownership of outcomes).
3. Collaborative nature (teamwork, cross-functional projects, pair-programming).
4. SOFT SKILLS: Extract specific soft skills. IF NO SOFT SKILLS ARE FOUND, clearly state
   "No soft skills identified" in the summary and set soft_skills_score to 1.
5. ADAPTABILITY: Evidence of picking up new tools quickly or shifting domains successfully.
6. LEARNING CURVE: Frequency of promotions or increasing responsibility over time.
7. REASONING TRACE: Summarise how you stepped through the CoT protocol in 3-5 sentences.

Provide a structured culture analysis.
"""

    # ── Initial Agent Pass ────────────────────────────────────────────────────
    report: CultureReport = await structured_llm.ainvoke(prompt)

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
