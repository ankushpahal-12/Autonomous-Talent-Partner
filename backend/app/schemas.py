"""
Pydantic models for request/response validation across all API endpoints.
Ensures type safety and API documentation consistency.

Version: 2.0
Updated: April 2026
Includes comprehensive scoring, Neo4j insights, and risk assessment schemas
"""

from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# ============================================================================
# Enums
# ============================================================================

class DecisionEnum(str, Enum):
    """Valid HR decision values."""
    SELECTED = "selected"
    REJECTED = "rejected"
    PENDING = "pending"
    SHORTLISTED = "shortlisted"

class CandidateStatusEnum(str, Enum):
    """Valid candidate status values."""
    PENDING_REVIEW = "pending_review"
    PROCESSED = "processed"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    SELECTED = "selected"

# ============================================================================
# Decision/Review Requests
# ============================================================================

class CandidateDecisionRequest(BaseModel):
    """Request body for updating HR decision on a candidate."""
    decision: DecisionEnum = Field(..., description="HR decision on candidate")
    reason: Optional[str] = Field(default="", description="Reason for the decision")
    
    @validator("reason")
    def reason_not_too_long(cls, v):
        if len(v) > 1000:
            raise ValueError("Reason must be less than 1000 characters")
        return v

class CandidateReviewRequest(BaseModel):
    """Request body for AI review of a candidate."""
    candidate_id: str = Field(..., description="Candidate ID to review")
    requirement_ids: Optional[List[str]] = Field(default=None, description="Optional requirement IDs to match against")

# ============================================================================
# Response Models
# ============================================================================

class ApiResponse(BaseModel):
    """Standard API response wrapper."""
    status: str = Field(..., description="Response status (success/error)")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    request_id: Optional[str] = Field(default=None, description="Unique request ID for tracking")

class ErrorResponse(BaseModel):
    """Standard error response."""
    status: str = "error"
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Additional error details")
    request_id: Optional[str] = Field(default=None, description="Unique request ID for tracking")

# ============================================================================
# Pagination
# ============================================================================

