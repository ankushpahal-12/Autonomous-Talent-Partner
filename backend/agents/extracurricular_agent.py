from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.config import settings
from .agent_thinking import (
    ThinkingMode,
    build_cot_prefix,
    build_adaptive_prompt_context,
    run_self_reflection,
    apply_reflection_adjustments,
)

class ExtracurricularReport(BaseModel):
    activities: List[str] = Field(description="List of identified extra-curricular activities")
    leadership_roles: List[str] = Field(description="Evidence of leadership (e.g. Captain, President, Lead)")
    social_impact: str = Field(description="Brief note on volunteering or community contribution")
    extracurricular_score: int = Field(description="1-10 overall score for breadth and depth of activities")
    summary: str = Field(description="Assessment of the candidate's well-roundedness")
    reasoning_trace: str = Field(
        default="",
        description="Brief internal reasoning trace summarising how breadth and leadership were assessed."
    )

async def run_extracurricular_agent(
    resume_text: str,
    mode: ThinkingMode = ThinkingMode.BALANCED,
    seniority_level: str = "mid",
    past_feedback_summary: Optional[str] = None,
    enable_self_reflection: bool = True,
) -> ExtracurricularReport:
    """
    Evaluates candidate activities beyond academics and technical work.
    Thinking Mode aware — POTENTIAL mode rewards breadth and leadership signals more.
    """
    key = settings.get_key_for_agent(5)
    if not key:
        import logging
        logging.warning("Extracurricular Agent started without a valid API key.")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=key,
        transport="rest",
        temperature=0.3,
        max_retries=5,
        timeout=60
    )
    structured_llm = llm.with_structured_output(ExtracurricularReport)

    cot   = build_cot_prefix(mode)
    adaptive = build_adaptive_prompt_context(seniority_level, past_feedback_summary)

    mode_note = {
        ThinkingMode.STRICT:    "Apply strict standards — only verified, high-impact activities count.",
        ThinkingMode.BALANCED:  "Evaluate breadth and depth proportionally.",
        ThinkingMode.POTENTIAL: "Reward any evidence of hustle, leadership, or initiative generously — "
                                "even informal activities count if they show character.",
    }[mode]

    prompt = f"""{cot}
{adaptive}
EVALUATION STANCE: {mode_note}

You are an "Extra-Curricular Achievement" Reviewer.
Analyze the candidate's resume for activities outside of their technical career and academics.

Look for:
1. Volunteering and social causes.
2. Leadership roles in clubs, sports, or student bodies.
3. Creative interests (Music, Arts, Writing).
4. Competitions (non-technical or multi-disciplinary).
5. REASONING TRACE: Summarise how you identified and scored activities in 3-5 sentences.

CANDIDATE RESUME:
{resume_text}

Provide a structured report. If no such activities are found, state
"No extracurricular activities identified" and score as 1.
"""

    # ── Initial Agent Pass ────────────────────────────────────────────────────
    report: ExtracurricularReport = await structured_llm.ainvoke(prompt)

    # ── Self-Reflection Pass ──────────────────────────────────────────────────
    if enable_self_reflection:
        review = await run_self_reflection(
            llm_instance=llm,
            initial_output=report,
            resume_text=resume_text,
            job_requirement="Extracurricular activities and breadth assessment.",
            mode=mode,
        )
        report = apply_reflection_adjustments(report, review)

    return report
