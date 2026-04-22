from app.database.mongodb import get_mongodb, connect_to_mongo
from datetime import datetime

async def _get_collection():
    """Helper to ensure DB connection is active and returns the candidates collection."""
    db = get_mongodb()
    if db is None:
        # DB connection hasn't been established yet (e.g. running outside FastAPI)
        connect_to_mongo()
        db = get_mongodb()
        
    if db is None:
        return None # Failed to connect, gracefully fallback
        
    return db["candidates"]

async def initial_save_candidate(candidate_id: str, gridfs_id: str) -> bool:
    """
    Step 2 from 1.txt: Save initial upload state of the candidate with GridFS ID.
    """
    collection = await _get_collection()
    if collection is None:
        return False
        
    document = {
        "_id": candidate_id,
        "gridfs_id": gridfs_id,
        "status": "uploaded",
        "parsed": False
    }
    
    try:
        # Use upsert to handle if run multiple times
        await collection.update_one(
            {"_id": candidate_id},
            {"$set": document},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Failed to save initial candidate: {e}")
        return False

async def update_candidate_parsed(candidate_id: str, parsed_data: dict) -> bool:
    """
    Step 5 from 1.txt: Update candidate record with the JSON structured data.
    """
    collection = await _get_collection()
    if collection is None:
        return False
        
    document_update = {
        "parsed_data": parsed_data,
        "status": "processed",
        "parsed": True
    }
    
    try:
        await collection.update_one(
            {"_id": candidate_id},
            {"$set": document_update}
        )
        return True
    except Exception as e:
        print(f"Failed to update parsed candidate data: {e}")
        return False

async def get_all_candidates():
    """Retrieve all candidate records from MongoDB."""
    collection = await _get_collection()
    if collection is None:
        return []
    
    candidates = []
    async for doc in collection.find({}):
        candidates.append(doc)
    return candidates

async def get_candidate_by_id(candidate_id: str):
    """Retrieve a single candidate record by ID."""
    collection = await _get_collection()
    if collection is None:
        return None
    
    return await collection.find_one({"_id": candidate_id})

async def update_candidate_decision(candidate_id: str, decision: str, reason: str = ""):
    """
    Step 11 & 15: Save final decision and triggers the next stage.
    Persists decision to both hr_decision and status fields for consistency.
    """
    collection = await _get_collection()
    if collection is None:
        return False
    
    # Map decision to status that frontend can recognize
    status_map = {
        "selected": "shortlisted",
        "rejected": "rejected"
    }
    mapped_status = status_map.get(decision, decision)
    
    update_doc = {
        "hr_decision": decision,  # 'selected' or 'rejected' - highest priority for deriveStatus
        "hr_feedback": reason,
        "status": mapped_status,  # 'shortlisted' or 'rejected' - fallback for deriveStatus
        "reviewed_by": "HR",
        "decided_at": datetime.utcnow().isoformat()
    }
    
    # Also update ai_report.final_decision for consistency
    try:
        candidate = await collection.find_one({"_id": candidate_id})
        if candidate:
            ai_report = candidate.get("ai_report", {})
            ai_report["final_decision"] = "SHORTLISTED" if decision == "selected" else "REJECTED"
            update_doc["ai_report"] = ai_report
        
        await collection.update_one(
            {"_id": candidate_id},
            {"$set": update_doc}
        )
        return True
    except Exception as e:
        print(f"Failed to update decision: {e}")
        return False

async def update_candidate_review(candidate_id: str, agent_reports: dict) -> bool:
    """
    Saves the complete AI multi-agent evaluation reports to MongoDB.
    Works with both the old schema (lead key) and new schema (final_decision key).
    """
    collection = await _get_collection()
    if collection is None:
        return False

    # Support both old schema (lead.overall_match_score) and new schema (final_decision.final_score)
    final_decision = agent_reports.get("final_decision", {})
    lead_fallback = agent_reports.get("lead", {})
    match_score = (
        final_decision.get("final_score")
        or lead_fallback.get("overall_match_score")
        or 0
    )

    status = "rejected" if match_score < 60 else "ai_reviewed"
    
    update_doc = {
        "agent_reports": agent_reports,
        "match_score": match_score,
        "status": status
    }
    
    try:
        await collection.update_one(
            {"_id": candidate_id},
            {"$set": update_doc}
        )
        return True
    except Exception as e:
        print(f"Failed to update candidate review: {e}")
        return False


async def delete_candidate(candidate_id: str) -> bool:
    """
    Permanently removes a candidate record from MongoDB.
    """
    collection = await _get_collection()
    if collection is None:
        return False
    try:
        result = await collection.delete_one({"_id": candidate_id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Failed to delete candidate '{candidate_id}': {e}")
        return False


async def update_external_intel(candidate_id: str, intel: dict) -> bool:
    """
    Stores external enrichment data (GitHub stats, LinkedIn summary)
    under the candidate's `external_intel` field.
    """
    collection = await _get_collection()
    if collection is None:
        return False
    try:
        await collection.update_one(
            {"_id": candidate_id},
            {"$set": {"external_intel": intel, "enriched": True}}
        )
        return True
    except Exception as e:
        print(f"Failed to update external intel for '{candidate_id}': {e}")
        return False


async def save_complete_evaluation(
    candidate_id: str,
    complete_report: dict
) -> bool:
    """
    Saves the COMPLETE candidate evaluation to MongoDB.
    
    Includes:
    - All agent reports (screener, tech, culture, etc.)
    - External intelligence scores and evidence
    - Final decision with reasoning and confidence
    - Performance metrics
    - Audit trails
    
    Args:
        candidate_id: Candidate ID
        complete_report: CompleteAgentReport as dict
        
    Returns:
        True if saved successfully
    """
    collection = await _get_collection()
    if collection is None:
        return False
    
    try:
        evaluation_doc = {
            "screener_report": complete_report.get("screener"),
            "tech_report": complete_report.get("tech"),
            "culture_report": complete_report.get("culture"),
            "extracurricular_report": complete_report.get("extracurricular"),
            "hackathon_report": complete_report.get("hackathon"),
            "code_quality_report": complete_report.get("code_quality"),
            "skill_counts": complete_report.get("skill_counts"),
            
            # External intelligence
            "external_intel": complete_report.get("external_intel"),
            "external_evaluation": complete_report.get("external_evaluation"),
            
            # Context
            "rag_reasoning": complete_report.get("rag_reasoning"),
            
            # Final decision
            "final_decision": complete_report.get("final_decision"),
            "rejection_feedback": complete_report.get("rejection_feedback"),
            
            # Audit
            "bias_audit_log": complete_report.get("bias_audit_log"),
            "performance_metrics": complete_report.get("performance_metrics"),
            
            "evaluated_at": datetime.utcnow().isoformat(),
            "evaluation_status": "complete"
        }
        
        await collection.update_one(
            {"_id": candidate_id},
            {
                "$set": {
                    "complete_evaluation": evaluation_doc,
                    "last_evaluated": datetime.utcnow().isoformat()
                }
            }
        )
        
        return True
    except Exception as e:
        print(f"Failed to save complete evaluation for '{candidate_id}': {e}")
        return False


async def get_complete_evaluation(candidate_id: str) -> dict:
    """
    Retrieves the complete evaluation for a candidate.
    
    Returns:
        Complete evaluation dict or empty dict if not found
    """
    collection = await _get_collection()
    if collection is None:
        return {}
    
    try:
        candidate = await collection.find_one({"_id": candidate_id})
        if candidate:
            return candidate.get("complete_evaluation", {})
        return {}
    except Exception as e:
        print(f"Failed to get complete evaluation: {e}")
        return {}

# ============================================================================
# COMPREHENSIVE SCORE STORAGE (NEW FEATURES)
# ============================================================================

async def save_comprehensive_scoring_data(
    candidate_id: str,
    scoring_data: dict
) -> bool:
    """
    Saves comprehensive scoring data including:
    - Data aggregation results
    - Consistency analysis
    - Neo4j insights
    - Risk assessment
    - Comparative analysis
    - Final scores and recommendations
    
    Args:
        candidate_id: Candidate ID
        scoring_data: Complete scoring analysis from enhanced decision service
        
    Returns:
        True if saved successfully
    """
    collection = await _get_collection()
    if collection is None:
        return False
    
    try:
        score_doc = {
            "data_aggregation": scoring_data.get("data_aggregation", {}),
            "consistency_analysis": scoring_data.get("consistency_analysis", {}),
            "neo4j_insights": scoring_data.get("neo4j_insights", {}),
            "risk_assessment": scoring_data.get("risk_assessment", {}),
            "comparative_analysis": scoring_data.get("comparative_analysis", {}),
            "confidence_factors": scoring_data.get("confidence_factors", {}),
            "final_recommendation": scoring_data.get("final_recommendation"),
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0"
        }
        
        await collection.update_one(
            {"_id": candidate_id},
            {"$set": {"comprehensive_scoring": score_doc}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Failed to save comprehensive scoring: {e}")
        return False

async def save_final_score_with_metadata(
    candidate_id: str,
    final_score: int,
    category_scores: dict,
    confidence_score: float,
    decision: str,
    explanation: str,
    risk_score: float = 0.0
) -> bool:
    """
    Saves final decision score with full metadata and audit trail.
    
    Args:
        candidate_id: Candidate ID
        final_score: Final score (0-100)
        category_scores: Dict of individual category scores
        confidence_score: Confidence in decision (0-1)
        decision: 'hire', 'reject', or 'further_interview'
        explanation: Detailed explanation
        risk_score: Overall risk score (0-1)
        
    Returns:
        True if saved successfully
    """
    collection = await _get_collection()
    if collection is None:
        return False
    
    try:
        final_score_doc = {
            "final_score": final_score,
            "category_scores": category_scores,
            "confidence_score": confidence_score,
            "risk_score": risk_score,
            "decision": decision,
            "explanation": explanation,
            "scored_at": datetime.utcnow().isoformat(),
            "score_version": "2.0"
        }
        
        # Determine status based on score and decision
        if decision == "hire":
            status = "hired"
        elif decision == "reject":
            status = "rejected"
        else:
            status = "further_interview"
        
        await collection.update_one(
            {"_id": candidate_id},
            {
                "$set": {
                    "final_score_data": final_score_doc,
                    "final_status": status,
                    "last_scored": datetime.utcnow().isoformat()
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Failed to save final score: {e}")
        return False

async def save_neo4j_analysis_results(
    candidate_id: str,
    neo4j_results: dict
) -> bool:
    """
    Saves Neo4j knowledge graph analysis results.
    
    Stores:
    - Skill relationships and gaps
    - Career path assessment
    - Learning curve estimation
    - Domain specialization
    
    Args:
        candidate_id: Candidate ID
        neo4j_results: Neo4j analysis results
        
    Returns:
        True if saved successfully
    """
    collection = await _get_collection()
    if collection is None:
        return False
    
    try:
        neo4j_doc = {
            "skill_relationships": neo4j_results.get("skill_relationships", {}),
            "transferable_skills": neo4j_results.get("transferable_skills", []),
            "skill_gaps": neo4j_results.get("skill_gaps", []),
            "career_path_fit": neo4j_results.get("career_path_fit"),
            "seniority_gap": neo4j_results.get("seniority_gap", 0),
            "domain_specialization": neo4j_results.get("domain_specialization"),
            "learning_curve": neo4j_results.get("learning_curve"),
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
        await collection.update_one(
            {"_id": candidate_id},
            {"$set": {"neo4j_analysis": neo4j_doc}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Failed to save Neo4j analysis: {e}")
        return False

async def save_risk_assessment_results(
    candidate_id: str,
    risk_data: dict
) -> bool:
    """
    Saves risk assessment results including:
    - Skill gap risk
    - Experience risk
    - Consistency risk
    - Overall risk score
    - Red flags
    
    Args:
        candidate_id: Candidate ID
        risk_data: Risk assessment data
        
    Returns:
        True if saved successfully
    """
    collection = await _get_collection()
    if collection is None:
        return False
    
    try:
        risk_doc = {
            "overall_risk_score": risk_data.get("overall_risk_score", 0.0),
            "skill_gap_risk": risk_data.get("skill_gap_risk", 0.0),
            "experience_risk": risk_data.get("experience_risk", 0.0),
            "consistency_risk": risk_data.get("consistency_risk", 0.0),
            "red_flags_count": risk_data.get("red_flags_count", 0),
            "red_flags": risk_data.get("red_flags", []),
            "confidence_adjustment": risk_data.get("confidence_adjustment", 0.0),
            "assessed_at": datetime.utcnow().isoformat()
        }
        
        await collection.update_one(
            {"_id": candidate_id},
            {"$set": {"risk_assessment": risk_doc}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Failed to save risk assessment: {e}")
        return False

async def get_candidate_final_score(candidate_id: str) -> dict:
    """
    Retrieves the final score data for a candidate.
    
    Returns:
        Final score data or empty dict if not found
    """
    collection = await _get_collection()
    if collection is None:
        return {}
    
    try:
        candidate = await collection.find_one({"_id": candidate_id})
        if candidate:
            return candidate.get("final_score_data", {})
        return {}
    except Exception as e:
        print(f"Failed to get final score: {e}")
        return {}

async def get_candidate_scores_history(candidate_id: str) -> list:
    """
    Retrieves all scoring attempts for a candidate (historical tracking).
    
    Returns:
        List of score attempts with timestamps
    """
    collection = await _get_collection()
    if collection is None:
        return []
    
    try:
        candidate = await collection.find_one({"_id": candidate_id})
        if candidate:
            scores_history = candidate.get("scores_history", [])
            return sorted(scores_history, key=lambda x: x.get("scored_at", ""), reverse=True)
        return []
    except Exception as e:
        print(f"Failed to get scores history: {e}")
        return []

async def archive_previous_score(
    candidate_id: str,
    current_score_data: dict
) -> bool:
    """
    Archives previous score when new scoring is done.
    Keeps full history for audit and comparison.
    
    Args:
        candidate_id: Candidate ID
        current_score_data: Score data to be archived
        
    Returns:
        True if archived successfully
    """
    collection = await _get_collection()
    if collection is None:
        return False
    
    try:
        await collection.update_one(
            {"_id": candidate_id},
            {
                "$push": {
                    "scores_history": {
                        **current_score_data,
                        "archived_at": datetime.utcnow().isoformat()
                    }
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Failed to archive score: {e}")
        return False
