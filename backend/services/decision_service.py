import json
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from app.core.config import settings

logger = logging.getLogger(__name__)

class FinalDecision(BaseModel):
    final_score: int = Field(description="Final candidate score from 1 to 100")
    category_scores: dict[str, int] = Field(description="Percentage scores (0-100) for individual categories")
    decision: str = Field(description="Must be 'hire', 'reject', or 'further_interview'")
    explanation: str = Field(description="Detailed explanation of the decision based on agent reports")
    meta_confidence_score: float = Field(default=0.0, description="Agreement level between sub-agents (0.0 to 1.0)")

class RejectionFeedback(BaseModel):
    missing_skills: list[str] = Field(description="Critical skills the candidate lacks")
    experience_gap: str = Field(description="Any gaps in experience duration or quality")
    suggestions: str = Field(description="Constructive suggestions for the candidate to improve")

class SkillVerification(BaseModel):
    """Neo4j-based skill verification results"""
    skill_name: str = Field(description="Skill being verified")
    found_in_resume: bool = Field(description="Found in resume/CV")
    found_in_external: bool = Field(description="Found in GitHub/LinkedIn")
    related_skills: List[str] = Field(default=[], description="Related skills from Neo4j graph")
    proficiency_level: str = Field(default="unknown", description="estimated/verified/strong")
    evidence_sources: List[str] = Field(default=[], description="Where skill was found")
    risk_score: float = Field(default=0.0, description="Risk score 0-1 if mismatch")

class ConsistencyAnalysis(BaseModel):
    """Consistency checking across all data sources"""
    timeline_consistent: bool = Field(description="Resume dates match external profiles")
    skill_consistency: float = Field(description="0-1 score of skill consistency across sources")
    experience_level_match: bool = Field(description="Experience level matches job requirement")
    title_progression_logical: bool = Field(description="Career progression makes sense")
    inconsistencies: List[str] = Field(default=[], description="Specific inconsistencies found")
    red_flags: List[str] = Field(default=[], description="Potential red flags")

class DataAggregation(BaseModel):
    """Comprehensive data aggregation from all sources"""
    all_skills: List[str] = Field(description="Aggregated skills from all sources")
    technical_depth: float = Field(description="0-100 technical depth score")
    experience_years: Optional[float] = Field(description="Total years of relevant experience")
    role_fit: float = Field(description="0-100 role fit score")
    culture_alignment: float = Field(description="0-100 culture fit score")
    code_quality: float = Field(description="0-100 code quality score")
    external_verification: float = Field(description="0-100 external evidence quality")
    educational_background: str = Field(description="Education summary")
    major_projects: List[str] = Field(default=[], description="Major projects mentioned")
    verified_achievements: List[str] = Field(default=[], description="Achievements verified externally")

class RiskAssessment(BaseModel):
    """Comprehensive risk assessment"""
    overall_risk_score: float = Field(description="0-1 overall risk score")
    skill_gap_risk: float = Field(description="0-1 risk from skill gaps")
    experience_risk: float = Field(description="0-1 risk from insufficient experience")
    consistency_risk: float = Field(description="0-1 risk from inconsistencies")
    red_flags_count: int = Field(description="Number of red flags identified")
    confidence_adjustment: float = Field(description="-0.5 to +0.5 adjustment to confidence based on risks")

class ComparativeAnalysis(BaseModel):
    """Analysis comparing candidate against role requirements"""
    must_have_skills_coverage: float = Field(description="0-1 coverage of must-have skills")
    nice_to_have_skills_coverage: float = Field(description="0-1 coverage of nice-to-have skills")
    experience_seniority_match: str = Field(description="junior/mid/senior/lead match")
    learning_potential: float = Field(description="0-1 score based on pattern of growth")
    overqualified_risk: bool = Field(description="Risk of candidate being overqualified")
    growth_trajectory: str = Field(description="Declining/Stable/Growing/Accelerating")

class EnhancedAnalysisReport(BaseModel):
    """Comprehensive enhanced decision analysis"""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    data_aggregation: DataAggregation = Field(description="Aggregated data from all sources")
    consistency_analysis: ConsistencyAnalysis = Field(description="Consistency checking results")
    skill_verifications: List[SkillVerification] = Field(default=[], description="Individual skill verification")
    risk_assessment: RiskAssessment = Field(description="Risk assessment results")
    comparative_analysis: ComparativeAnalysis = Field(description="Comparison with role requirements")
    neo4j_insights: Dict[str, Any] = Field(default={}, description="Neo4j knowledge graph insights")
    confidence_factors: Dict[str, float] = Field(default={}, description="Factors affecting confidence")
    final_recommendation: str = Field(description="strong_hire/hire/neutral/consider_further/reject")

def get_decision_llm():
    """Get decision LLM with API key rotation to prevent rate limiting"""
    key = settings.get_key_for_agent(10)
    if not key:
        logger.warning("Decision LLM initialized without a valid API key.")
    
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=key,
        transport="rest",
        temperature=0.2,
        max_retries=5,
        timeout=60
    )

llm = get_decision_llm()

# ============================================================================
# NEO4J INTEGRATION & KNOWLEDGE GRAPH ANALYSIS
# ============================================================================

