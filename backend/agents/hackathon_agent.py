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

class HackathonReport(BaseModel):
    hackathons_found: List[str] = Field(description="List of hackathons mentioned")
    wins_and_top_tier: List[str] = Field(description="Evidence of winning or high-ranking placements")
    participation_percentage: int = Field(description="Percentage score based on wins vs participation (e.g. 100% for win, 50% for finalist)")
    hackathon_score: int = Field(description="1-10 overall score for hackathon profile")
    summary: str = Field(description="Brief assessment of the candidate's competitive coding/innovation track record")
    reasoning_trace: str = Field(
        default="",
        description="Brief internal reasoning trace summarising how hackathon level and position were calculated."
    )

async def run_hackathon_agent(
    resume_text: str,
    mode: ThinkingMode = ThinkingMode.BALANCED,
    seniority_level: str = "mid",
    past_feedback_summary: Optional[str] = None,
    enable_self_reflection: bool = True,
) -> HackathonReport:
    """
    Evaluates hackathon wins, participation, and competitive nature.
    Thinking Mode aware — POTENTIAL mode credits active participation even without wins.
    """
    key = settings.get_key_for_agent(6)
    if not key:
        import logging
        logging.warning("Hackathon Agent started without a valid API key.")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=key,
        transport="rest",
        temperature=0.2,
        max_retries=5,
        timeout=60
    )
    structured_llm = llm.with_structured_output(HackathonReport)

    cot      = build_cot_prefix(mode)
    adaptive = build_adaptive_prompt_context(seniority_level, past_feedback_summary)

    mode_note = {
        ThinkingMode.STRICT:    "Only count wins or top-3 finishes as significant evidence.",
        ThinkingMode.BALANCED:  "Weight wins heavily but credit finalists and active participants.",
        ThinkingMode.POTENTIAL: "Any hackathon participation shows initiative — reward consistent "
                                "participation even without placements.",
    }[mode]

    prompt = f"""{cot}
{adaptive}
EVALUATION STANCE: {mode_note}

You are a "Hackathon & Competition" Evaluator.
Analyze the candidate's resume for hackathons, coding competitions, and innovation challenges.

CRITERIA FOR SCORING (Matrix):
1. LEVEL MULTIPLIER:
   - International: 1.5x (e.g. MajorMLH, Google Solution Challenge, International ICPC)
   - National: 1.2x (e.g. Smart India Hackathon, National level University events)
   - Local: 1.0x (e.g. College-specific hackathons)

2. POSITION BASE SCORE (out of 100):
   - Winner / 1st Place: 100
   - 2nd / 3rd Place: 80
   - Top 10 / Finalist: 60
   - Participant: 40

Calculation: participation_percentage = (Position Base * Level Multiplier), capped at 100.
If no participation is found, the score MUST be 0.

3. REASONING TRACE: Summarise how you applied the level multiplier and position scoring in 3-5 sentences.

CANDIDATE RESUME:
{resume_text}

Evaluate the level and position specifically. Output the calculated percentage.
"""

    # ── Initial Agent Pass ────────────────────────────────────────────────────
    report: HackathonReport = await structured_llm.ainvoke(prompt)

    # ── Self-Reflection Pass ──────────────────────────────────────────────────
    if enable_self_reflection:
        review = await run_self_reflection(
            llm_instance=llm,
            initial_output=report,
            resume_text=resume_text,
            job_requirement="Hackathon participation and competitive coding assessment.",
            mode=mode,
        )
        report = apply_reflection_adjustments(report, review)

    return report
