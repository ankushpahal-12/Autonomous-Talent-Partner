"""
Agent Orchestration Intelligence Layer
=================================================
Provides three major upgrades for inter-agent coordination:

1. ToolSelectionAdvisor  — Agents decide WHICH MCP tools they actually need
                           instead of blindly calling everything.

2. CrossAgentDebate      — When two agents sharply contradict each other,
                           a lightweight debate loop resolves the conflict.

3. ErrorCorrectionLayer  — If the fuzzy/deterministic score heavily contradicts
                           a generative agent score, the pipeline flags or re-checks.
"""

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 1. TOOL SELECTION INTELLIGENCE
# ─────────────────────────────────────────────────────────────────────────────

AVAILABLE_MCP_TOOLS = {
    "rag":            "Retrieve job requirement context from vector store for semantic comparison.",
    "knowledge_graph":"Query Neo4j for related skills and domain relationships.",
    "vector_search":  "Semantic similarity search across the candidate pool.",
    "github_scraper": "Fetch live GitHub repository data to verify project claims.",
    "linkedin_scraper":"Fetch LinkedIn profile data to verify experience claims.",
    "mongo_lookup":   "Query MongoDB for structured data or past hiring rules.",
}


class ToolSelectionDecision(BaseModel):
    """Structured output of the tool selection advisor."""
    tools_needed: List[str] = Field(
        description="List of tool keys the agent actually needs from the available tools."
    )
    reasoning: str = Field(
        description="Brief justification for why each selected tool is necessary."
    )
    can_proceed_without_tools: bool = Field(
        default=False,
        description="True if the agent has enough data from the resume alone and no tools are needed."
    )


TOOL_SELECTION_PROMPT = """
You are an intelligent Tool Selection Advisor for an AI hiring system.

An agent is about to evaluate a candidate. Before blindly calling every tool,
decide which tools are actually necessary given the available data.

AVAILABLE TOOLS:
{tool_list}

CANDIDATE RESUME SUMMARY:
{resume_summary}

JOB REQUIREMENT SUMMARY:
{requirement_summary}

AGENT TASK:
{agent_task}

RULES:
- Only select tools that would materially change the output.
- If the resume has enough detail for the agent's task, set can_proceed_without_tools = True.
- Do NOT select linkedin_scraper if no LinkedIn URL is present in the resume.
- Do NOT select github_scraper if no GitHub URL or project links are present.
- Select rag or knowledge_graph only if skill gap analysis is needed.

Respond with a ToolSelectionDecision.
"""


async def decide_tools_needed(
    resume_text: str,
    job_requirement: str,
    agent_task: str,
    llm_key_index: int = 0,
) -> ToolSelectionDecision:
    """
    Ask the LLM whether it actually needs MCP tools or can proceed directly.

    Args:
        resume_text: Full resume text.
        job_requirement: Job requirement string.
        agent_task: A short description of what the calling agent needs to do.
        llm_key_index: API key index to use.

    Returns:
        ToolSelectionDecision listing required tools and reasoning.
    """
    try:
        key = settings.get_key_for_agent(llm_key_index)
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=key,
            transport="rest",
            temperature=0.0,
            timeout=20,
        )
        structured = llm.with_structured_output(ToolSelectionDecision)

        tool_list = "\n".join(
            f"  - {k}: {v}" for k, v in AVAILABLE_MCP_TOOLS.items()
        )

        prompt = TOOL_SELECTION_PROMPT.format(
            tool_list=tool_list,
            resume_summary=resume_text[:1500],
            requirement_summary=job_requirement[:800],
            agent_task=agent_task,
        )

        decision: ToolSelectionDecision = await structured.ainvoke(prompt)
        logger.info(
            f"[ToolSelection] Agent task='{agent_task[:40]}...' → "
            f"tools={decision.tools_needed}, skip={decision.can_proceed_without_tools}"
        )
        return decision

    except Exception as e:
        logger.warning(f"[ToolSelection] Advisor failed (non-critical): {e}")
        # Safe fallback — proceed without tools
        return ToolSelectionDecision(
            tools_needed=[],
            reasoning="Tool selection unavailable — proceeding without MCP tools.",
            can_proceed_without_tools=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
# 2. CROSS-AGENT DEBATE SYSTEM
# ─────────────────────────────────────────────────────────────────────────────

CONTRADICTION_THRESHOLD = 3  # Score difference (out of 10) that triggers a debate


class DebateVerdict(BaseModel):
    """Final resolved verdict after agent debate."""
    agreed_score: int = Field(
        description="The resolved score (1–10) after debate. Must be between the two positions."
    )
    winner: str = Field(
        description="Which agent's position is closer to truth: 'agent_a', 'agent_b', or 'split'."
    )
    resolution_reasoning: str = Field(
        description="Step-by-step explanation of why this score was chosen over the alternatives."
    )
    key_evidence_used: List[str] = Field(
        default=[],
        description="Specific resume signals that tipped the decision."
    )


DEBATE_PROMPT = """
You are a NEUTRAL ARBITRATOR for an AI hiring panel.

Two agents have evaluated the same candidate and sharply disagree.
Your job: review both positions and produce a fair, evidence-backed resolution.

AGENT A — {agent_a_name}
  Score: {score_a}/10
  Summary: {summary_a}

AGENT B — {agent_b_name}
  Score: {score_b}/10
  Summary: {summary_b}

CANDIDATE RESUME:
{resume_text}

JOB REQUIREMENT:
{job_requirement}

ARBITRATION RULES:
1. The resolved score must be between {score_a} and {score_b}.
2. Base the decision solely on verifiable resume evidence.
3. If one agent raises a red flag not mentioned by the other, investigate it.
4. State which agent's position is better supported ('agent_a', 'agent_b', or 'split').

Produce a DebateVerdict.
"""


async def run_cross_agent_debate(
    agent_a_name: str,
    score_a: int,
    summary_a: str,
    agent_b_name: str,
    score_b: int,
    summary_b: str,
    resume_text: str,
    job_requirement: str,
    llm_key_index: int = 0,
) -> Optional[DebateVerdict]:
    """
    Trigger a debate when two agents disagree by more than CONTRADICTION_THRESHOLD.

    Returns:
        DebateVerdict if a debate was warranted and resolved, None if scores are aligned.
    """
    diff = abs(score_a - score_b)
    if diff < CONTRADICTION_THRESHOLD:
        logger.debug(
            f"[Debate] {agent_a_name} vs {agent_b_name}: diff={diff} < threshold, no debate needed."
        )
        return None

    logger.info(
        f"[Debate] TRIGGERED: {agent_a_name}({score_a}) vs {agent_b_name}({score_b}) "
        f"— diff={diff}"
    )

    try:
        key = settings.get_key_for_agent(llm_key_index)
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=key,
            transport="rest",
            temperature=0.1,
            timeout=45,
        )
        arbitrator = llm.with_structured_output(DebateVerdict)

        prompt = DEBATE_PROMPT.format(
            agent_a_name=agent_a_name,
            score_a=score_a,
            summary_a=summary_a,
            agent_b_name=agent_b_name,
            score_b=score_b,
            summary_b=summary_b,
            resume_text=resume_text[:3000],
            job_requirement=job_requirement[:1000],
        )

        verdict: DebateVerdict = await arbitrator.ainvoke(prompt)
        logger.info(
            f"[Debate] Resolved: {agent_a_name} vs {agent_b_name} → "
            f"score={verdict.agreed_score}, winner={verdict.winner}"
        )
        return verdict

    except Exception as e:
        logger.warning(f"[Debate] Arbitration failed (non-critical): {e}")
        # Safe fallback — average the two scores
        avg = (score_a + score_b) // 2
        return DebateVerdict(
            agreed_score=avg,
            winner="split",
            resolution_reasoning=f"Arbitration unavailable. Using average of {score_a} and {score_b}.",
            key_evidence_used=[],
        )