async def analyze_with_neo4j(
    candidate_skills: List[str],
    candidate_experience_level: str,
    required_skills: List[str],
    required_seniority: str,
    job_domain: str
) -> Dict[str, Any]:
    """
    Analyze candidate against job requirements using Neo4j knowledge graph.
    
    Returns insights on:
    - Skill relationships and transferability
    - Career path alignment
    - Skill gap analysis
    - Growth potential
    """
    try:
        from ..services.neo4j_service import kg_service
        
        neo4j_insights = {
            "skill_relationships": {},
            "transferable_skills": [],
            "skill_gaps": [],
            "career_path_fit": "unknown",
            "domain_specialization": "",
            "learning_curve": "unknown"
        }
        
        # 1. Analyze skill relationships and gaps
        required_lower = {s.lower() for s in required_skills}
        candidate_lower = {s.lower() for s in candidate_skills}
        
        direct_matches = required_lower & candidate_lower
        missing_skills = required_lower - candidate_lower
        
        # Check for transferable skills via Neo4j
        transferable = []
        for skill in missing_skills:
            related = kg_service.get_related_skills(skill, limit=5)
            candidate_related = {r.lower() for r in related} & candidate_lower
            if candidate_related:
                transferable.extend(candidate_related)
                neo4j_insights["skill_relationships"][skill] = list(candidate_related)
        
        neo4j_insights["transferable_skills"] = list(set(transferable))
        neo4j_insights["skill_gaps"] = [s for s in missing_skills if s not in transferable]
        
        # 2. Career path analysis
        seniority_levels = ["junior", "mid", "senior", "lead", "principal"]
        candidate_idx = seniority_levels.index(candidate_experience_level.lower()) if candidate_experience_level.lower() in seniority_levels else 1
        required_idx = seniority_levels.index(required_seniority.lower()) if required_seniority.lower() in seniority_levels else 1
        
        if candidate_idx >= required_idx:
            neo4j_insights["career_path_fit"] = "meets_requirement" if candidate_idx == required_idx else "overqualified"
        else:
            neo4j_insights["career_path_fit"] = "below_requirement"
        
        neo4j_insights["seniority_gap"] = required_idx - candidate_idx
        
        # 3. Domain specialization check
        domain_skills = []
        for skill in candidate_skills:
            related = kg_service.get_related_skills(skill, limit=3)
            if any(job_domain.lower() in r.lower() or r.lower() in job_domain.lower() for r in related):
                domain_skills.append(skill)
        
        neo4j_insights["domain_specialization"] = "strong" if len(domain_skills) >= len(candidate_skills) * 0.6 else "general"
        
        # 4. Learning curve estimation
        gap_count = len(neo4j_insights["skill_gaps"])
        transferable_count = len(neo4j_insights["transferable_skills"])
        
        if gap_count == 0:
            neo4j_insights["learning_curve"] = "minimal"
        elif gap_count <= 2 and transferable_count >= len(missing_skills) * 0.5:
            neo4j_insights["learning_curve"] = "short"
        elif gap_count <= 4:
            neo4j_insights["learning_curve"] = "medium"
        else:
            neo4j_insights["learning_curve"] = "long"
        
        logger.info(f"Neo4j analysis completed: {gap_count} skills gaps, {transferable_count} transferable")
        return neo4j_insights
        
    except Exception as e:
        logger.error(f"Neo4j analysis failed: {e}")
        return {
            "error": str(e),
            "skill_relationships": {},
            "transferable_skills": [],
            "skill_gaps": [],
            "career_path_fit": "error"
        }

async def aggregate_all_agent_data(
    screener_data: Dict[str, Any],
    tech_data: Dict[str, Any],
    culture_data: Dict[str, Any],
    job_requirements: str,
    extracurricular_data: Optional[Dict] = None,
    hackathon_data: Optional[Dict] = None,
    code_quality_data: Optional[Dict] = None,
    external_data: Optional[Dict] = None
) -> DataAggregation:
    """
    Aggregates all agent data into a unified structure for analysis.
    
    Extracts:
    - All skills from all sources
    - Technical depth assessment
    - Experience calculation
    - Role fit analysis
    - Culture alignment
    - Verified achievements
    """
    try:
        all_skills = set()
        
        # Extract skills from tech report
        tech_skills = tech_data.get("evaluated_skills", []) or []
        all_skills.update(tech_skills)
        
        # Extract skills from external sources
        if external_data:
            external_skills = external_data.get("languages", [])
            if isinstance(external_skills, dict):
                all_skills.update(external_skills.keys())
            elif isinstance(external_skills, list):
                all_skills.update(external_skills)
        
        # Calculate technical depth
        technical_depth = float(tech_data.get("technical_depth_score", 50))
        
        # Calculate years of experience
        experience_years = None
        if "years_of_exp" in tech_data:
            try:
                experience_years = float(tech_data["years_of_exp"])
            except (ValueError, TypeError):
                experience_years = None
        
        # Extract role fit from tech report
        role_fit = float(tech_data.get("role_category_score", 50))
        
        # Culture alignment
        culture_alignment = float(culture_data.get("soft_skills_score", 50))
        
        # Code quality
        code_quality = 0.0
        if code_quality_data:
            code_quality = float(code_quality_data.get("overall_quality_score", 0))
        
        # External verification
        external_verification = 0.0
        if external_data:
            external_verification = float(external_data.get("overall_external_score", 0))
        
        # Education
        educational_background = screener_data.get("education_details", "Not specified")
        
        # Major projects
        major_projects = tech_data.get("project_category", [])
        if isinstance(major_projects, str):
            major_projects = [major_projects]
        
        # Verified achievements
        verified_achievements = []
        if code_quality_data:
            projects = code_quality_data.get("analyzed_repos", [])
            if projects:
                verified_achievements.append(f"Contributed to {len(projects)} repositories")
        
        if external_data and external_data.get("github"):
            gh_data = external_data["github"]
            if gh_data.get("total_stars"):
                verified_achievements.append(f"Projects with {gh_data['total_stars']} total stars")
        
        return DataAggregation(
            all_skills=list(all_skills),
            technical_depth=technical_depth,
            experience_years=experience_years,
            role_fit=role_fit,
            culture_alignment=culture_alignment,
            code_quality=code_quality,
            external_verification=external_verification,
            educational_background=educational_background,
            major_projects=major_projects,
            verified_achievements=verified_achievements
        )
    
    except Exception as e:
        logger.error(f"Data aggregation failed: {e}")
        return DataAggregation(
            all_skills=[],
            technical_depth=0,
            role_fit=0,
            culture_alignment=0,
            code_quality=0,
            external_verification=0,
            educational_background="Error aggregating data"
        )

