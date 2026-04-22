"""
Lead agent (conductor) that orchestrates all sub-agents for comprehensive candidate evaluation.
Features:
- Parallel execution of independent agents (3x faster)
- Automatic error recovery and fallbacks
- Comprehensive logging and performance tracking
- Input validation and caching
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List, Tuple

from pydantic import BaseModel, Field

from .screener_agents import run_screener_agent, ScreenerReport
from .tech_agent import run_tech_agent, TechReport
from .culture_agent import run_culture_agent, CultureReport
from .extracurricular_agent import run_extracurricular_agent, ExtracurricularReport
from .hackathon_agent import run_hackathon_agent, HackathonReport
from .code_quality_agent import run_code_quality_agent, CodeQualityReport
from .skill_counter import run_skill_counter_agent, SkillCounterReport
from .agent_utils import async_retry, RetryConfig, track_performance, get_fallback_response, CircuitBreaker
from .agent_cache import cache_agent_result
from .agent_validators import validate_resume_text, validate_job_requirement
from .scraper_agent import calculate_external_intelligence_score, save_external_evaluation_to_db
from .behavioral_agent import run_behavioral_agent, BehavioralProfile
from .fairness_agent import run_fairness_agent, FairnessAuditResult
from .agent_thinking import ThinkingMode
from .agent_debate import run_cross_agent_debate, run_error_correction, DebateVerdict, ErrorCorrectionResult
from  services.decision_service import run_decision_chain, run_rejection_chain, run_enhanced_decision_chain, run_comprehensive_analysis, run_fuzzy_aware_decision_chain
from  services.vector_parser import evaluate_candidate_with_rag
from  services.retention_service import analyze_flight_risk, FlightRiskReport
from  services.elo_ranking_service import calculate_elo_ranking, EloRankingResult
from  services.fuzzy_scoring import get_fuzzy_scorer, extract_raw_scores_from_reports
from  utils.mcp_client import mcp_client_manager

logger = logging.getLogger(__name__)

class CompleteAgentReport(BaseModel):
    """Complete candidate evaluation report from all agents."""
    screener: ScreenerReport
    tech: TechReport
    culture: CultureReport
    extracurricular: Optional[ExtracurricularReport] = None
    hackathon: Optional[HackathonReport] = None
    code_quality: Optional[CodeQualityReport] = None
    skill_counts: Optional[SkillCounterReport] = None
    rag_reasoning: Optional[str] = None
    external_intel: Optional[dict] = None
    external_evaluation: Optional[dict] = None
    # New Module Fields
    flight_risk: Optional[dict] = None
    behavioral_profile: Optional[dict] = None
    elo_ranking: Optional[dict] = None
    fuzzy_score_breakdown: Optional[dict] = None
    fairness_audit: Optional[dict] = None
    final_decision: dict
    rejection_feedback: Optional[dict] = None
    bias_audit_log: Optional[dict] = None
    performance_metrics: Optional[Dict[str, float]] = None
    # Phase 2 Fields
    debate_verdict: Optional[dict] = None
    error_correction: Optional[dict] = None
    thinking_mode: Optional[str] = None
    seniority_level: Optional[str] = None
    memory_injected: bool = False
@async_retry(config=RetryConfig(max_retries=2))
@track_performance
async def run_screener_with_fallback(
    fair_resume: str,
    job_req: str,
    mode: ThinkingMode = ThinkingMode.BALANCED,
    seniority_level: str = "mid",
    past_feedback_summary: Optional[str] = None,
) -> ScreenerReport:
    """Run screener agent with robustness and thinking mode support."""
    try:
        return await run_screener_agent(
            fair_resume, job_req,
            mode=mode,
            seniority_level=seniority_level,
            past_feedback_summary=past_feedback_summary,
        )
    except Exception as e:
        logger.error(f"Screener agent failed: {e}")
        fallback = get_fallback_response("screener", e)
        return ScreenerReport(**fallback)

@async_retry(config=RetryConfig(max_retries=2))
@track_performance
async def run_tech_with_fallback(
    resume: str,
    job_req: str,
    external_projects: Optional[List] = None,
    mode: ThinkingMode = ThinkingMode.BALANCED,
    seniority_level: str = "mid",
    past_feedback_summary: Optional[str] = None,
) -> TechReport:
    """Run tech agent with robustness and thinking mode support."""
    try:
        return await run_tech_agent(
            resume, job_req,
            external_projects=external_projects,
            mode=mode,
            seniority_level=seniority_level,
            past_feedback_summary=past_feedback_summary,
            enable_self_reflection=True,
        )
    except Exception as e:
        logger.error(f"Tech agent failed: {e}")
        fallback = get_fallback_response("tech", e)
        return TechReport(**fallback)

@async_retry(config=RetryConfig(max_retries=2))
@track_performance
async def run_culture_with_fallback(
    resume: str,
    job_req: str,
    mode: ThinkingMode = ThinkingMode.BALANCED,
    seniority_level: str = "mid",
    past_feedback_summary: Optional[str] = None,
) -> CultureReport:
    """Run culture agent with robustness and thinking mode support."""
    try:
        return await run_culture_agent(
            resume, job_req,
            mode=mode,
            seniority_level=seniority_level,
            past_feedback_summary=past_feedback_summary,
            enable_self_reflection=True,
        )
    except Exception as e:
        logger.error(f"Culture agent failed: {e}")
        fallback = get_fallback_response("culture", e)
        return CultureReport(**fallback)

@async_retry(config=RetryConfig(max_retries=2))
@track_performance
async def run_extracurricular_with_fallback(
    resume: str,
    mode: ThinkingMode = ThinkingMode.BALANCED,
    seniority_level: str = "mid",
    past_feedback_summary: Optional[str] = None,
) -> ExtracurricularReport:
    """Run extracurricular agent with robustness and thinking mode support."""
    try:
        return await run_extracurricular_agent(
            resume,
            mode=mode,
            seniority_level=seniority_level,
            past_feedback_summary=past_feedback_summary,
        )
    except Exception as e:
        logger.error(f"Extracurricular agent failed: {e}")
        fallback = get_fallback_response("extracurricular", e)
        return ExtracurricularReport(**fallback)

@async_retry(config=RetryConfig(max_retries=2))
@track_performance
async def run_hackathon_with_fallback(
    resume: str,
    mode: ThinkingMode = ThinkingMode.BALANCED,
    seniority_level: str = "mid",
    past_feedback_summary: Optional[str] = None,
) -> HackathonReport:
    """Run hackathon agent with robustness and thinking mode support."""
    try:
        return await run_hackathon_agent(
            resume,
            mode=mode,
            seniority_level=seniority_level,
            past_feedback_summary=past_feedback_summary,
        )
    except Exception as e:
        logger.error(f"Hackathon agent failed: {e}")
        fallback = get_fallback_response("hackathon", e)
        return HackathonReport(**fallback)

@async_retry(config=RetryConfig(max_retries=2))
@track_performance
async def run_code_quality_with_fallback(
    external_projects: Optional[List],
    mode: ThinkingMode = ThinkingMode.BALANCED,
    seniority_level: str = "mid",
    past_feedback_summary: Optional[str] = None,
) -> CodeQualityReport:
    """Run code quality agent with robustness and thinking mode support."""
    try:
        return await run_code_quality_agent(
            external_projects,
            mode=mode,
            seniority_level=seniority_level,
            past_feedback_summary=past_feedback_summary,
        )
    except Exception as e:
        logger.error(f"Code quality agent failed: {e}")
        fallback = get_fallback_response("code_quality", e)
        return CodeQualityReport(**fallback)

@async_retry(config=RetryConfig(max_retries=2))
@track_performance
async def run_behavioral_with_fallback(
    resume: str,
    github_readme: Optional[str] = None,
    mode: ThinkingMode = ThinkingMode.BALANCED,
    seniority_level: str = "mid",
    past_feedback_summary: Optional[str] = None,
) -> BehavioralProfile:
    """Run behavioral agent with robustness and thinking mode support."""
    try:
        return await run_behavioral_agent(
            resume,
            github_readme=github_readme,
            mode=mode,
            seniority_level=seniority_level,
            past_feedback_summary=past_feedback_summary,
            enable_self_reflection=True,
        )
    except Exception as e:
        logger.error(f"Behavioral agent failed: {e}")
        return BehavioralProfile(
            primary_archetype="Executor",
            archetype_confidence="Low",
            solo_vs_team_score=50,
            detail_vs_vision_score=50,
            risk_appetite="Balanced",
            communication_style="Mixed",
            leadership_signal="None Detected",
            team_fit_concerns=[],
            archetype_narrative="Behavioral profiling unavailable due to analysis error. Manual assessment recommended."
        )

@async_retry(config=RetryConfig(max_retries=2))
@track_performance
async def run_skill_counter_with_fallback(resume: str) -> SkillCounterReport:
    """Run skill counter agent with robustness."""
    try:
        return await run_skill_counter_agent(resume)
    except Exception as e:
        logger.error(f"Skill counter agent failed: {e}")
        return SkillCounterReport(skills=[])

async def run_raG_evaluation(resume: str, requirement_id: str) -> Optional[str]:
    """Run RAG evaluation with error handling."""
    try:
        logger.info("Starting RAG evaluation...")
        result = await evaluate_candidate_with_rag(resume, requirement_id)
        logger.info("RAG evaluation completed successfully")
        return result
    except Exception as e:
        logger.error(f"RAG evaluation failed: {e}")
        return None

# ============================================================================
# Main Orchestration Function
# ============================================================================

@track_performance
async def run_full_candidate_review(
    resume_text: str,
    job_requirement_text: str,
    requirement_id: Optional[str] = None,
    external_intel: Optional[dict] = None,
    parsed_data: Optional[dict] = None,
    request_id: Optional[str] = None,
    candidate_id: Optional[str] = None,
    save_to_db: bool = True,
    # Phase 1 & 2 Cognitive Parameters
    thinking_mode: ThinkingMode = ThinkingMode.BALANCED,
    seniority_level: str = "mid",
    past_feedback_summary: Optional[str] = None,
) -> CompleteAgentReport:
    """
    Orchestrates all sub-agents for comprehensive candidate evaluation.

    UPGRADES (Phases 1 & 2):
    - Thinking Modes (STRICT / BALANCED / POTENTIAL) passed to all cognitive agents
    - Seniority-aware adaptive prompting
    - Hybrid memory context injection (past similar candidates + learned rules)
    - Cross-Agent Debate when Tech vs Culture disagree sharply
    - Error Correction Layer when fuzzy score contradicts agent composite

    Args:
        resume_text: Full candidate resume
        job_requirement_text: Job requirement description
        requirement_id: Optional requirement ID for RAG
        external_intel: Optional GitHub/LinkedIn data
        parsed_data: Optional pre-parsed candidate data
        request_id: Optional request ID for tracking
        candidate_id: Optional candidate ID for database save
        save_to_db: Whether to save complete evaluation to database
        thinking_mode: Evaluation lens — STRICT, BALANCED, or POTENTIAL
        seniority_level: Role seniority — 'junior', 'mid', 'senior', 'lead'
        past_feedback_summary: Memory context string from hybrid memory system

    Returns:
        CompleteAgentReport with all agent findings, debate verdict, and error correction
    """
    
    pipeline_start = time.time()
    performance_metrics = {}
    
    # === STAGE 0: Input Validation ===
    logger.info(f"[{request_id}] Starting candidate review pipeline")
    
    resume_validation = validate_resume_text(resume_text)
    if not resume_validation.is_valid:
        logger.error(f"[{request_id}] Resume validation failed: {resume_validation.error_message}")
        raise ValueError(resume_validation.error_message)
    
    job_validation = validate_job_requirement(job_requirement_text)
    if not job_validation.is_valid:
        logger.error(f"[{request_id}] Job requirement validation failed: {job_validation.error_message}")
        raise ValueError(job_validation.error_message)
    
    logger.info(
        f"[{request_id}] Input validation passed",
        extra={
            "resume_tokens": resume_validation.token_count,
            "job_tokens": job_validation.token_count
        }
    )
    
    # === STAGE 1: Fair Hiring & Bias Reduction ===
    logger.info(f"[{request_id}] Applying fair hiring bias reduction")
    redact_res = await mcp_client_manager.invoke_tool(
        "lead_agent", "tool_fair_hiring_redact", {"resume_text": resume_text}
    )
    redaction_result = json.loads(redact_res) if redact_res else {"redacted_text": resume_text, "audit_log": {}}
    fair_resume_text = redaction_result.get("redacted_text", resume_text)
    bias_audit_log = redaction_result.get("audit_log", {})
    
    # === STAGE 2: System Memory Retrieval ===
    logger.info(f"[{request_id}] Retrieving role-specific learned rules via MCP")
    role_category = _detect_role_category(job_requirement_text)
    
    rules_resp = await mcp_client_manager.invoke_tool(
        "lead_agent", "tool_db_get_active_rules", {"role_category": role_category}
    )
    learned_rules = json.loads(rules_resp) if rules_resp and not rules_resp.startswith("{\"error") else []
    
    rule_prompt = ""
    if learned_rules:
        rule_prompt = "\nDYNAMIC SYSTEM RULES (Applied based on past HR feedback):\n"
        for rule in learned_rules:
            rule_pattern = rule.get("pattern", "")
            if rule_pattern:
                rule_prompt += f"- {rule_pattern}\n"
    
    logger.info(
        f"[{request_id}] Role category & rules loaded",
        extra={
            "role_category": role_category,
            "learned_rules_count": len(learned_rules)
        }
    )
    
    # === STAGE 3: Parallel Agent Execution ===
    logger.info(f"[{request_id}] Starting parallel agent execution")
    parallel_start = time.time()
    
    external_projects = external_intel.get("project_analysis") if external_intel else None
    
    # Execute independent agents in parallel
    # Dependency graph:
    # >>> Screener, Tech, Culture (can run in parallel)
    # >>> Extracurricular, Hackathon, Code Quality, Skill Counter (can run in parallel)
    
    screener_task = run_screener_with_fallback(
        fair_resume_text, job_requirement_text + rule_prompt,
        mode=thinking_mode,
        seniority_level=seniority_level,
        past_feedback_summary=past_feedback_summary,
    )
    tech_task = run_tech_with_fallback(
        resume_text, job_requirement_text + rule_prompt,
        external_projects=external_projects,
        mode=thinking_mode,
        seniority_level=seniority_level,
        past_feedback_summary=past_feedback_summary,
    )
    culture_task = run_culture_with_fallback(
        resume_text, job_requirement_text + rule_prompt,
        mode=thinking_mode,
        seniority_level=seniority_level,
        past_feedback_summary=past_feedback_summary,
    )
    
    # Run layer 1 in parallel
    screener_res, tech_res, culture_res = await asyncio.gather(
        screener_task, tech_task, culture_task,
        return_exceptions=True
    )
    
    # Handle exceptions
    if isinstance(screener_res, Exception):
        logger.error(f"Screener exception: {screener_res}")
        screener_res = ScreenerReport(**get_fallback_response("screener", screener_res))
    if isinstance(tech_res, Exception):
        logger.error(f"Tech exception: {tech_res}")
        tech_res = TechReport(**get_fallback_response("tech", tech_res))
    if isinstance(culture_res, Exception):
        logger.error(f"Culture exception: {culture_res}")
        culture_res = CultureReport(**get_fallback_response("culture", culture_res))
    
    # Layer 2: Optional agents (can always run in parallel)
    extra_task = run_extracurricular_with_fallback(
        resume_text,
        mode=thinking_mode,
        seniority_level=seniority_level,
        past_feedback_summary=past_feedback_summary,
    )
    hack_task = run_hackathon_with_fallback(
        resume_text,
        mode=thinking_mode,
        seniority_level=seniority_level,
        past_feedback_summary=past_feedback_summary,
    )
    code_task = run_code_quality_with_fallback(
        external_projects,
        mode=thinking_mode,
        seniority_level=seniority_level,
        past_feedback_summary=past_feedback_summary,
    )
    skill_task = run_skill_counter_with_fallback(resume_text)
    
    extra_res, hack_res, code_res, skill_res = await asyncio.gather(
        extra_task, hack_task, code_task, skill_task,
        return_exceptions=True
    )
    
    # Handle exceptions
    if isinstance(extra_res, Exception):
        logger.error(f"Extracurricular exception: {extra_res}")
        extra_res = ExtracurricularReport(**get_fallback_response("extracurricular", extra_res))
    if isinstance(hack_res, Exception):
        logger.error(f"Hackathon exception: {hack_res}")
        hack_res = HackathonReport(**get_fallback_response("hackathon", hack_res))
    if isinstance(code_res, Exception):
        logger.error(f"Code quality exception: {code_res}")
        code_res = CodeQualityReport(**get_fallback_response("code_quality", code_res))
    if isinstance(skill_res, Exception):
        logger.error(f"Skill counter exception: {skill_res}")
        skill_res = SkillCounterReport(skills=[])
    
    parallel_duration = time.time() - parallel_start
    performance_metrics["parallel_agents_ms"] = parallel_duration * 1000
    logger.info(f"[{request_id}] Parallel agents completed in {parallel_duration*1000:.0f}ms")

    # === STAGE 3.2: Cross-Agent Debate (Tech vs Culture) ===
    debate_verdict_dict: Optional[dict] = None
    try:
        tech_score   = getattr(tech_res,     "technical_fit_score", 5)
        culture_score= getattr(culture_res,  "culture_fit_score",   5)
        tech_summary = getattr(tech_res,     "summary", "")
        culture_summary = getattr(culture_res,"summary", "")

        verdict = await run_cross_agent_debate(
            agent_a_name="Tech Agent",
            score_a=tech_score,
            summary_a=tech_summary,
            agent_b_name="Culture Agent",
            score_b=culture_score,
            summary_b=culture_summary,
            resume_text=resume_text,
            job_requirement=job_requirement_text,
        )
        if verdict:
            debate_verdict_dict = verdict.model_dump()
            logger.info(
                f"[{request_id}] Debate resolved: agreed_score={verdict.agreed_score}, "
                f"winner={verdict.winner}"
            )
    except Exception as e:
        logger.warning(f"[{request_id}] Cross-agent debate failed (non-critical): {e}")

    # === STAGE 3.5: Flight Risk & Behavioral Profiling (run in parallel) ===
    logger.info(f"[{request_id}] Running Flight Risk + Behavioral Profiling")
    new_modules_start = time.time()

    linkedin_data = external_intel.get("linkedin") if external_intel else None
    github_readme = None
    if external_intel and external_intel.get("pinned_repos"):
        github_readme = external_intel["pinned_repos"][0].get("readme", "") if external_intel["pinned_repos"] else None

    flight_risk_task = asyncio.to_thread(
        analyze_flight_risk, linkedin_data, job_requirement_text
    )
    behavioral_task = run_behavioral_with_fallback(
        resume_text,
        github_readme=github_readme,
        mode=thinking_mode,
        seniority_level=seniority_level,
        past_feedback_summary=past_feedback_summary,
    )

    flight_risk_result, behavioral_result = await asyncio.gather(
        flight_risk_task, behavioral_task, return_exceptions=True
    )

    if isinstance(flight_risk_result, Exception):
        logger.error(f"FlightRiskAnalyzer failed: {flight_risk_result}")
        flight_risk_result = None
    if isinstance(behavioral_result, Exception):
        logger.error(f"BehavioralAgent failed: {behavioral_result}")
        behavioral_result = None

    performance_metrics["new_modules_ms"] = (time.time() - new_modules_start) * 1000
    
    # === STAGE 4: Knowledge Graph Enrichment ===
    logger.info(f"[{request_id}] Enriching with knowledge graph")
    kg_start = time.time()
    
    found_skills = tech_res.key_technologies or []
    kg_insights: Dict[str, list] = {}
    for skill in found_skills[:5]:
        kg_res = await mcp_client_manager.invoke_tool(
            "lead_agent", "tool_get_related_skills", {"skill_name": skill}
        )
        if kg_res and not kg_res.startswith("Error") and not kg_res.startswith("No "):
            parts = kg_res.split(":", 1)
            if len(parts) == 2:
                kg_insights[skill] = [s.strip() for s in parts[1].split(",")]
    
    enriched_tech_report = f"""
