"""
behavioral_agent.py — Psychographic & Team Archetype Profiler
=============================================================
An LLM-powered agent that analyzes writing style, action verbs, and
narrative patterns in resume text to map a candidate to one of 5 professional
archetypes and estimate key behavioral work-style dimensions.

Output is intentionally qualitative and HR-readable — it tells you WHO this
person is, not just what skills they have.
"""

import logging
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from .agent_thinking import (
    ThinkingMode,
    build_cot_prefix,
    build_adaptive_prompt_context,
    run_self_reflection,
    apply_reflection_adjustments,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class BehavioralProfile(BaseModel):
    """Psychographic profile and team archetype mapping for a candidate."""

    # Archetype classification
    primary_archetype: str = Field(
        description="Primary archetype. Must be one of: 'Architect', 'Executor', 'Collaborator', 'Innovator', 'Mentor'"
    )
    archetype_confidence: str = Field(
        description="Confidence in archetype assignment: 'High', 'Medium', or 'Low'"
    )

    # Work style dimensions (0-100 scales)
    solo_vs_team_score: int = Field(
        description="0 = extreme solo worker, 100 = extreme team collaborator. 50 = balanced."
    )
    detail_vs_vision_score: int = Field(
        description="0 = extremely detail-oriented, 100 = big-picture visionary. 50 = balanced."
    )
    risk_appetite: str = Field(
        description="Risk tolerance. Must be one of: 'Conservative', 'Balanced', 'Risk-Taker'"
    )

    # Personality signals
    communication_style: str = Field(
        description="Dominant communication style detected: 'Technical', 'Narrative', 'Quantitative', or 'Mixed'"
    )
    leadership_signal: str = Field(
        description="Leadership indication: 'Strong', 'Moderate', 'Minimal', or 'None Detected'"
    )

    # Fit flags
    team_fit_concerns: List[str] = Field(
        default_factory=list,
        description="Potential team culture mismatch concerns (if any). E.g. 'Lone Wolf pattern may conflict with collaborative Agile teams'."
    )

    # Human-readable output
    archetype_narrative: str = Field(
        description="1-2 sentence HR-ready summary describing the candidate's behavioral style and team fit implications."
    )
    reasoning_trace: str = Field(
        default="",
        description="Brief internal reasoning trace summarising how archetype and work-style dimensions were derived."
    )


# ============================================================================
# Archetype Descriptions (used in the prompt to guide the LLM)
# ============================================================================

ARCHETYPE_DESCRIPTIONS = """
ARCHETYPE GUIDE:
- Architect: Designs systems, writes design docs, favors long-form planning over fast iteration. Uses: "designed", "architected", "proposed", "structured".
- Executor: Gets things done fast. Bias for action and shipping. Uses: "built", "delivered", "launched", "shipped", "reduced latency by X%".
- Collaborator: Centers their work on the team. Uses "we", "mentored", "coordinated", "cross-functional". Thrives in Agile environments.
- Innovator: Pushes boundaries. Self-starters. Hackathons, side projects, open-source contributions. Uses: "experimented", "invented", "prototyped", "pioneered".
- Mentor: Leads by teaching and enabling others. Uses: "mentored", "coached", "led training", "created documentation for", "onboarded".
"""




async def run_behavioral_agent(
    resume_text: str,
    github_readme: Optional[str] = None,
    mode: ThinkingMode = ThinkingMode.BALANCED,
    seniority_level: str = "mid",
    past_feedback_summary: Optional[str] = None,
    enable_self_reflection: bool = True,
) -> BehavioralProfile:
    """
    Analyzes writing style and language patterns in a resume to determine
    the candidate's behavioral archetype and work-style dimensions.

    Args:
        resume_text: The full candidate resume text.
        github_readme: Optional README text from their best GitHub repo.

    Returns:
        BehavioralProfile with archetype, dimensions, and HR narrative.
    """
    key = settings.get_key_for_agent(3)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=key,
        transport="rest",
        temperature=0.3,
        max_retries=3,
        timeout=45
    )
    structured_llm = llm.with_structured_output(BehavioralProfile)

    # Combine resume and optional GitHub README
    analysis_text = f"=== RESUME ===\n{resume_text[:3000]}"
    if github_readme:
        analysis_text += f"\n\n=== GITHUB README (Top Project) ===\n{github_readme[:1000]}"

    # ── Build Cognitive Prefix ────────────────────────────────────────────────
    cognitive_prefix = build_cot_prefix(mode)
    adaptive_context = build_adaptive_prompt_context(seniority_level, past_feedback_summary)

    prompt = f"""{cognitive_prefix}
{adaptive_context}

You are an organizational psychologist and behavioral analyst specializing in tech talent.
Your task is to analyze the language patterns, action verbs, writing style, and narrative in the candidate's resume (and optionally their GitHub README) to:

1. Identify their PRIMARY team archetype.
2. Estimate their work style dimensions.
3. Write an HR-ready narrative about what kind of teammate they would be.

{ARCHETYPE_DESCRIPTIONS}

SCORING GUIDE:
- solo_vs_team_score: Count "I" vs "we" language. Look for individual ownership vs team credit.
- detail_vs_vision_score: Bullet-point thinkers (detail) vs narrative paragraph writers (vision).
- risk_appetite: Stable corporate roles = Conservative. Startup + hackathon experience = Risk-Taker.

IMPORTANT:
- Be ruthlessly specific. If they say "I built" 8 times and "we" zero times, that's a solo archetype signal.
- Look for Innovator signals: hackathons, open-source repos, personal projects outside work.
- Look for Mentor signals: "onboarded", "led workshops", "grew team from X to Y".
- Flag team fit concerns ONLY if genuine mismatch signals exist. Not every candidate needs a concern.

CANDIDATE TEXT TO ANALYZE:
{analysis_text}
"""

    # ── Initial Agent Pass ────────────────────────────────────────────────────
    try:
        profile: BehavioralProfile = await structured_llm.ainvoke(prompt)

        # ── Self-Reflection Pass ──────────────────────────────────────────────────
        if enable_self_reflection:
            review = await run_self_reflection(
                llm_instance=llm,
                initial_output=profile,
                resume_text=resume_text,
                job_requirement="Behavioral profiling and team archetype assessment.",
                mode=mode,
            )
            profile = apply_reflection_adjustments(profile, review)

        return profile
    except Exception as e:
        logger.error(f"BehavioralAgent failed: {e}")
        return BehavioralProfile(
            primary_archetype="Executor",
            archetype_confidence="Low",
            solo_vs_team_score=50,
            detail_vs_vision_score=50,
            risk_appetite="Balanced",
            communication_style="Mixed",
            leadership_signal="None Detected",
            team_fit_concerns=[],
            archetype_narrative="Behavioral profiling could not be completed due to an analysis error. Manual assessment recommended."
        )