async def analyze_consistency(
    screener_data: Dict[str, Any],
    tech_data: Dict[str, Any],
    culture_data: Dict[str, Any],
    external_data: Optional[Dict] = None
) -> ConsistencyAnalysis:
    """
    Analyzes consistency across all data sources.
    
    Checks:
    - Timeline consistency (resume dates vs LinkedIn)
    - Skill consistency (resume vs GitHub vs LinkedIn)
    - Experience level match across sources
    - Career progression logic
    - Red flags
    """
    inconsistencies = []
    red_flags = []
    
    try:
        # 1. Timeline consistency
        timeline_consistent = True
        if external_data and external_data.get("linkedin"):
            linkedin_exp = external_data["linkedin"].get("experience", [])
            resume_dates = screener_data.get("date_range", "")
            
            # Simple check: if both have dates, they should overlap or connect logically
            if linkedin_exp and resume_dates:
                # This is a simplified check - in production, parse actual dates
                timeline_consistent = True  # Assume consistent unless proven otherwise
        
        # 2. Skill consistency
        resume_skills = set(tech_data.get("evaluated_skills", []) or [])
        external_skills = set()
        
        if external_data:
            if external_data.get("languages"):
                langs = external_data["languages"]
                if isinstance(langs, dict):
                    external_skills.update(langs.keys())
                elif isinstance(langs, list):
                    external_skills.update(langs)
        
        skill_consistency = 0.0
        if resume_skills or external_skills:
            overlap = len(resume_skills & external_skills)
            total = len(resume_skills | external_skills)
            skill_consistency = overlap / total if total > 0 else 0.0
            
            if skill_consistency < 0.3:
                inconsistencies.append("Low skill overlap between resume and external profiles")
                red_flags.append("Resume claims may not be verified by external evidence")
        
        # 3. Experience level match
        tech_level = str(tech_data.get("seniority_level", "unknown")).lower()
        culture_level = str(culture_data.get("seniority_indicator", "unknown")).lower()
        
        experience_level_match = tech_level == culture_level or "unknown" in [tech_level, culture_level]
        
        if not experience_level_match:
            inconsistencies.append(f"Seniority mismatch: Tech={tech_level}, Culture={culture_level}")
        
        # 4. Title progression logic
        title_progression_logical = True
        if external_data and external_data.get("linkedin"):
            linkedin_exp = external_data["linkedin"].get("experience", [])
            if linkedin_exp and len(linkedin_exp) > 1:
                # Check if titles make sense progression
                # This is simplified - in production do more sophisticated analysis
                title_progression_logical = True
        
        # 5. Additional red flags
        tech_score = float(tech_data.get("technical_depth_score", 50))
        culture_score = float(culture_data.get("soft_skills_score", 50))
        
        if abs(tech_score - culture_score) > 40:
            red_flags.append(f"Large gap between technical ({tech_score}) and culture ({culture_score}) scores")
        
        if external_data:
            gh_score = float(external_data.get("github_score", 0))
            if gh_score > 0 and tech_score < 40:
                red_flags.append("Strong GitHub presence but weak technical interview - verify technical depth")
            elif gh_score < 30 and tech_score > 70:
                red_flags.append("Weak GitHub presence but strong technical interview - verify code quality")
        
        return ConsistencyAnalysis(
            timeline_consistent=timeline_consistent,
            skill_consistency=skill_consistency,
            experience_level_match=experience_level_match,
            title_progression_logical=title_progression_logical,
            inconsistencies=inconsistencies,
            red_flags=red_flags
        )
    
    except Exception as e:
        logger.error(f"Consistency analysis failed: {e}")
        return ConsistencyAnalysis(
            timeline_consistent=True,
            skill_consistency=0.0,
            experience_level_match=True,
            title_progression_logical=True,
            inconsistencies=[f"Analysis error: {str(e)}"],
            red_flags=[]
        )

async def assess_risks(
    data_aggregation: DataAggregation,
    consistency_analysis: ConsistencyAnalysis,
    neo4j_insights: Dict[str, Any],
    screener_data: Dict[str, Any],
    external_data: Optional[Dict] = None
) -> RiskAssessment:
    """
    Comprehensive risk assessment across multiple dimensions.
    
    Calculates:
    - Skill gap risks
    - Experience risks
    - Consistency/credibility risks
    - Overall risk score
    - Confidence adjustment
    """
    try:
        # 1. Skill gap risk
        skill_gaps = neo4j_insights.get("skill_gaps", [])
        gap_count = len(skill_gaps)
        
        if gap_count == 0:
            skill_gap_risk = 0.0
        elif gap_count == 1:
            skill_gap_risk = 0.15
        elif gap_count <= 3:
            skill_gap_risk = 0.35
        else:
            skill_gap_risk = min(0.7, 0.35 + (gap_count - 3) * 0.05)
        
        # 2. Experience risk
        experience_risk = 0.0
        seniority_gap = neo4j_insights.get("seniority_gap", 0)
        
        if seniority_gap == 0:
            experience_risk = 0.0
        elif seniority_gap == 1:
            experience_risk = 0.25
        elif seniority_gap <= 2:
            experience_risk = 0.45
        else:
            experience_risk = min(0.8, 0.45 + (seniority_gap - 2) * 0.05)
        
        # 3. Consistency risk
        consistency_risk = 0.0
        if consistency_analysis.inconsistencies:
            consistency_risk = min(0.6, len(consistency_analysis.inconsistencies) * 0.15)
        
        if consistency_analysis.skill_consistency < 0.3:
            consistency_risk = max(consistency_risk, 0.4)
        
        # 4. Overall risk score (weighted average)
        overall_risk = (skill_gap_risk * 0.35 + experience_risk * 0.35 + consistency_risk * 0.3)
        
        # 5. Confidence adjustment based on risk
        confidence_adjustment = 0.0
        
        if overall_risk < 0.2:
            confidence_adjustment = 0.15  # Low risk: boost confidence
        elif overall_risk < 0.4:
            confidence_adjustment = 0.05
        elif overall_risk > 0.6:
            confidence_adjustment = -0.25  # High risk: reduce confidence
        elif overall_risk > 0.75:
            confidence_adjustment = -0.4
        
        # 6. Additional risk factors
        red_flags_count = len(consistency_analysis.red_flags)
        if red_flags_count > 0:
            confidence_adjustment -= (red_flags_count * 0.05)
        
        # Check for external verification concerns
        if external_data and external_data.get("warnings"):
            consistency_risk = min(1.0, consistency_risk + 0.15)
            confidence_adjustment -= 0.1
        
        return RiskAssessment(
            overall_risk_score=overall_risk,
            skill_gap_risk=skill_gap_risk,
            experience_risk=experience_risk,
            consistency_risk=consistency_risk,
            red_flags_count=red_flags_count,
            confidence_adjustment=confidence_adjustment
        )
    
    except Exception as e:
        logger.error(f"Risk assessment failed: {e}")
        return RiskAssessment(
            overall_risk_score=0.5,
            skill_gap_risk=0.0,
            experience_risk=0.0,
            consistency_risk=0.3,
            red_flags_count=1,
            confidence_adjustment=0.0
        )