# ─────────────────────────────────────────────────────────────────────────────
# 3. ERROR CORRECTION LAYER
# ─────────────────────────────────────────────────────────────────────────────

# Thresholds for contradiction detection
FUZZY_VS_AGENT_THRESHOLD = 25   # Percentage points difference
FLAG_FOR_REVIEW_THRESHOLD = 35  # Above this → flag for human review


class ErrorCorrectionResult(BaseModel):
    """Output of the error correction check."""
    contradiction_detected: bool
    severity: str = Field(description="'none', 'moderate', or 'severe'")
    fuzzy_score: float
    agent_score_normalized: float
    gap: float
    flag_for_human_review: bool
    correction_notes: List[str] = Field(default=[])
    recommended_final_score: Optional[float] = None


def run_error_correction(
    fuzzy_score: float,           # 0–100 from deterministic fuzzy engine
    agent_composite_score: float, # 1–10 from generative agents (will be normalised to 0-100)
    agent_summaries: Dict[str, str],
) -> ErrorCorrectionResult:
    """
    Compare deterministic fuzzy score vs. generative agent composite score.
    Flag large contradictions and optionally recommend a blended final score.

    Args:
        fuzzy_score: 0–100 fuzzy logic score.
        agent_composite_score: 1–10 agent score (normalised internally to 0–100).
        agent_summaries: Dict of {agent_name: summary_text} for logging context.

    Returns:
        ErrorCorrectionResult with flag and correction notes.
    """
    agent_normalised = (agent_composite_score / 10.0) * 100.0
    gap = abs(fuzzy_score - agent_normalised)

    if gap < FUZZY_VS_AGENT_THRESHOLD:
        severity = "none"
        contradiction = False
        flag_review = False
        notes = []
    elif gap < FLAG_FOR_REVIEW_THRESHOLD:
        severity = "moderate"
        contradiction = True
        flag_review = False
        notes = [
            f"Fuzzy score ({fuzzy_score:.1f}) and agent composite ({agent_normalised:.1f}) "
            f"disagree by {gap:.1f} points.",
            "Consider reviewing agent summaries for missed signals.",
        ]
    else:
        severity = "severe"
        contradiction = True
        flag_review = True
        notes = [
            f"SEVERE CONTRADICTION: Fuzzy={fuzzy_score:.1f} vs Agent={agent_normalised:.1f} "
            f"(gap={gap:.1f} pts).",
            "Flagged for human review. One or more agents may have missed critical evidence.",
        ]

    # Log a summary of which agents contributed
    if contradiction:
        for name, summary in agent_summaries.items():
            notes.append(f"  [{name}]: {summary[:120]}")
        logger.warning(
            f"[ErrorCorrection] {severity.upper()} contradiction — "
            f"fuzzy={fuzzy_score:.1f}, agent_norm={agent_normalised:.1f}, gap={gap:.1f}"
        )

    # Recommended blended score: weighted average (fuzzy=40%, agents=60%)
    recommended = round((fuzzy_score * 0.40) + (agent_normalised * 0.60), 1) if contradiction else None

    return ErrorCorrectionResult(
        contradiction_detected=contradiction,
        severity=severity,
        fuzzy_score=fuzzy_score,
        agent_score_normalized=agent_normalised,
        gap=gap,
        flag_for_human_review=flag_review,
        correction_notes=notes,
        recommended_final_score=recommended,
    )
