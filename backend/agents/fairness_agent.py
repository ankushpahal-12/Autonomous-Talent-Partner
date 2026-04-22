"""
fairness_agent.py — Adversarial Fairness Auditor
=================================================
An independent LLM agent whose ENTIRE job is to challenge the Lead Agent's
decision to detect and mitigate potential hidden biases.

Key rules:
- It can ONLY upgrade a 'reject' → 'further_interview'. Never downgrades.
- When it overrules, the original decision is preserved in the report so HR is ALWAYS informed.
- The rejection feedback chain downstream is skipped if this agent overrules.

Biases it actively looks for:
1. Degree bias (penalizing lack of CS degree despite strong self-taught evidence)
2. Employment gap bias (penalizing gaps without investigating reason)
3. Company prestige bias (only praised because of FAANG, not actual skill)
4. Non-traditional path bias (bootcamp, self-taught, career switcher)
5. Name/location discrimination signals in the reasoning
"""

import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class FairnessAuditResult(BaseModel):
    """Result of the Adversarial Fairness Agent's audit."""
    overruled: bool = Field(
        description="True if the Fairness Agent is changing the Lead Agent's decision."
    )
    original_decision: str = Field(
        description="The original decision made by the Lead Agent (hire/reject/further_interview)."
    )
    final_decision: str = Field(
        description="The decision AFTER the fairness audit. Will differ from original only if overruled=True."
    )
    bias_types_detected: List[str] = Field(
        default_factory=list,
        description="List of specific bias types found, e.g. ['Degree bias', 'Gap penalization']"
    )
    bias_evidence: List[str] = Field(
        default_factory=list,
        description="Specific quotes or reasoning from the Lead Agent that triggered the bias flag."
    )
    overrule_justification: str = Field(
        description="If overruled=True: detailed explanation of WHY the decision was overruled. "
                    "If overruled=False: confirmation that no credible bias was detected."
    )
    audit_narrative: str = Field(
        description="1-3 sentence HR-ready summary. If overruled, tells HR what happened and why the candidate deserves a second look."
    )
    confidence: float = Field(
        description="Auditor's confidence in its assessment (0.0 to 1.0)."
    )


# ============================================================================
# Agent Function
# ============================================================================