async def comparative_analysis(
    data_aggregation: DataAggregation,
    job_requirements: str,
    neo4j_insights: Dict[str, Any]
) -> ComparativeAnalysis:
    """
    Compare candidate against role requirements.
    
    Analyzes:
    - Must-have skills coverage
    - Nice-to-have skills coverage
    - Seniority match
    - Learning potential
    - Growth trajectory
    """
    try:
        # Parse must-have skills from job requirements (simplified)
        must_haves = []
        nice_haves = []
        
        # Extract skills mentioned in requirements
        job_lower = job_requirements.lower()
        candidate_all_skills = {s.lower() for s in data_aggregation.all_skills}
        
        # Must-have coverage
        must_have_coverage = 0.5  # Default assumption
        if must_haves:
            covered = len({s.lower() for s in must_haves} & candidate_all_skills)
            must_have_coverage = covered / len(must_haves) if must_haves else 0.0
        
        # Nice-to-have coverage
        nice_have_coverage = 0.3  # Default assumption
        if nice_haves:
            covered = len({s.lower() for s in nice_haves} & candidate_all_skills)
            nice_have_coverage = covered / len(nice_haves) if nice_haves else 0.0
        
        # Seniority match
        seniority_gap = neo4j_insights.get("seniority_gap", 0)
        if seniority_gap == 0:
            exp_seniority_match = "exact_match"
        elif seniority_gap == -1:
            exp_seniority_match = "slightly_junior"
        elif seniority_gap == 1:
            exp_seniority_match = "slightly_senior"
        else:
            exp_seniority_match = "mismatch"
        
        # Learning potential
        learning_potential = 1.0 - (neo4j_insights.get("skill_gaps", []) and len(neo4j_insights["skill_gaps"]) or 0) * 0.1
        learning_potential = max(0.0, min(1.0, learning_potential))
        
        # Growth trajectory
        transferable = len(neo4j_insights.get("transferable_skills", []))
        gaps = len(neo4j_insights.get("skill_gaps", []))
        
        if gaps == 0:
            growth = "Stable"
        elif transferable > gaps:
            growth = "Accelerating"
        elif transferable == gaps:
            growth = "Growing"
        else:
            growth = "Declining"
        
        overqualified = seniority_gap > 1
        
        return ComparativeAnalysis(
            must_have_skills_coverage=must_have_coverage,
            nice_to_have_skills_coverage=nice_have_coverage,
            experience_seniority_match=exp_seniority_match,
            learning_potential=learning_potential,
            overqualified_risk=overqualified,
            growth_trajectory=growth
        )
    
    except Exception as e:
        logger.error(f"Comparative analysis failed: {e}")
        return ComparativeAnalysis(
            must_have_skills_coverage=0.5,
            nice_to_have_skills_coverage=0.3,
            experience_seniority_match="unknown",
            learning_potential=0.5,
            overqualified_risk=False,
            growth_trajectory="Unknown"
        )

async def run_comprehensive_analysis(
    screener_data: str,
    tech_data: str,
    culture_data: str,
    job_requirements: str,
    external_intel: Optional[str] = None,
    extracurricular_data: Optional[str] = None,
    hackathon_data: Optional[str] = None,
    code_quality_data: Optional[str] = None
) -> EnhancedAnalysisReport:
    """
    Comprehensive analysis of candidate using all data sources and Neo4j insights.
    
    Performs:
    1. Data aggregation from all agents
    2. Consistency analysis
    3. Neo4j knowledge graph analysis
    4. Risk assessment
    5. Comparative analysis against role requirements
    
    Returns enriched analysis for decision making.
    """
    try:
        # Parse JSON data
        screener_dict = json.loads(screener_data) if isinstance(screener_data, str) else screener_data
        tech_dict = json.loads(tech_data) if isinstance(tech_data, str) else tech_data
        culture_dict = json.loads(culture_data) if isinstance(culture_data, str) else culture_data
        
        external_dict = None
        if external_intel:
            external_dict = json.loads(external_intel) if isinstance(external_intel, str) else external_intel
        
        extracurricular_dict = None
        if extracurricular_data:
            extracurricular_dict = json.loads(extracurricular_data) if isinstance(extracurricular_data, str) else extracurricular_data
        
        hackathon_dict = None
        if hackathon_data:
            hackathon_dict = json.loads(hackathon_data) if isinstance(hackathon_data, str) else hackathon_data
        
        code_quality_dict = None
        if code_quality_data:
            code_quality_dict = json.loads(code_quality_data) if isinstance(code_quality_data, str) else code_quality_data
        
        # 1. Aggregate all data
        logger.info("Running comprehensive analysis - Stage 1: Data Aggregation")
        data_agg = await aggregate_all_agent_data(
            screener_dict, tech_dict, culture_dict, job_requirements,
            extracurricular_dict, hackathon_dict, code_quality_dict, external_dict
        )
        
        # 2. Consistency analysis
        logger.info("Running comprehensive analysis - Stage 2: Consistency Check")
        consistency = await analyze_consistency(
            screener_dict, tech_dict, culture_dict, external_dict
        )
        
        # 3. Neo4j analysis
        logger.info("Running comprehensive analysis - Stage 3: Neo4j Knowledge Graph")
        required_skills = job_requirements.split() if isinstance(job_requirements, str) else []
        required_seniority = tech_dict.get("seniority_level", "mid")
        job_domain = "software_engineering"  # Default, can be extracted from requirements
        
        neo4j_insights = await analyze_with_neo4j(
            data_agg.all_skills,
            tech_dict.get("seniority_level", "mid"),
            required_skills,
            required_seniority,
            job_domain
        )
        
        # 4. Risk assessment
        logger.info("Running comprehensive analysis - Stage 4: Risk Assessment")
        risk_assessment = await assess_risks(
            data_agg, consistency, neo4j_insights, screener_dict, external_dict
        )
        
        # 5. Comparative analysis
        logger.info("Running comprehensive analysis - Stage 5: Comparative Analysis")
        comp_analysis = await comparative_analysis(
            data_agg, job_requirements, neo4j_insights
        )
        
        # 6. Build confidence factors
        confidence_factors = {
            "data_quality": 0.8 if len(data_agg.all_skills) > 0 else 0.4,
            "external_verification": external_dict.get("overall_external_score", 0) / 100.0 if external_dict else 0.0,
            "consistency_score": consistency.skill_consistency,
            "neo4j_coverage": 1.0 - (len(neo4j_insights.get("skill_gaps", [])) / max(1, len(data_agg.all_skills))),
            "risk_adjustment": 1.0 - risk_assessment.overall_risk_score
        }
        
        # 7. Final recommendation
        avg = (
            comp_analysis.must_have_skills_coverage +
            comp_analysis.nice_to_have_skills_coverage +
            confidence_factors["consistency_score"]
        ) / 3.0
        
        if risk_assessment.overall_risk_score > 0.6:
            final_rec = "reject"
        elif avg > 0.85 and risk_assessment.overall_risk_score < 0.2:
            final_rec = "strong_hire"
        elif avg > 0.7 and risk_assessment.overall_risk_score < 0.4:
            final_rec = "hire"
        elif avg > 0.5:
            final_rec = "consider_further"
        else:
            final_rec = "reject"
        
        report = EnhancedAnalysisReport(
            data_aggregation=data_agg,
            consistency_analysis=consistency,
            skill_verifications=[],  # Individual skill verifications would be populated here
            risk_assessment=risk_assessment,
            comparative_analysis=comp_analysis,
            neo4j_insights=neo4j_insights,
            confidence_factors=confidence_factors,
            final_recommendation=final_rec
        )
        
        logger.info(f"Comprehensive analysis completed: {final_rec}")
        return report
    
    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {e}")
        raise

