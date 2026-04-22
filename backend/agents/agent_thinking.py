"""
Agent Thinking Modes, Chain-of-Thought, and Self-Reflection Layer.

This module implements the cognitive upgrade layer for all agents:
  - ThinkingMode: Strict / Balanced / Potential — changes how agents evaluate candidates.
  - build_cot_prefix: Enforces step-by-step reasoning before the agent produces output.
  - SelfReflectionReview: A lightweight Pydantic model for the self-review pass.
  - run_self_reflection: Runs a second LLM pass to critique and refine the initial report.
  - build_adaptive_prompt_context: Adjusts instructions based on role seniority and past feedback.
"""

import logging
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ── Thinking Modes ───────────────────────────────────────────────────────────

class ThinkingMode(str, Enum):
    """
    Controls the evaluation lens an agent applies.

    STRICT    – High standards. Penalise gaps heavily. Best for senior/critical roles.
    BALANCED  – Normal hiring bar. Weigh strengths and gaps proportionally.
    POTENTIAL – Future-focused. Reward learning ability and growth trajectory.
                Gaps are acceptable if strong fundamentals exist.
    """
    STRICT    = "strict"
    BALANCED  = "balanced"
    POTENTIAL = "potential"


THINKING_MODE_INSTRUCTIONS: dict[ThinkingMode, str] = {
    ThinkingMode.STRICT: """
EVALUATION MODE: STRICT
━━━━━━━━━━━━━━━━━━━━━━
• Apply the HIGHEST standard. Every missing required skill is a red flag.
• Do NOT give benefit of the doubt on ambiguous data.
• Any unexplained employment gap (>3 months) must be flagged.
• Scores MUST reflect actual evidence, not potential.
• Only "Professional/Industry" or "Startup/High Growth" projects count toward technical depth.
""",
    ThinkingMode.BALANCED: """
EVALUATION MODE: BALANCED
━━━━━━━━━━━━━━━━━━━━━━━━
• Apply standard hiring criteria. Weigh both strengths and gaps fairly.
• Missing nice-to-have skills are acceptable if core skills are strong.
• Give reasonable benefit of the doubt on minor resume ambiguities.
• Scores should reflect the overall candidate picture.
""",
    ThinkingMode.POTENTIAL: """
EVALUATION MODE: POTENTIAL (Future-Focused)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Prioritise LEARNING VELOCITY and GROWTH TRAJECTORY over current gaps.
• A candidate who built complex projects with limited experience is a STRONG signal.
• Missing skills that are learnable within 1-3 months should NOT penalise the score.
• Reward cross-domain adaptability and self-teaching examples.
• Potential score and growth_indicators are PRIMARY drivers of the final score.
""",
}


def get_thinking_mode_instructions(mode: ThinkingMode) -> str:
    """Return the instruction block for the given thinking mode."""
    return THINKING_MODE_INSTRUCTIONS.get(mode, THINKING_MODE_INSTRUCTIONS[ThinkingMode.BALANCED])


# ── Chain-of-Thought Prefix ───────────────────────────────────────────────────

CHAIN_OF_THOUGHT_PREFIX = """
REASONING PROTOCOL — MANDATORY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Before producing your structured output, silently reason through these steps:

  Step 1 — PARSE:       Extract all factual data from the resume (skills, projects, experience, education).
  Step 2 — VERIFY:      Cross-check claimed skills against actual project usage. Flag any keyword-stuffed skills.
  Step 3 — COMPARE:     Map the candidate's verified profile against the job requirements.
  Step 4 — EVALUATE GAP: Identify critical gaps (hard blockers) vs. acceptable gaps (learnable).
  Step 5 — SYNTHESISE:  Form an overall assessment consistent with the EVALUATION MODE above.
  Step 6 — DECIDE:      Assign final scores. Every score must be traceable to evidence from Steps 1-5.

Do NOT skip steps. Do NOT guess. Do NOT hallucinate projects or skills not in the data.
"""


def build_cot_prefix(mode: ThinkingMode) -> str:
    """
    Construct the full cognitive prefix to prepend to any agent prompt.
    Includes the thinking mode instructions + chain-of-thought protocol.
    """
    return get_thinking_mode_instructions(mode) + CHAIN_OF_THOUGHT_PREFIX


# ── Self-Reflection Layer ─────────────────────────────────────────────────────

class SelfReflectionReview(BaseModel):
    """Structured output of the self-reflection pass."""
    is_consistent: bool = Field(
        description="True if the initial output is internally consistent (scores align with evidence)."
    )
    contradictions_found: list[str] = Field(
        default=[],
        description="Any contradictions detected, e.g. 'High technical score but no verified projects'."
    )
    missed_signals: list[str] = Field(
        default=[],
        description="Important signals from the resume that were not considered."
    )
    score_adjustments: dict[str, Any] = Field(
        default={},
        description="Suggested adjustments as {field_name: new_value}. Only include fields that should change."
    )
    reflection_summary: str = Field(
        description="One-sentence verdict: Was the initial output correct and complete?"
    )