Technical Findings (Structured):
{json.dumps(tech_res.model_dump(), indent=2)}

Knowledge Graph Insights (related skills detected):
{json.dumps(kg_insights, indent=2)}
    """
    
    performance_metrics["kg_enrichment_ms"] = (time.time() - kg_start) * 1000
    
    # === STAGE 5: RAG Context (if requirement_id provided) ===
    rag_reasoning = None
    if requirement_id:
        rag_result = await run_raG_evaluation(resume_text, requirement_id)
        if rag_result:
            rag_reasoning = rag_result
    
    # === STAGE 4.6: Fuzzy Logic Score Calculation ===
    logger.info(f"[{request_id}] Calculating deterministic Fuzzy Logic score")
    fuzzy_start = time.time()

    flight_risk_dict = flight_risk_result.model_dump() if flight_risk_result and hasattr(flight_risk_result, 'model_dump') else None
    external_eval_dict = None

    raw_scores = extract_raw_scores_from_reports(
        screener_report=screener_res,
        tech_report=tech_res,
        culture_report=culture_res,
        extracurricular_report=extra_res,
        hackathon_report=hack_res,
        code_quality_report=code_res,
        flight_risk_report=flight_risk_dict,
        external_eval=None  # will be filled after external scoring
    )

    fuzzy_scorer = get_fuzzy_scorer()
    fuzzy_result = fuzzy_scorer.calculate_score(
        tech=raw_scores["tech"],
        growth=raw_scores["growth"],
        culture=raw_scores["culture"],
        execution=raw_scores["execution"],
        consistency=raw_scores["consistency"]
    )
    fuzzy_score_data = fuzzy_result.model_dump()
    performance_metrics["fuzzy_scoring_ms"] = (time.time() - fuzzy_start) * 1000
    logger.info(f"[{request_id}] Fuzzy score: {fuzzy_result.fuzzy_final_score:.1f} ({fuzzy_result.deterministic_decision})")

    # === STAGE 4.7: Error Correction Layer (fuzzy vs agent composite) ===
    error_correction_dict: Optional[dict] = None
    try:
        tech_s    = getattr(tech_res,    "technical_fit_score", 5)
        culture_s = getattr(culture_res, "culture_fit_score",   5)
        agent_composite = (tech_s + culture_s) / 2.0  # 1-10 scale
        ec_result = run_error_correction(
            fuzzy_score=fuzzy_result.fuzzy_final_score,
            agent_composite_score=agent_composite,
            agent_summaries={
                "tech":    getattr(tech_res,    "summary", ""),
                "culture": getattr(culture_res, "summary", ""),
            },
        )
        error_correction_dict = ec_result.model_dump()
        if ec_result.flag_for_human_review:
            logger.warning(
                f"[{request_id}] ERROR CORRECTION flagged for human review — "
                f"fuzzy={fuzzy_result.fuzzy_final_score:.1f}, "
                f"agent_norm={ec_result.agent_score_normalized:.1f}"
            )
    except Exception as e:
        logger.warning(f"[{request_id}] Error correction check failed (non-critical): {e}")

    # === STAGE 6: Fuzzy-Aware Decision Chain ===
    logger.info(f"[{request_id}] Running Fuzzy Logic + AI hybrid decision chain")
    decision_start = time.time()
    
    requirements_context = job_requirement_text
    if rag_reasoning:
        requirements_context = f"""
