"""
Tech Agent — upgraded with Thinking Modes, Chain-of-Thought, and Self-Reflection.
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


class SkillEvaluation(BaseModel):
    skill: str = Field(description="Name of the skill")
    proficiency_score: int = Field(description="Proficiency percentage out of 100 based on resume depth and usage")


class TechReport(BaseModel):
    tech_stack_match: Literal["high", "medium", "low"] = Field(description="Match between candidate tech stack and requirement")
    system_design_experience: str = Field(description="Brief note on system design experience or N/A", default="N/A")
    problem_solving_indicators: str = Field(description="Brief note on problem solving or N/A", default="N/A")
    technical_red_flags: List[str] = Field(description="Any technical red flags found", default=[])
    key_technologies: List[str] = Field(description="List of key technologies found", default=[])
    evaluated_skills: List[SkillEvaluation] = Field(
        description="Evaluate up to 8 top skills providing a deterministic proficiency percentage (1-100) based on their resume.",
        default=[]
    )
    project_complexity_score: int = Field(description="1-10 overall score for project complexity and relevance", default=5)
    project_category: Literal["Professional/Industry", "Startup/High Growth", "Student/Academic", "Tutorial/Generic"] = Field(
        description="Classification of most significant projects"
    )
    project_verification_note: str = Field(description="Brief note on projects (boosted by external evidence if provided)", default="N/A")
    summary: str = Field(description="Technical summary of projects and tech expertise", default="N/A")
    technical_fit_score: int = Field(description="1-10 overall technical suitability")
    potential_score: int = Field(description="1-10 score for candidate growth potential and learning ability", default=5)
    growth_indicators: List[str] = Field(
        description="Specific indicators of rapid learning or domain adaptability (e.g. 'Project built without prior exp')",
        default=[]
    )
    reasoning_trace: str = Field(
        description="A brief internal reasoning trace summarising how you stepped through the CoT protocol (Steps 1-6).",
        default=""
    )


async def run_tech_agent(
    resume_text: str,
    job_requirement: str,
    external_projects: Optional[List[dict]] = None,
    mode: ThinkingMode = ThinkingMode.BALANCED,
    seniority_level: str = "mid",
    past_feedback_summary: Optional[str] = None,
    enable_self_reflection: bool = True,
) -> TechReport:
    """
    Evaluates the depth and complexity of technical projects mentioned in the resume.

    Args:
        resume_text: Full resume text.
        job_requirement: Full job description / requirements string.
        external_projects: Optional list of GitHub repo metadata for verification.
        mode: ThinkingMode — STRICT, BALANCED, or POTENTIAL.
        seniority_level: 'junior', 'mid', 'senior', or 'lead'.
        past_feedback_summary: Optional memory context from past similar candidates.
        enable_self_reflection: Whether to run the self-review pass after initial output.

    Returns:
        TechReport (possibly adjusted by self-reflection).
    """
    key = settings.get_key_for_agent(2)
    if not key:
        import logging
        logging.warning("Technical Agent started without a valid API key.")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=key,
        transport="rest",
        temperature=0.2,
        max_retries=5,
        timeout=60,
    )
    structured_llm = llm.with_structured_output(TechReport)

    # ── Build Cognitive Prefix ────────────────────────────────────────────────
    cognitive_prefix = build_cot_prefix(mode)
    adaptive_context = build_adaptive_prompt_context(seniority_level, past_feedback_summary)

    # ── Build External Evidence Block ─────────────────────────────────────────
    external_context = ""
    if external_projects:
        external_context = "\nEXTERNAL PROJECT EVIDENCE (GitHub Analysis):\n"
        for repo in external_projects:
            external_context += f"- Repo: {repo.get('name')} (Stars: {repo.get('stars')}, Forks: {repo.get('forks')})\n"
            external_context += f"  README Snippet: {repo.get('readme', '')[:1000]}\n"

    prompt = f"""{cognitive_prefix}
{adaptive_context}

ANTI-KEYWORD STUFFING RULES:
1. Explicitly check if the listed 'skills' appear in the 'projects' or 'experience' descriptions.
2. If a skill is ONLY in the list and NOT used in any project/context, treat it as "unverified" and reduce its score.
3. If EXTERNAL PROJECT EVIDENCE is provided, use it to VERIFY the complexity and actual usage of these skills.
4. Boost the project_complexity_score if the code/README shows high technical depth.
5. PROJECT CLASSIFICATION (STRICT):
   - Industry/Professional: Real-world apps, production deployments, complex architecture.
   - Startup/High Growth: Fast-paced, feature-rich, innovative.
   - Student/Academic: Simple CRUDs, college assignments, library systems.
   - Tutorial/Generic: e.g., To-Do list, calculator, weather app from a course.

6. POTENTIAL & GROWTH (CRITICAL):
   - If a candidate built a complex project in a language they just learned, increase potential_score.
   - Identify "Trainability": If they are strong in ML fundamentals but weak in DL, they are "Trainable".
   - Look for self-learning indicators (e.g., non-academic projects, heavy GitHub activity in new field).

7. REASONING TRACE: Populate the reasoning_trace field with a 3-5 sentence summary of how you applied Steps 1-6.

Analyze the candidate's resume against the technical requirements:
{job_requirement}

CANDIDATE DATA:
RESUME: {resume_text}
{external_context}

Provide a structured technical analysis based on VERIFIED usage only.
"""

    # ── Initial Agent Pass ────────────────────────────────────────────────────
    report: TechReport = await structured_llm.ainvoke(prompt)

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