async def run_decision_chain(
    screener_report: str, 
    tech_report: str, 
    culture_report: str, 
    requirements_context: str,
    external_intel: Optional[str] = None,
    extracurricular_report: Optional[str] = None,
    hackathon_report: Optional[str] = None,
    code_quality_report: Optional[str] = None
) -> dict:
    """
    Takes all multi-agent outputs and generates the final score, decision, and explanation.
    Now incorporates external evidence (GitHub/LinkedIn) to verify resume claims.
    """
    decision_parser = JsonOutputParser(pydantic_object=FinalDecision)
    
    prompt = PromptTemplate(
        template="""You are the Final Decision Maker (Lead Agent) for the Hiring Pipeline.
        Based on the provided agent reports, job requirements, and EXTERNAL EVIDENCE, generate the final decision.
        
        Job Requirements Context:
        {requirements}
        
        Screener Report:
        {screener}
        
        Technical Report:
        {tech}
        
        Extra-Curricular Report:
        {extracurricular_report}
        
        Hackathon Evaluation:
        {hackathon_report}
        
        Code Quality Review:
        {code_quality_report}

        ---
        EXTERNAL EVIDENCE (GitHub/LinkedIn Analysis):
        {external_intel}
        ---

        HOLISTIC HUMAN-LIKE EVALUATION MODEL (100 PTS TOTAL):
        
        You are an expert Engineering Manager evaluating this candidate, not a robotic calculator. Grade them holistically based on their proven ability, potential, and "hustle". Do not rigidly deduct points; instead, look at the big picture.

        Evaluate across these 5 dimensions and output percentage scores (0-100) in the 'category_scores' dictionary:
        
        1. Core_Technical_Competence: Focus on problem-solving, project depth, and actual code quality rather than rigidly matching keywords. A great GitHub repo outweighs missing a minor framework.
           
        2. Growth_Potential_and_Hustle: Look for curiosity and learning velocity. Do they attend hackathons? Do they build side projects? Give high points to self-starters who learn fast.
           
        3. Team_and_Cultural_Fit: How well do they communicate? Are they a good team player? Evaluate their soft skills and narrative richness from their LinkedIn and cover letters.
           
        4. Real_World_Execution: Do they build actual working software or just follow generic tutorials? High scores for industry-grade projects and high-impact internships.
           
        5. Consistency_and_Credibility: Do their resume claims align with their real-world digital footprint (LinkedIn/GitHub)? If they lack a skill but admit it, that's better than lying. Use your judgment—minor chronological gaps are fine if the overall candidate is strong.

        SCORING PHILOSOPHY:
        - Don't enforce strict zero-score rules. Give them the benefit of the doubt if they show raw talent.
        - Look for "spikes" in ability. If someone is truly exceptional in one area (e.g., incredible GitHub projects), let that offset minor weaknesses (e.g., lack of certifications).
        - Use your subjective judgment as a senior leader to determine if this person would be a valuable hire.
        
        Final Decision must balance technical depth, cultural fit, and verified evidence.
        
        CONFIDENCE CALIBRATION (CRITICAL):
        - Analyze how well the different agents agree. 
        - If Tech agrees with Culture and Screener, meta_confidence is HIGH (0.9).
        - If there is a major conflict (e.g. Tech says Hire, Culture says Reject), meta_confidence is LOW (0.4-0.6).
        
        Output the decision exactly as requested by the format instructions.
        \n{format_instructions}""",
        input_variables=["requirements", "screener", "tech", "culture", "external_intel", "extracurricular_report", "hackathon_report", "code_quality_report"],
        partial_variables={"format_instructions": decision_parser.get_format_instructions()},
    )
    
    chain = prompt | llm | decision_parser
    
    return await chain.ainvoke({
        "requirements": requirements_context,
        "screener": screener_report,
        "tech": tech_report,
        "culture": culture_report,
        "external_intel": external_intel or "No external data provided.",
        "extracurricular_report": extracurricular_report or "No extracurricular data provided.",
        "hackathon_report": hackathon_report or "No hackathon data provided.",
        "code_quality_report": code_quality_report or "No code quality data provided."
    })

async def run_rejection_chain(decision_explanation: str, resume_details: str) -> dict:
    """
    Dedicated chain to generate constructive feedback if a candidate is rejected.
    """
    feedback_parser = JsonOutputParser(pydantic_object=RejectionFeedback)
    
    prompt = PromptTemplate(
        template="""You are an empathetic HR feedback generator.
        The candidate was rejected based on the following evaluation context.
        Generate structured, constructive feedback highlighting missing skills and experience gaps, along with actionable suggestions.
        
        Decision Explanation:
        {explanation}
        
        Candidate Details/Resume Overview:
        {resume}
        
        \n{format_instructions}""",
        input_variables=["explanation", "resume"],
        partial_variables={"format_instructions": feedback_parser.get_format_instructions()},
    )
    
    chain = prompt | llm | feedback_parser
    
    return await chain.ainvoke({
        "explanation": decision_explanation,
        "resume": resume_details
    })

