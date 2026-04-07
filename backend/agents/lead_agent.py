import asyncio
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from .screener_agents import run_screener_agent, ScreenerReport
from .tech_agent import run_tech_agent, TechReport
from .culture_agent import run_culture_agent, CultureReport
from services.neo4j_service import kg_service
from services.decision_service import run_decision_chain, run_rejection_chain
from services.vector_parser import evaluate_candidate_with_rag

class CompleteAgentReport(BaseModel):
    screener: ScreenerReport
    tech: TechReport
    culture: CultureReport
    rag_reasoning: Optional[str] = None       # RAG-grounded context analysis
    final_decision: dict
    rejection_feedback: Optional[dict] = None

async def run_full_candidate_review(
    resume_text: str,
    job_requirement_text: str,
    requirement_id: Optional[str] = None     # Pass this to enable RAG retrieval
) -> CompleteAgentReport:
    """
    Orchestrates sub-agents and synthesizes results using:
    - RAG (retrieves grounded job requirement context from ChromaDB)
    - Knowledge Graph enrichment (Neo4j / fallback)
    - Parallel multi-agent evaluation (Screener, Tech, Culture)
    - LangChain Decision + Rejection chains
    """

    # === STAGE 1: RAG Context Retrieval ===
    # Run RAG lookup in parallel with sub-agents when a requirement_id is provided
    rag_task = None
    if requirement_id:
        rag_task = evaluate_candidate_with_rag(resume_text, requirement_id)

    # === STAGE 2: Run Sub-Agents in Parallel ===
    screener_task = run_screener_agent(resume_text, job_requirement_text)
    tech_task     = run_tech_agent(resume_text, job_requirement_text)
    culture_task  = run_culture_agent(resume_text, job_requirement_text)

    # Gather all async tasks together for maximum speed
    if rag_task:
        screener_res, tech_res, culture_res, rag_reasoning = await asyncio.gather(
            screener_task, tech_task, culture_task, rag_task
        )
    else:
        screener_res, tech_res, culture_res = await asyncio.gather(
            screener_task, tech_task, culture_task
        )
        rag_reasoning = None

    # === STAGE 3: Knowledge Graph Enrichment via Neo4j ===
    found_skills = tech_res.key_technologies or []
    kg_insights: Dict[str, list] = {}
    for skill in found_skills[:5]:
        related = kg_service.get_related_skills(skill)
        if related:
            kg_insights[skill] = related

    enriched_tech_report = f"""
    Technical Findings (Structured):
    {tech_res.model_dump_json()}

    Knowledge Graph Insights (related skills detected):
    {kg_insights}
    """

    # === STAGE 4: Build Requirements Context for Decision Chain ===
    # If RAG returned grounded context, embed it into the requirements block
    requirements_context = job_requirement_text
    if rag_reasoning:
        requirements_context = f"""
JOB REQUIREMENT (original):
{job_requirement_text}

RAG CONTEXT ANALYSIS (retrieved from indexed job documents):
{rag_reasoning}
        """.strip()

    # === STAGE 5: Final Decision Chain ===
    final_decision_result = await run_decision_chain(
        screener_report=screener_res.model_dump_json(),
        tech_report=enriched_tech_report,
        culture_report=culture_res.model_dump_json(),
        requirements_context=requirements_context
    )

    # === STAGE 6: Rejection Feedback Chain (only if rejected) ===
    rejection_feedback = None
    decision_value = final_decision_result.get("decision", "").lower()
    if decision_value in ("reject", "rejected"):
        rejection_feedback = await run_rejection_chain(
            decision_explanation=final_decision_result.get("explanation", ""),
            resume_details=resume_text
        )

    return CompleteAgentReport(
        screener=screener_res,
        tech=tech_res,
        culture=culture_res,
        rag_reasoning=rag_reasoning,
        final_decision=final_decision_result,
        rejection_feedback=rejection_feedback
    )