JOB REQUIREMENT:
{job_requirement_text}

RAG CONTEXT (retrieved from indexed documents):
{rag_reasoning}
        """.strip()
    
    external_str = json.dumps(external_intel, indent=2) if external_intel else None
    behavioral_str = json.dumps(behavioral_result.model_dump(), indent=2) if behavioral_result and hasattr(behavioral_result, 'model_dump') else None
    flight_risk_str = json.dumps(flight_risk_dict, indent=2) if flight_risk_dict else None

    final_decision_result = await run_fuzzy_aware_decision_chain(
        screener_report=screener_res.model_dump_json(),
        tech_report=enriched_tech_report,
        culture_report=culture_res.model_dump_json(),
        requirements_context=requirements_context,
        fuzzy_score_data=fuzzy_score_data,
        external_intel=external_str,
        extracurricular_report=extra_res.model_dump_json() if extra_res else None,
        hackathon_report=hack_res.model_dump_json() if hack_res else None,
        code_quality_report=code_res.model_dump_json() if code_res else None,
        behavioral_profile=behavioral_str,
        flight_risk_data=flight_risk_str,
        # Phase 1 & 2: Cognitive Parameters — propagate all the way to the LLM
        thinking_mode=thinking_mode.value if hasattr(thinking_mode, "value") else str(thinking_mode),
        seniority_level=seniority_level,
    )
    
    performance_metrics["decision_chain_ms"] = (time.time() - decision_start) * 1000
    
    # === STAGE 6.5: Adversarial Fairness Agent ===
    decision_value = final_decision_result.get("decision", "").lower()
    logger.info(f"[{request_id}] Running Fairness Auditor on decision: '{decision_value}'")
    fairness_start = time.time()

    fairness_result = await run_fairness_agent(
        original_decision=decision_value,
        decision_explanation=final_decision_result.get("explanation", ""),
        resume_text=resume_text,
        screener_report=screener_res.model_dump_json(),
        tech_report=enriched_tech_report,
        flight_risk_data=flight_risk_dict
    )

    fairness_dict = fairness_result.model_dump() if hasattr(fairness_result, 'model_dump') else None

    # Apply overrule if the Fairness Agent disagrees
    if fairness_result and fairness_result.overruled:
        logger.warning(f"[{request_id}] FAIRNESS OVERRULE: '{decision_value}' → '{fairness_result.final_decision}'. Bias: {fairness_result.bias_types_detected}")
        final_decision_result["decision"] = fairness_result.final_decision
        final_decision_result["_fairness_overruled"] = True
        final_decision_result["_fairness_narrative"] = fairness_result.audit_narrative
        decision_value = fairness_result.final_decision.lower()

    performance_metrics["fairness_audit_ms"] = (time.time() - fairness_start) * 1000

    # === STAGE 7: Rejection Feedback (skip if Fairness Agent overruled) ===
    rejection_feedback = None
    if decision_value in ("reject", "rejected") and not (fairness_result and fairness_result.overruled):
        logger.info(f"[{request_id}] Generating rejection feedback")
        rejection_feedback = await run_rejection_chain(
            decision_explanation=final_decision_result.get("explanation", ""),
            resume_details=resume_text
        )
    
    # === STAGE 8: External Intelligence Scoring ===
    external_evaluation = None
    if external_intel:
        logger.info(f"[{request_id}] Calculating external intelligence score")
        external_start = time.time()
        
        try:
            external_evaluation = await calculate_external_intelligence_score(external_intel)
            external_dict = external_evaluation.model_dump() if hasattr(external_evaluation, 'model_dump') else external_evaluation
            external_eval_dict = external_dict
            performance_metrics["external_eval_ms"] = (time.time() - external_start) * 1000
            
            # Incorporate external evaluation into final decision category scores
            ext_score = external_dict.get("overall_external_score", 0)
            if final_decision_result.get("category_scores"):
                final_decision_result["category_scores"]["external_intel"] = ext_score
            
            if external_dict.get("recommendation") == "strong":
                current_confidence = final_decision_result.get("meta_confidence_score", 0.5)
                final_decision_result["meta_confidence_score"] = min(0.95, current_confidence + 0.15)
            
        except Exception as e:
            logger.error(f"[{request_id}] External evaluation failed: {e}")

    # === STAGE 8.5: Elo Ranking (Percentile vs. Candidate Pool) ===
    elo_ranking_result = None
    try:
        from app.database.mongodb import get_mongodb
        db = get_mongodb()
        db_collection = db["candidates"] if db is not None else None
        elo_result = await calculate_elo_ranking(
            candidate_final_score=final_decision_result.get("final_score", 50),
            job_requirement_text=job_requirement_text,
            db_collection=db_collection
        )
        elo_ranking_result = elo_result.model_dump() if hasattr(elo_result, 'model_dump') else None
        if elo_ranking_result:
            final_decision_result["elo_statement"] = elo_result.elo_statement
        logger.info(f"[{request_id}] Elo ranking: {elo_result.elo_statement[:80]}...")
    except Exception as e:
        logger.error(f"[{request_id}] Elo ranking failed: {e}")

    # === Final Report ===
    performance_metrics["total_pipeline_ms"] = (time.time() - pipeline_start) * 1000
    
    logger.info(
        f"[{request_id}] Candidate review completed",
        extra={
            "total_duration_ms": performance_metrics["total_pipeline_ms"],
            "decision": decision_value,
            "agents_failed": sum(1 for v in [screener_res, tech_res, culture_res] if hasattr(v, '_error'))
        }
    )
    
    return CompleteAgentReport(
        screener=screener_res,
        tech=tech_res,
        culture=culture_res,
        extracurricular=extra_res,
        hackathon=hack_res,
        code_quality=code_res,
        skill_counts=skill_res,
        rag_reasoning=rag_reasoning,
        external_intel=external_intel,
        external_evaluation=external_dict if external_evaluation else None,
        # New Module Outputs
        flight_risk=flight_risk_dict,
        behavioral_profile=behavioral_result.model_dump() if behavioral_result and hasattr(behavioral_result, 'model_dump') else None,
        elo_ranking=elo_ranking_result,
        fuzzy_score_breakdown=fuzzy_score_data,
        fairness_audit=fairness_dict,
        final_decision=final_decision_result,
        rejection_feedback=rejection_feedback,
        bias_audit_log=bias_audit_log,
        performance_metrics=performance_metrics,
        # Phase 2 Outputs
        debate_verdict=debate_verdict_dict,
        error_correction=error_correction_dict,
        thinking_mode=thinking_mode.value,
        seniority_level=seniority_level,
        memory_injected=(past_feedback_summary is not None),
    )


async def save_evaluation_to_database(
    candidate_id: str,
    complete_report: CompleteAgentReport
) -> bool:
    """
    Saves the complete candidate evaluation to MongoDB.
    
    Includes:
    - All agent reports with scores
    - External intelligence scores
    - Final decision with reasoning
    - Performance metrics
    - Audit trails
    
    Args:
        candidate_id: Candidate ID
        complete_report: CompleteAgentReport object
        
    Returns:
        True if saved successfully
    """
    try:
        report_dict = {
            "screener": complete_report.screener.model_dump() if complete_report.screener else None,
            "tech": complete_report.tech.model_dump() if complete_report.tech else None,
            "culture": complete_report.culture.model_dump() if complete_report.culture else None,
            "extracurricular": complete_report.extracurricular.model_dump() if complete_report.extracurricular else None,
            "hackathon": complete_report.hackathon.model_dump() if complete_report.hackathon else None,
            "code_quality": complete_report.code_quality.model_dump() if complete_report.code_quality else None,
            "skill_counts": complete_report.skill_counts.model_dump() if complete_report.skill_counts else None,
            "rag_reasoning": complete_report.rag_reasoning,
            "external_intel": complete_report.external_intel,
            "external_evaluation": complete_report.external_evaluation,
            "final_decision": complete_report.final_decision,
            "rejection_feedback": complete_report.rejection_feedback,
            "bias_audit_log": complete_report.bias_audit_log,
            "performance_metrics": complete_report.performance_metrics,
        }
        
        res_str = await mcp_client_manager.invoke_tool(
            "lead_agent", 
            "tool_db_save_complete_eval", 
            {
                "candidate_id": candidate_id, 
                "report_json": json.dumps(report_dict)
            }
        )
        saved = False
        if res_str:
            res_data = json.loads(res_str)
            saved = res_data.get("saved", False)
        
        if saved:
            logger.info(f"[{candidate_id}] Complete evaluation saved to database via MCP")
        else:
            logger.warning(f"[{candidate_id}] Failed to save evaluation to database via MCP")
        
        return saved
    except Exception as e:
        logger.error(f"Error saving evaluation for {candidate_id} via MCP: {e}")
        return False


def _detect_role_category(job_requirement_text: str) -> str:
    """
    Detect role category from job requirement for system memory lookup.
    """
    job_upper = job_requirement_text.upper()
    
    if any(keyword in job_upper for keyword in ["PYTHON", "BACKEND", "SERVER", "API"]):
        return "Backend"
    elif any(keyword in job_upper for keyword in ["ML", "MACHINE LEARNING", "DATA SCIENCE", "AI", "NEURAL"]):
        return "Machine Learning"
    elif any(keyword in job_upper for keyword in ["FRONTEND", "REACT", "VUE", "ANGULAR", "UI"]):
        return "Frontend"
    elif any(keyword in job_upper for keyword in ["DEVOPS", "CLOUD", "KUBERNETES", "DOCKER", "CI/CD"]):
        return "DevOps"
    else:
        return "General"