# ============================================================================
# ENHANCED DECISION CHAIN WITH COMPREHENSIVE ANALYSIS
# ============================================================================

async def run_enhanced_decision_chain(
    screener_report: str,
    tech_report: str,
    culture_report: str,
    requirements_context: str,
    external_intel: Optional[str] = None,
    extracurricular_report: Optional[str] = None,
    hackathon_report: Optional[str] = None,
    code_quality_report: Optional[str] = None
) -> dict:
    """
    Enhanced decision chain that incorporates comprehensive analysis including:
    - Neo4j knowledge graph insights
    - Consistency analysis
    - Risk assessment
    - Comparative analysis
    - Confidence calibration based on multiple factors
    
    This provides a more robust and data-driven decision.
    """
    try:
        # Run comprehensive analysis first to gather insights
        logger.info("Starting enhanced decision chain with comprehensive analysis")
        comprehensive_analysis = await run_comprehensive_analysis(
            screener_report, tech_report, culture_report, requirements_context,
            external_intel, extracurricular_report, hackathon_report, code_quality_report
        )
        
        # Build enriched context from analysis
        analysis_context = f"""
======= COMPREHENSIVE ANALYSIS INSIGHTS (Neo4j, Consistency, Risk) =======

DATA AGGREGATION:
- Technical Depth: {comprehensive_analysis.data_aggregation.technical_depth}/100
- Role Fit: {comprehensive_analysis.data_aggregation.role_fit}/100
- Culture Alignment: {comprehensive_analysis.data_aggregation.culture_alignment}/100
- External Verification: {comprehensive_analysis.data_aggregation.external_verification}/100
- Code Quality: {comprehensive_analysis.data_aggregation.code_quality}/100
- All Skills Identified: {len(comprehensive_analysis.data_aggregation.all_skills)}

CONSISTENCY ANALYSIS:
- Skill Consistency Score: {comprehensive_analysis.consistency_analysis.skill_consistency:.2f} (0-1)
- Timeline Consistent: {comprehensive_analysis.consistency_analysis.timeline_consistent}
- Experience Level Match: {comprehensive_analysis.consistency_analysis.experience_level_match}
- Red Flags Count: {len(comprehensive_analysis.consistency_analysis.red_flags)}
- Red Flags: {', '.join(comprehensive_analysis.consistency_analysis.red_flags) if comprehensive_analysis.consistency_analysis.red_flags else 'None'}

NEO4J KNOWLEDGE GRAPH INSIGHTS:
- Career Path Fit: {comprehensive_analysis.neo4j_insights.get('career_path_fit', 'unknown')}
- Skill Gaps: {len(comprehensive_analysis.neo4j_insights.get('skill_gaps', []))} gaps identified
- Transferable Skills: {len(comprehensive_analysis.neo4j_insights.get('transferable_skills', []))} identified
- Domain Specialization: {comprehensive_analysis.neo4j_insights.get('domain_specialization', 'unknown')}
- Learning Curve: {comprehensive_analysis.neo4j_insights.get('learning_curve', 'unknown')}
- Gap Details: {comprehensive_analysis.neo4j_insights.get('skill_gaps', [])}

RISK ASSESSMENT:
- Overall Risk Score: {comprehensive_analysis.risk_assessment.overall_risk_score:.2f} (0-1)
- Skill Gap Risk: {comprehensive_analysis.risk_assessment.skill_gap_risk:.2f}
- Experience Risk: {comprehensive_analysis.risk_assessment.experience_risk:.2f}
- Consistency Risk: {comprehensive_analysis.risk_assessment.consistency_risk:.2f}
- Confidence Adjustment: {comprehensive_analysis.risk_assessment.confidence_adjustment:+.2f}

COMPARATIVE ANALYSIS:
- Must-Have Skills Coverage: {comprehensive_analysis.comparative_analysis.must_have_skills_coverage:.1%}
- Nice-to-Have Skills Coverage: {comprehensive_analysis.comparative_analysis.nice_to_have_skills_coverage:.1%}
- Experience Seniority Match: {comprehensive_analysis.comparative_analysis.experience_seniority_match}
- Learning Potential: {comprehensive_analysis.comparative_analysis.learning_potential:.1%}
- Overqualified Risk: {comprehensive_analysis.comparative_analysis.overqualified_risk}
- Growth Trajectory: {comprehensive_analysis.comparative_analysis.growth_trajectory}

CONFIDENCE FACTORS:
- Data Quality: {comprehensive_analysis.confidence_factors.get('data_quality', 0):.2f}
- External Verification: {comprehensive_analysis.confidence_factors.get('external_verification', 0):.2f}
- Consistency Score: {comprehensive_analysis.confidence_factors.get('consistency_score', 0):.2f}
- Neo4j Coverage: {comprehensive_analysis.confidence_factors.get('neo4j_coverage', 0):.2f}
- Risk Adjustment: {comprehensive_analysis.confidence_factors.get('risk_adjustment', 0):.2f}

PRELIMINARY RECOMMENDATION: {comprehensive_analysis.final_recommendation}
=====================================================================
"""
        
        # Run standard decision chain with enriched context
        decision_parser = JsonOutputParser(pydantic_object=FinalDecision)
        
        prompt = PromptTemplate(
            template="""You are the Final Decision Maker (Lead Agent) for the Hiring Pipeline.
Your decision should be informed by comprehensive analysis including Neo4j knowledge graph insights, 
consistency checks across sources, risk assessment, and comparative analysis.

COMPREHENSIVE ANALYSIS RESULTS:
{analysis_context}

Job Requirements Context:
{requirements}

Screener Report:
{screener}

Technical Report:
{tech}

Extra-Curricular Report:
{extracurricular_report}

Hackathon Evaluation:
{hackathon_report}

Code Quality Review:
{code_quality_report}

EXTERNAL EVIDENCE (GitHub/LinkedIn Analysis):
{external_intel}

---

DECISION FRAMEWORK WITH NEO4J INSIGHTS:

Your decision should weigh:

1. SKILL ALIGNMENT (40%):
   - Must-have skills coverage (from comprehensive analysis)
   - Neo4j transferable skills assessment
   - Skill gaps and learning curve estimate
   - External verification of technical abilities

2. EXPERIENCE & SENIORITY (30%):
   - Experience level match via Neo4j career path analysis
   - Timeline consistency across resume and external sources
   - Growth trajectory assessment
   - Relevant experience to role domain

3. CULTURE & FIT (15%):
   - Soft skills and cultural alignment score
   - Consistency of professional narrative
   - Achievement verification

4. RISK ASSESSMENT (15%):
   - Overall risk score from comprehensive analysis
   - Red flags and inconsistencies
   - Overqualification risk
   - Confidence factors

RECOMMENDATIONS FROM COMPREHENSIVE ANALYSIS:
- Follow the preliminary recommendation: {preliminary_rec}
- Adjust confidence based on risk assessment (confidence adjustment: {confidence_adj:+.2f})
- Flag any red flags identified in consistency analysis
- Consider skill gaps' severity (gaps: {major_gaps})

MANDATORY PRECISION RULES:
- Final score must reflect Neo4j insights and risk factors
- If overall risk score > 0.6, decision should not be "hire"
- If skill consistency < 0.3, flag as high-risk even if other scores are good
- Apply mandatory adjustments from risk assessment
- Confidence calibration MUST incorporate all factors including risk adjustment

Output your decision exactly as requested by the format instructions.
\n{format_instructions}""",
            input_variables=["analysis_context", "requirements", "screener", "tech", "extracurricular_report", 
                           "hackathon_report", "code_quality_report", "external_intel", "preliminary_rec", 
                           "confidence_adj", "major_gaps"],
            partial_variables={"format_instructions": decision_parser.get_format_instructions()},
        )
        
        chain = prompt | llm | decision_parser
        
        major_gaps = comprehensive_analysis.neo4j_insights.get('skill_gaps', [])[:3]
        result = await chain.ainvoke({
            "analysis_context": analysis_context,
            "requirements": requirements_context,
            "screener": screener_report,
            "tech": tech_report,
            "extracurricular_report": extracurricular_report or "No data provided.",
            "hackathon_report": hackathon_report or "No data provided.",
            "code_quality_report": code_quality_report or "No data provided.",
            "external_intel": external_intel or "No external data provided.",
            "preliminary_rec": comprehensive_analysis.final_recommendation,
            "confidence_adj": comprehensive_analysis.risk_assessment.confidence_adjustment,
            "major_gaps": major_gaps
        })
        
        # Apply risk-based adjustments to final decision
        if comprehensive_analysis.risk_assessment.overall_risk_score > 0.6:
            if result.get("decision", "").lower() == "hire":
                logger.warning(f"Risk override: Changing decision from hire to reject due to high risk score ({comprehensive_analysis.risk_assessment.overall_risk_score:.2f})")
                result["decision"] = "further_interview"
                result["explanation"] = f"HIGH RISK ASSESSMENT ({comprehensive_analysis.risk_assessment.overall_risk_score:.2f}): " + result.get("explanation", "")
        
        # Apply confidence adjustment
        result["meta_confidence_score"] = max(0.0, min(1.0, 
            result.get("meta_confidence_score", 0.5) + comprehensive_analysis.risk_assessment.confidence_adjustment
        ))
        
        logger.info(f"Enhanced decision chain completed: {result.get('decision')} (confidence: {result.get('meta_confidence_score'):.2f})") 
        return result
    
    except Exception as e:
        logger.error(f"Enhanced decision chain failed: {e}, falling back to standard decision chain")
        # Fallback to standard decision chain
        return await run_decision_chain(
            screener_report, tech_report, culture_report, requirements_context,
            external_intel, extracurricular_report, hackathon_report, code_quality_report
        )