SELF_REFLECTION_PROMPT_TEMPLATE = """
You are a QUALITY ASSURANCE REVIEWER for an AI hiring system.

You have just received the INITIAL AGENT OUTPUT below. Your task is to critically review it.

Ask yourself:
  1. "Is this decision consistent with the evidence in the resume?"
  2. "Did the agent miss any important signals (positive OR negative)?"
  3. "Do the numerical scores align with the written justifications?"
  4. "Are there any contradictions between different fields?"

INITIAL AGENT OUTPUT (JSON):
{initial_output}

ORIGINAL RESUME TEXT:
{resume_text}

JOB REQUIREMENT:
{job_requirement}

EVALUATION MODE APPLIED: {mode}

Be honest and critical. If the output looks correct, say so. If not, identify specific issues and suggest corrected field values.
"""


async def run_self_reflection(
    llm_instance,
    initial_output,
    resume_text: str,
    job_requirement: str,
    mode: ThinkingMode,
) -> SelfReflectionReview:
    """
    Runs a second LLM pass to self-review an agent's initial output.

    Args:
        llm_instance: A configured ChatGoogleGenerativeAI instance.
        initial_output: The Pydantic model output from the first agent pass.
        resume_text: Original resume text.
        job_requirement: Full job requirement string.
        mode: The ThinkingMode used in the first pass.

    Returns:
        SelfReflectionReview with any detected contradictions and adjustments.
    """
    try:
        structured_reviewer = llm_instance.with_structured_output(SelfReflectionReview)

        # Serialise initial output to JSON string for the prompt
        initial_json = initial_output.model_dump_json(indent=2) if hasattr(initial_output, "model_dump_json") else str(initial_output)

        prompt = SELF_REFLECTION_PROMPT_TEMPLATE.format(
            initial_output=initial_json,
            resume_text=resume_text[:4000],  # cap to avoid token overflow
            job_requirement=job_requirement[:1500],
            mode=mode.value.upper(),
        )

        review: SelfReflectionReview = await structured_reviewer.ainvoke(prompt)

        if review.contradictions_found:
            logger.info(
                f"Self-reflection found {len(review.contradictions_found)} contradiction(s): "
                f"{review.contradictions_found}"
            )

        return review

    except Exception as e:
        logger.warning(f"Self-reflection pass failed (non-critical): {e}")
        # Return a neutral review — don't break the pipeline if reflection fails
        return SelfReflectionReview(
            is_consistent=True,
            reflection_summary="Self-reflection unavailable — initial output accepted as-is.",
        )


def apply_reflection_adjustments(initial_output, review: SelfReflectionReview):
    """
    Apply score adjustments from the self-reflection review back onto the initial output object.
    Only modifies fields that exist on the output model and are included in score_adjustments.

    Returns the (possibly modified) output object.
    """
    if not review.score_adjustments:
        return initial_output

    for field_name, new_value in review.score_adjustments.items():
        if hasattr(initial_output, field_name):
            try:
                setattr(initial_output, field_name, new_value)
                logger.info(f"Self-reflection adjusted '{field_name}' → {new_value}")
            except Exception as e:
                logger.warning(f"Could not apply adjustment for '{field_name}': {e}")

    return initial_output


# ── Adaptive Prompting ────────────────────────────────────────────────────────

SENIORITY_ADAPTIVE_INSTRUCTIONS: dict[str, str] = {
    "junior": """
ROLE SENIORITY: JUNIOR
  • Weight foundational concepts over production experience.
  • Strong academic projects and side projects count significantly.
  • Assess trainability and eagerness to learn.
""",
    "mid": """
ROLE SENIORITY: MID-LEVEL
  • Expect at least 1-2 real-world or production projects.
  • Balance between technical depth and soft skills.
  • Must show ability to work independently.
""",
    "senior": """
ROLE SENIORITY: SENIOR
  • Production systems, architecture decisions, and mentorship history are REQUIRED.
  • Tutorial or academic projects alone are INSUFFICIENT.
  • Assess problem-solving at scale and design thinking.
""",
    "lead": """
ROLE SENIORITY: LEAD / PRINCIPAL
  • Technical leadership, team management, and system design at org level are CRITICAL.
  • Evaluate business impact of past decisions, not just code quality.
  • Strong communication and documented decision-making track records are expected.
""",
}


def build_adaptive_prompt_context(
    seniority_level: str,
    past_feedback_summary: Optional[str] = None,
) -> str:
    """
    Build an adaptive context block to prepend to agent prompts.

    Args:
        seniority_level: One of 'junior', 'mid', 'senior', 'lead'.
        past_feedback_summary: Optional string summarising past HR feedback patterns
                               retrieved from the memory/feedback system.

    Returns:
        A formatted string to inject into the agent prompt.
    """
    level = seniority_level.lower().strip()
    seniority_block = SENIORITY_ADAPTIVE_INSTRUCTIONS.get(level, SENIORITY_ADAPTIVE_INSTRUCTIONS["mid"])

    feedback_block = ""
    if past_feedback_summary:
        feedback_block = f"""
LEARNED FROM PAST DECISIONS (Memory-Aware Context):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{past_feedback_summary}

Apply these learnings when interpreting similar signals in the current candidate's profile.
"""

    return seniority_block + feedback_block