class PaginationParams(BaseModel):
    """Query parameters for paginated endpoints."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: Optional[str] = Field(default="desc", description="Sort order (asc/desc)")

class PaginatedResponse(BaseModel):
    """Response wrapper for paginated results."""
    items: List[Dict[str, Any]] = Field(..., description="Items in current page")
    total: int = Field(..., description="Total count of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")

# ============================================================================
# Activity Logging
# ============================================================================

class ActivityLog(BaseModel):
    """Activity log entry."""
    actor: str = Field(..., description="Who performed the action (e.g., 'HR', 'System', 'AI')")
    action: str = Field(..., description="Action description")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    timestamp: datetime = Field(..., description="When the action occurred")

# ============================================================================
# Resume Upload Response
# ============================================================================

class ResumeUploadResponse(BaseModel):
    """Response from resume upload endpoint."""
    status: str = "success"
    message: str
    candidate_id: str
    gridfs_id: str
    data: Optional[Dict[str, Any]] = None

# ============================================================================
# Candidate Matching
# ============================================================================

class CandidateMatch(BaseModel):
    """A candidate match result against a job requirement."""
    candidate_id: str
    name: Optional[str]
    match_score: float = Field(..., ge=0, le=100, description="Match score 0-100")
    matched_skills: List[str]
    missing_skills: List[str]
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")

class JobMatchResponse(BaseModel):
    """Response for job matching endpoint."""
    requirement_id: str
    job_title: str
    matches: List[CandidateMatch] = Field(..., description="Top candidate matches")
    total_candidates_evaluated: int

# ============================================================================
# Health Check
# ============================================================================

class HealthCheckResponse(BaseModel):
    """Response from health check endpoint."""
    status: str = Field(..., description="Overall health status")
    version: str
    database_connected: bool
    vector_db_connected: bool
    timestamp: datetime

# ============================================================================
# Comprehensive Scoring Schemas (v2.0)
# ============================================================================

class DataAggregationSchema(BaseModel):
    """Aggregated data metrics from all sources."""
    all_skills: List[str] = Field(..., description="All skills identified across sources")
    technical_depth: float = Field(..., ge=0, le=100, description="Technical depth score")
    experience_years: Optional[float] = Field(default=0, description="Years of relevant experience")
    role_fit: float = Field(..., ge=0, le=100, description="Role fit score")
    culture_alignment: float = Field(..., ge=0, le=100, description="Culture alignment score")
    code_quality: float = Field(..., ge=0, le=100, description="Code quality score")
    external_verification: float = Field(..., ge=0, le=100, description="External verification quality")
    educational_background: str = Field(default="", description="Education summary")
    major_projects: List[str] = Field(default=[], description="Major projects mentioned")
    verified_achievements: List[str] = Field(default=[], description="Verified achievements")

class ConsistencyAnalysisSchema(BaseModel):
    """Data consistency analysis across sources."""
    timeline_consistent: bool = Field(..., description="Are resume dates consistent with external profiles?")
    skill_consistency: float = Field(..., ge=0, le=1, description="Skill consistency score across sources")
    experience_level_match: bool = Field(..., description="Does experience level match job requirement?")
    title_progression_logical: bool = Field(..., description="Is career progression logical?")
    inconsistencies: List[str] = Field(default=[], description="Specific inconsistencies found")
    red_flags: List[str] = Field(default=[], description="Red flags identified")

class Neo4jInsightsSchema(BaseModel):
    """Neo4j knowledge graph insights."""
    skill_relationships: Dict[str, List[str]] = Field(default={}, description="Required skill → candidate skills mapping")
    transferable_skills: List[str] = Field(default=[], description="Transferable skills identified")
    skill_gaps: List[str] = Field(default=[], description="Skills required but not found")
    career_path_fit: str = Field(default="unknown", description="Career path fit assessment")
    seniority_gap: int = Field(default=0, description="Seniority level gap")
    domain_specialization: str = Field(default="general", description="Domain specialization level")
    learning_curve: str = Field(default="unknown", description="Estimated learning curve")

class RiskAssessmentSchema(BaseModel):
    """Comprehensive risk assessment."""
    overall_risk_score: float = Field(..., ge=0, le=1, description="Overall risk score 0-1")
    skill_gap_risk: float = Field(..., ge=0, le=1, description="Risk from skill gaps")
    experience_risk: float = Field(..., ge=0, le=1, description="Risk from experience gaps")
    consistency_risk: float = Field(..., ge=0, le=1, description="Risk from inconsistencies")
    red_flags_count: int = Field(default=0, description="Number of red flags")
    confidence_adjustment: float = Field(default=0, description="Confidence adjustment factor")

class ComparativeAnalysisSchema(BaseModel):
    """Candidate vs role comparison analysis."""
    must_have_skills_coverage: float = Field(..., ge=0, le=1, description="Must-have skills coverage")
    nice_to_have_skills_coverage: float = Field(..., ge=0, le=1, description="Nice-to-have skills coverage")
    experience_seniority_match: str = Field(..., description="Seniority match")
    learning_potential: float = Field(..., ge=0, le=1, description="Learning potential score")
    overqualified_risk: bool = Field(default=False, description="Is candidate overqualified?")
    growth_trajectory: str = Field(..., description="Growth trajectory assessment")

class ComprehensiveScoringSchema(BaseModel):
    """Complete comprehensive scoring analysis."""
    timestamp: datetime = Field(..., description="When analysis was performed")
    data_aggregation: DataAggregationSchema = Field(..., description="Aggregated metrics")
    consistency_analysis: ConsistencyAnalysisSchema = Field(..., description="Consistency checks")
    neo4j_insights: Neo4jInsightsSchema = Field(..., description="Neo4j knowledge graph insights")
    risk_assessment: RiskAssessmentSchema = Field(..., description="Risk assessment")
    comparative_analysis: ComparativeAnalysisSchema = Field(..., description="Comparative analysis")
    confidence_factors: Dict[str, float] = Field(default={}, description="Confidence factors")
    final_recommendation: str = Field(..., description="Final recommendation")
    version: str = Field(default="2.0", description="Schema version")

class EnhancedDecisionSchema(BaseModel):
    """Enhanced decision with comprehensive analysis."""
    final_score: int = Field(..., ge=0, le=100, description="Final score 0-100")
    category_scores: Dict[str, int] = Field(..., description="Per-category scores")
    decision: str = Field(..., description="Decision: hire/reject/further_interview")
    explanation: str = Field(..., description="Detailed explanation")
    meta_confidence_score: float = Field(..., ge=0, le=1, description="Confidence in decision")

class FinalScoreDataSchema(BaseModel):
    """Final score with metadata for storage."""
    final_score: int = Field(..., ge=0, le=100, description="Final score")
    category_scores: Dict[str, int] = Field(..., description="Category scores")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence score")
    risk_score: float = Field(..., ge=0, le=1, description="Overall risk score")
    decision: str = Field(..., description="Final decision")
    explanation: str = Field(..., description="Explanation")
    scored_at: datetime = Field(..., description="When scored")
    score_version: str = Field(default="2.0", description="Score version")

class FeedbackWithScoringSchema(BaseModel):
    """Feedback loop entry with comprehensive scoring."""
    candidate_id: str = Field(..., description="Candidate ID")
    timestamp: datetime = Field(..., description="When feedback was recorded")
    ai_recommendation: str = Field(..., description="AI recommendation")
    ai_score: float = Field(..., ge=0, le=100, description="AI final score")
    ai_risk_score: float = Field(..., ge=0, le=1, description="AI risk assessment")
    hr_decision: str = Field(..., description="HR final decision")
    hr_reason: str = Field(default="", description="HR reason for decision")
    learning_note: str = Field(..., description="Learning note from gap analysis")
    extracted_rule: str = Field(default="", description="Extracted learning rule")
    role_category: str = Field(default="General", description="Role category for rule")
    gap_type: str = Field(..., description="Type of gap: selection_bias/overconfidence/alignment")
    scoring_gap: Optional[float] = Field(default=None, description="Score difference")

class EnrichedCandidateSchema(BaseModel):
    """Candidate with comprehensive scoring data."""
    candidate_id: str = Field(..., description="Candidate ID")
    name: str = Field(..., description="Candidate name")
    email: str = Field(..., description="Candidate email")
    final_score: int = Field(..., ge=0, le=100, description="Final score")
    decision: str = Field(..., description="Final decision")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    risk_score: float = Field(..., ge=0, le=1, description="Risk assessment")
    comprehensive_analysis: Optional[ComprehensiveScoringSchema] = Field(default=None, description="Full analysis")
    enhanced_decision: Optional[EnhancedDecisionSchema] = Field(default=None, description="Enhanced decision")

# ============================================================================
# Job Builder (JD) Schemas
# ============================================================================

class JobStatusEnum(str, Enum):
    DRAFT = "draft"
    REVIEWING = "reviewing"
    FINALIZED = "finalized"
    PUBLISHED = "published"

class JobRequirementDetails(BaseModel):
    skills: List[str] = Field(default=[], description="Required skills")
    experience: str = Field(default="", description="Experience level")
    education: str = Field(default="", description="Educational requirements")

class JobSuggestion(BaseModel):
    id: str = Field(..., description="Suggestion ID")
    suggested_text: str = Field(..., description="Suggested improvement")
    reason: str = Field(..., description="Why this was suggested")
    status: str = Field(default="pending", description="pending, applied, rejected")

class JobBase(BaseModel):
    title: str = Field(..., description="Job Title - Mandatory")
    description: str = Field(default="", description="Overall Job Description")
    requirements: JobRequirementDetails = Field(default_factory=JobRequirementDetails)
    source: str = Field(default="manual", description="ai/manual/upload")
    created_by: str = Field(default="HR", description="Who created this JD")

class JobCreateRequest(BaseModel):
    title: str = Field(..., description="Mandatory job title")
    text: Optional[str] = Field(default=None, description="Initial text from manual write or AI")
    source: str = Field(default="manual", description="ai/manual/upload")

class JobEditRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[JobRequirementDetails] = None

class JobResponse(JobBase):
    job_id: str
    display_id: str = Field(..., description="Readable ID like JOB-101")
    created_at: datetime
    version: int
    suggestions: List[JobSuggestion] = Field(default=[])
    status: JobStatusEnum