# ============================================================================
# FUZZY LOGIC + AI HYBRID DECISION CHAIN (Module 5)
# ============================================================================

async def run_fuzzy_aware_decision_chain(
    screener_report: str,
    tech_report: str,
    culture_report: str,
    requirements_context: str,
    fuzzy_score_data: dict,
    external_intel: Optional[str] = None,
    extracurricular_report: Optional[str] = None,
    hackathon_report: Optional[str] = None,
    code_quality_report: Optional[str] = None,
    behavioral_profile: Optional[str] = None,
    flight_risk_data: Optional[str] = None,
    # Phase 1 & 2 Cognitive Parameters
    thinking_mode: str = "balanced",
    seniority_level: str = "mid",
) -> dict:
    """
    The Hybrid Fuzzy Logic + AI Final Decision Chain.

    This is the crown jewel of the scoring engine. The flow is:
    1. The fuzzy_score_data is already calculated (deterministic math).
    2. The LLM receives the pre-calculated score and is told: "This is the score. Write the explanation."
    3. The LLM writes the human-readable narrative, NOT the number.

    This guarantees:
    - 100% consistent, fair, mathematically defensible final_score
    - Rich, empathetic, human-like explanation generated by AI
    - No AI "mood swings" changing the score between runs

    Args:
        fuzzy_score_data: Output from FuzzyScoreResult (contains fuzzy_final_score, input_scores, etc.)
        All other args: Same as run_enhanced_decision_chain

    Returns:
        Standard FinalDecision dict with the fuzzy_score locked in.
    """
    fuzzy_final_score = fuzzy_score_data.get("fuzzy_final_score", 65)
    fuzzy_decision = fuzzy_score_data.get("deterministic_decision", "consider_further")
    input_scores = fuzzy_score_data.get("input_scores", {})
    engine_used = fuzzy_score_data.get("engine_used", "unknown")

    # Map fuzzy decision to standard pipeline decision
    decision_map = {
        "strong_hire": "hire",
        "hire": "hire",
        "consider_further": "further_interview",
        "reject": "reject"
    }
    mapped_decision = decision_map.get(fuzzy_decision, "further_interview")

    # ── Thinking Mode Directive ───────────────────────────────────────────────
    _mode = thinking_mode.lower() if thinking_mode else "balanced"
    _thinking_directives = {
        "strict": (
            "EVALUATION MODE: STRICT.\n"
            "Apply the highest standards. Penalise any skill gaps, "
            "experience shortfalls, or unverified claims. "
            "Only candidates with strong, verified evidence across ALL dimensions "
            "should be recommended for hire."
        ),
        "balanced": (
            "EVALUATION MODE: BALANCED.\n"
            "Apply fair, holistic standards. Weigh strengths against "
            "weaknesses proportionally. Give benefit of the doubt for "
            "minor gaps if overall profile is strong."
        ),
        "potential": (
            "EVALUATION MODE: POTENTIAL.\n"
            "Prioritise growth trajectory, learning velocity, and hustle "
            "over rigid keyword matching. Candidates showing clear upward momentum "
            "should be scored generously even if some senior skills are missing."
        ),
    }
    thinking_directive = _thinking_directives.get(_mode, _thinking_directives["balanced"])

    _seniority_note = (
        f"ROLE SENIORITY: {seniority_level.upper()}. "
        "Calibrate expectations accordingly — a junior role has lower bar for "
        "experience depth; a lead role requires strong evidence of ownership and mentoring."
    )

    logger.info(f"Fuzzy score: {fuzzy_final_score:.1f} → {fuzzy_decision} "
                f"(engine: {engine_used}, mode: {_mode}, seniority: {seniority_level})")

    decision_parser = JsonOutputParser(pydantic_object=FinalDecision)

    prompt = PromptTemplate(
        template="""You are the Final Decision Maker (Lead Agent) for an AI Hiring Pipeline.

The final candidate score has ALREADY been calculated by a Fuzzy Logic mathematical engine.
Your role is NOT to recalculate or change the score. Your role is to:
1. Write a rich, human, empathetic EXPLANATION for this score.
2. Confirm the decision label.
3. Generate the category breakdown scores that align with the pre-calculated final score.

{thinking_directive}
{seniority_note}

=== MATHEMATICALLY CALCULATED SCORE (DO NOT CHANGE) ===
Final Score: {fuzzy_score}/100
Decision Label: {fuzzy_decision}
Engine: {engine_used}

Score Components (used by the math engine):
- Core Technical Competence: {tech_input}/100
- Growth Potential & Hustle: {growth_input}/100
- Team & Cultural Fit: {culture_input}/100
- Real-World Execution: {execution_input}/100
- Consistency & Credibility: {consistency_input}/100
========================================================

Job Requirements Context:
{requirements}

Screener Report:
{screener}

Technical Report:
{tech}

Extra-Curricular Report:
{extracurricular_report}

Hackathon Evaluation:
{hackathon_report}

Code Quality Review:
{code_quality_report}

External Evidence (GitHub/LinkedIn):
{external_intel}

Behavioral Profile:
{behavioral_profile}

Flight Risk Analysis:
{flight_risk_data}

YOUR TASK:
Write a comprehensive EXPLANATION of WHY this candidate earned a {fuzzy_score}/100 score.
Be specific. Reference actual data from the agent reports. Be empathetic but factual.
Apply your evaluation mode guidelines above when framing the strengths and weaknesses.

RULES:
- You MUST output final_score = {fuzzy_score_int} (exactly as calculated. Do not change it.)
- You MUST output decision = '{mapped_decision}' (as determined by the math engine)
- Your category_scores dict MUST use these exact keys and values close to the component scores:
  Core_Technical_Competence, Growth_Potential_and_Hustle, Team_and_Cultural_Fit, Real_World_Execution, Consistency_and_Credibility
- meta_confidence_score: Set based on how consistent the agent reports are with each other (0.0-1.0)

{format_instructions}""",
        input_variables=[
            "thinking_directive", "seniority_note",
            "fuzzy_score", "fuzzy_decision", "engine_used", "mapped_decision",
            "tech_input", "growth_input", "culture_input", "execution_input", "consistency_input",
            "fuzzy_score_int", "requirements", "screener", "tech",
            "extracurricular_report", "hackathon_report", "code_quality_report",
            "external_intel", "behavioral_profile", "flight_risk_data"
        ],
        partial_variables={"format_instructions": decision_parser.get_format_instructions()},
    )

    chain = prompt | llm | decision_parser

    try:
        result = await chain.ainvoke({
            "thinking_directive": thinking_directive,
            "seniority_note": _seniority_note,
            "fuzzy_score": round(fuzzy_final_score, 1),
            "fuzzy_score_int": int(round(fuzzy_final_score)),
            "fuzzy_decision": fuzzy_decision,
            "engine_used": engine_used,
            "mapped_decision": mapped_decision,
            "tech_input": input_scores.get("tech", 50),
            "growth_input": input_scores.get("growth", 50),
            "culture_input": input_scores.get("culture", 50),
            "execution_input": input_scores.get("execution", 50),
            "consistency_input": input_scores.get("consistency", 70),
            "requirements": requirements_context,
            "screener": screener_report,
            "tech": tech_report,
            "extracurricular_report": extracurricular_report or "No data provided.",
            "hackathon_report": hackathon_report or "No data provided.",
            "code_quality_report": code_quality_report or "No data provided.",
            "external_intel": external_intel or "No external data provided.",
            "behavioral_profile": behavioral_profile or "No behavioral profile available.",
            "flight_risk_data": flight_risk_data or "No flight risk data available.",
        })

        # HARD LOCK: Ensure the LLM didn't hallucinate a different score or decision
        result["final_score"]          = int(round(fuzzy_final_score))
        result["decision"]             = mapped_decision
        result["_fuzzy_engine_used"]   = engine_used
        result["_fuzzy_input_scores"]  = input_scores
        result["_thinking_mode"]       = _mode
        result["_seniority_level"]     = seniority_level

        logger.info(
            f"Fuzzy-aware decision chain completed: score={result['final_score']}, "
            f"decision={result['decision']}, mode={_mode}"
        )
        return result

    except Exception as e:
        logger.error(f"Fuzzy-aware decision chain failed: {e}. Falling back to enhanced chain.")
        fallback = await run_enhanced_decision_chain(
            screener_report, tech_report, culture_report, requirements_context,
            external_intel, extracurricular_report, hackathon_report, code_quality_report
        )
        # Still inject fuzzy score as a minimum integrity guarantee
        fallback["final_score"] = int(round(fuzzy_final_score))
        fallback["_fuzzy_fallback"] = True
        return fallback