async def run_fairness_agent(
    original_decision: str,
    decision_explanation: str,
    resume_text: str,
    screener_report: Optional[str] = None,
    tech_report: Optional[str] = None,
    flight_risk_data: Optional[dict] = None,
) -> FairnessAuditResult:
    """
    Challenges the Lead Agent's decision for potential bias.

    SAFETY RULE: Can only change 'reject' → 'further_interview'.
    Cannot downgrade 'hire' to 'reject'.

    Args:
        original_decision: The decision from the Lead Agent ('hire'/'reject'/'further_interview').
        decision_explanation: The Lead Agent's detailed explanation text.
        resume_text: The full candidate resume for context.
        screener_report: Optional screener agent report for baseline data.
        tech_report: Optional tech agent report for skill verification.
        flight_risk_data: Optional flight risk analysis (to check overqualification bias).

    Returns:
        FairnessAuditResult with overrule status and full audit trail.
    """
    key = settings.get_key_for_agent(9)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=key,
        transport="rest",
        temperature=0.1,  # Low temp for consistent, principled auditing
        max_retries=3,
        timeout=45
    )
    structured_llm = llm.with_structured_output(FairnessAuditResult)

    # Build context for the auditor
    context_parts = [f"=== LEAD AGENT DECISION ===\n{original_decision.upper()}"]
    context_parts.append(f"\n=== LEAD AGENT EXPLANATION ===\n{decision_explanation}")
    context_parts.append(f"\n=== CANDIDATE RESUME ===\n{resume_text[:2000]}")
    if screener_report:
        context_parts.append(f"\n=== SCREENER REPORT ===\n{screener_report[:800]}")
    if tech_report:
        context_parts.append(f"\n=== TECH REPORT ===\n{tech_report[:800]}")

    context = "\n".join(context_parts)

    # Define the critical constraint based on the decision type
    if original_decision.lower() in ("hire", "further_interview"):
        overrule_instruction = (
            "The Lead Agent recommended HIRE or FURTHER_INTERVIEW. "
            "Your job is to check if this decision was contaminated by PRESTIGE BIAS "
            "(e.g., hired only because of a FAANG name and not genuine technical skill). "
            "YOU CANNOT CHANGE a hire to a reject. Set overruled=False unless prestige bias is overwhelming. "
            "In all cases, set final_decision to the same as original_decision."
        )
    else:
        overrule_instruction = (
            "The Lead Agent recommended REJECT. "
            "Your MISSION is to act as the candidate's last advocate. "
            "Analyze whether this rejection is rooted in any of the biases listed below. "
            "If you find CREDIBLE evidence of bias, you MUST set overruled=True and set final_decision='further_interview'. "
            "You are their ONLY safeguard. Be willing to overrule if the evidence supports it."
        )

    prompt = f"""You are the Adversarial Fairness Auditor for an AI hiring system. Your role is described below.

MISSION: {overrule_instruction}

BIASES TO ACTIVELY HUNT FOR:
1. **Degree Bias**: Penalizing lack of a formal CS degree when the candidate has equivalent self-taught experience (GitHub, side projects, certifications, bootcamp)
2. **Employment Gap Bias**: Penalizing an employment gap without acknowledging valid reasons (illness, family, startup failure, personal projects)
3. **Prestige Bias**: Over-crediting experience from a famous company (FAANG) when actual project impact is shallow, or the reverse — under-crediting strong work at unknown companies
4. **Non-Traditional Path Bias**: Penalizing a career switcher, bootcamp graduate, or self-taught developer despite demonstrated skills
5. **Overqualification Penalization Bias**: Flagging someone as overqualified merely for having advanced titles, rather than assessing their actual motivation for the role

STRICT OUTPUT RULES:
- If original_decision = 'reject' AND you find credible bias: set overruled=True, final_decision='further_interview'
- If original_decision = 'reject' AND you find NO credible bias: set overruled=False, final_decision='reject'
- If original_decision = 'hire' or 'further_interview': NEVER set overruled=True. Set final_decision to the same value.
- bias_evidence must contain SPECIFIC QUOTES or REASONING from the Lead Agent's explanation — not generic claims
- Do NOT overrule just because you want to be nice. You need EVIDENCE.
- confidence reflects how sure you are. If a rejection explanation is thin/vague, that itself is a signal.

ALL CONTEXT FOR YOUR AUDIT:
{context}
"""

    try:
        result = await structured_llm.ainvoke(prompt)

        # HARD SAFETY OVERRIDE: Prevent any downgrade from hire/interview → reject
        if original_decision.lower() in ("hire", "further_interview"):
            if result.final_decision.lower() == "reject":
                result.final_decision = original_decision
                result.overruled = False
                logger.warning("FairnessAgent safety override: Cannot downgrade a hire to reject.")

        # HARD SAFETY OVERRIDE: If overrule on reject, final_decision MUST be further_interview
        if original_decision.lower() == "reject" and result.overruled:
            result.final_decision = "further_interview"

        if result.overruled:
            logger.info(f"[FairnessAgent] OVERRULED: '{original_decision}' → '{result.final_decision}'. Bias: {result.bias_types_detected}")
        else:
            logger.info(f"[FairnessAgent] Decision '{original_decision}' confirmed. No credible bias detected.")

        return result

    except Exception as e:
        logger.error(f"FairnessAgent failed: {e}")
        # On failure, return a safe non-overruling result so the pipeline doesn't break
        return FairnessAuditResult(
            overruled=False,
            original_decision=original_decision,
            final_decision=original_decision,
            bias_types_detected=[],
            bias_evidence=[],
            overrule_justification="Fairness audit could not be completed due to a system error. Manual review is recommended.",
            audit_narrative="Automated fairness audit encountered an error. HR should manually review this decision for potential bias.",
            confidence=0.0
        )
