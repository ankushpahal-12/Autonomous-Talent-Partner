"""
MCP Server for the Autonomous Talent Partner.
Provides tools for resume parsing, embedding, and candidate evaluation.
"""

import os
import json
import sys
import logging
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path for imports
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import non-LLM dependent services
from services.vector_parser import embed_candidate_data, search_candidates_by_job_description
from services.db_service import initial_save_candidate, update_candidate_parsed, get_candidate_by_id, update_candidate_review
from services.requirement_service import get_all_requirements
from services.neo4j_service import kg_service
from agents.lead_agent import run_full_candidate_review
from app.database.connection_manager import db_manager
from app.database.vectordb import init_vector_db, shutdown_vector_db
from app.core.config import settings

# Lazy import for LLM-dependent service (avoid circular import issues)
def get_resume_parser():
    """Lazy import to avoid circular dependency issues with LLM initialization"""
    from services.resume_parser import parse_resume_from_gridfs
    return parse_resume_from_gridfs

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """
    Initializes MongoDB and Vector DB connections on server startup.
    Gracefully closes connections on shutdown.
    """
    try:
        logger.info("MCP Server: Connecting to databases...")
        
        # Connect to MongoDB with pooling
        await db_manager.connect(
            mongo_uri=settings.MONGO_URI,
            db_name=settings.DATABASE_NAME,
            pool_size=settings.MONGO_POOL_SIZE,
            timeout_ms=settings.MONGO_CONNECTION_TIMEOUT_MS
        )
        
        # Initialize Vector DB
        init_vector_db()
        logger.info("MCP Server: All databases connected successfully")
        
    except Exception as e:
        logger.error(f"MCP Server startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    try:
        logger.info("MCP Server: Shutting down...")
        await db_manager.disconnect()
        shutdown_vector_db()
        logger.info("MCP Server: Shutdown complete")
    except Exception as e:
        logger.error(f"MCP Server shutdown error: {e}", exc_info=True)

# Create FastMCP server with lifespan support
mcp = FastMCP("TalentPartner-MCP", lifespan=app_lifespan)

@mcp.tool()
async def process_and_embed_resume(candidate_id: str, gridfs_id: str) -> str:
    """
    Processes a resume from GridFS: parses it, extracts structured data,
    syncs to knowledge graph, and embeds into vector database.
    All operations performed in-memory using GridFS references.
    
    Args:
        candidate_id (str): Unique identifier for the candidate
        gridfs_id (str): MongoDB GridFS file ID for the resume PDF
        
    Returns:
        str: JSON string of the parsed and processed candidate profile
    """
    try:
        logger.info(f"Processing resume for candidate: {candidate_id}")
        
        # Step 1: Store initial candidate record
        await initial_save_candidate(candidate_id, gridfs_id)
        
        # Step 2: Parse resume from GridFS into structured JSON
        parse_resume_from_gridfs = get_resume_parser()
        candidate_profile = await parse_resume_from_gridfs(gridfs_id, candidate_id)
        
        # Validation: Check if document is actually a resume
        if not candidate_profile.get("is_resume", True):
            error_msg = "Uploaded document does not appear to be a valid Resume/CV"
            logger.warning(f"{error_msg} - {candidate_id}")
            return json.dumps({"error": error_msg})
        
        # Step 3: Store parsed data in MongoDB
        await update_candidate_parsed(candidate_id, candidate_profile)
        logger.info(f"Candidate profile stored: {candidate_id}")
        
        # Step 4: Sync candidate to Neo4j knowledge graph
        if settings.NEO4J_ENABLED:
            kg_service.sync_candidate_to_graph(
                candidate_id=candidate_id,
                name=candidate_profile.get("name", candidate_id),
                skills=candidate_profile.get("skills", []),
                status="pending_review"
            )
            logger.info(f"Synced to knowledge graph: {candidate_id}")
        
        # Step 5: Embed candidate data into vector database
        success = embed_candidate_data(candidate_profile)
        if success:
            candidate_profile["_embedded"] = True
            logger.info(f"Embedded in vector database: {candidate_id}")
            return json.dumps(candidate_profile, indent=2)
        else:
            logger.error(f"Failed to embed in vector database: {candidate_id}")
            return json.dumps({"error": "Failed to embed candidate data in vector database"})
            
    except Exception as e:
        logger.error(f"Resume processing failed for {candidate_id}: {e}", exc_info=True)
        return json.dumps({"error": f"Processing failed: {str(e)}"})

@mcp.tool()
async def search_candidate_pool(job_description: str, limit: int = 10) -> str:
    """
    Searches the candidate pool using semantic similarity against a job description.
    Returns the top N matching candidates based on vector similarity.
    
    Args:
        job_description (str): Job requirement description to search against
        limit (int): Maximum number of results to return (default: 10)
        
    Returns:
        str: JSON string containing matching candidates with scores
    """
    try:
        logger.info(f"Searching candidate pool with limit: {limit}")
        matches = await search_candidates_by_job_description(job_description, limit=limit)
        return json.dumps(matches, indent=2)
    except Exception as e:
        logger.error(f"Candidate pool search failed: {e}", exc_info=True)
        return json.dumps({"error": f"Search failed: {str(e)}"})

@mcp.tool()
async def get_candidate_ai_review(candidate_id: str) -> str:
    """
    Retrieves the AI multi-agent review report for a candidate if available.
    
    Args:
        candidate_id (str): Candidate ID to fetch review for
        
    Returns:
        str: JSON string of the AI review report or error message
    """
    try:
        candidate = await get_candidate_by_id(candidate_id)
        if not candidate:
            return json.dumps({"error": f"Candidate not found: {candidate_id}"})
        
        ai_review = candidate.get("ai_review")
        if not ai_review:
            return json.dumps({"error": f"No AI review found for {candidate_id}"})
        
        return json.dumps(ai_review, indent=2)
    except Exception as e:
        logger.error(f"Failed to fetch AI review for {candidate_id}: {e}")
        return json.dumps({"error": str(e)})

# Server info and heartbeat
@mcp.tool()
async def health_check() -> str:
    """
    Health check endpoint for the MCP server.
    Verifies database and vector DB connectivity.
    
    Returns:
        str: JSON string with health status
    """
    return json.dumps({
        "status": "healthy" if db_manager.is_connected() else "degraded",
        "database_connected": db_manager.is_connected(),
        "timestamp": __import__("datetime").datetime.utcnow().isoformat()
    })

logger.info("MCP Server initialized and ready")

@mcp.tool()
async def parse_resume_only(candidate_id: str, gridfs_id: str) -> str:
    """
    Parses a resume from GridFS without embedding it. Strictly in-memory.
    
    Args:
        candidate_id (str): A unique ID for this candidate.
        gridfs_id (str): The MongoDB GridFS ID.
        
    Returns:
        str: A JSON string of the parsed profile.
    """
    try:
        await initial_save_candidate(candidate_id, gridfs_id)
        parse_resume_from_gridfs = get_resume_parser()
        candidate_profile = await parse_resume_from_gridfs(gridfs_id, candidate_id)
        
        if not candidate_profile.get("is_resume", True):
            return json.dumps({"error": "The uploaded document does not appear to be a valid Resume or CV."})
            
        await update_candidate_parsed(candidate_id, candidate_profile)
        return json.dumps(candidate_profile, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def embed_candidate_only(candidate_json_str: str) -> str:
    """
    Takes a JSON string representing a parsed candidate profile and 
    embeds it into the Vector DB.
    
    Args:
        candidate_json_str (str): JSON representation of the candidate profile.
        
    Returns:
        str: Success or error message.
    """
    try:
        candidate_profile = json.loads(candidate_json_str)
        success = embed_candidate_data(candidate_profile)
        if success:
            return "Successfully embedded candidate data into ChromaDB."
        else:
            return "Failed to embed candidate data."
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def search_similar_candidates(job_description: str, top_k: int = 3) -> str:
    """
    Searches the Vector DB for candidates matching the provided job description.
    
    Args:
        job_description (str): The text description of the job and required skills.
        top_k (int): Number of top candidates to retrieve.
        
    Returns:
        str: JSON string of matching candidates and their scores.
    """
    try:
        results = search_candidates_by_job_description(job_description, top_k)
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
async def run_candidate_review(candidate_id: str) -> str:
    """
    Triggers the multi-agent AI pipeline for a specific candidate.
    
    Args:
        candidate_id (str): A unique ID for this candidate.
        
    Returns:
        str: A JSON string containing the complete multi-agent evaluation reports.
    """
    try:
        candidate = await get_candidate_by_id(candidate_id)
        if not candidate:
            return f"Error: Candidate with ID {candidate_id} not found."
            
        parsed_data = candidate.get("parsed_data", {})
        resume_context = f"Skills: {', '.join(parsed_data.get('skills', []))}\nProjects: {' | '.join(parsed_data.get('projects', []))}"
        
        requirements = await get_all_requirements()
        req_text = "Software Engineer Role"
        req_id = None
        if requirements:
            first_req = requirements[0]
            req_text = first_req.get("extracted_text") or first_req.get("title", "Software Engineer Role")
            req_id = first_req.get("_id")
            
        report = await run_full_candidate_review(resume_context, req_text, requirement_id=req_id)
        
        # Serialize using new CompleteAgentReport schema
        report_dict = {
            "screener": report.screener.model_dump(),
            "tech": report.tech.model_dump(),
            "culture": report.culture.model_dump(),
            "extracurricular": report.extracurricular.model_dump() if report.extracurricular else None,
            "hackathon": report.hackathon.model_dump() if report.hackathon else None,
            "code_quality": report.code_quality.model_dump() if report.code_quality else None,
            "rag_reasoning": report.rag_reasoning,
            "final_decision": report.final_decision,
            "rejection_feedback": report.rejection_feedback,
        }
        
        await update_candidate_review(candidate_id, report_dict)
        return json.dumps(report_dict, indent=2, default=str)
        
    except Exception as e:
        return f"Error executing review: {str(e)}"

from agents.scraper_agent import run_scraper_agent
from services.db_service import update_external_intel
from app.database.mongodb import get_mongodb
from typing import List, Dict, Any

@mcp.tool()
async def tool_search_candidates_in_mongo(query_text: str) -> str:
    """
    Searches MongoDB for candidates based on a text string (matches name, email, or skills).
    """
    db = get_mongodb()
    if db is None:
        return "MongoDB connection not available."
    
    collection = db["candidates"]
    candidates = []
    try:
        from bson.regex import Regex
        regex_query = Regex(f".*{query_text}.*", "i")
        cursor = collection.find({
            "$or": [
                {"parsed_data.name": regex_query},
                {"parsed_data.skills": regex_query},
                {"_id": regex_query}
            ]
        }).limit(10)
        
        async for doc in cursor:
            name = doc.get("parsed_data", {}).get("name", "Unknown")
            skills = doc.get("parsed_data", {}).get("skills", [])
            match_score = doc.get("match_score", "N/A")
            decision = doc.get("final_decision", doc.get("status", "pending"))
            candidates.append(f"ID: {doc['_id']} | Name: {name} | Score: {match_score} | Status: {decision} | Skills: {', '.join(skills)}")
            
        if not candidates:
            return f"No candidates found matching: {query_text}"
        return "\n".join(candidates)
    except Exception as e:
        return f"Error querying candidates: {str(e)}"

@mcp.tool()
def tool_get_related_skills(skill_name: str) -> str:
    """
    Queries the Neo4j Knowledge Graph to find related skills.
    """
    try:
        related = kg_service.get_related_skills(skill_name, limit=10)
        if related:
            return f"Skills related to '{skill_name}': {', '.join(related)}"
        return f"No relations found in the Knowledge Graph for '{skill_name}'."
    except Exception as e:
        return f"Error querying Knowledge Graph: {str(e)}"

@mcp.tool()
async def tool_db_save_external_eval(candidate_id: str, external_eval_json: str) -> str:
    """
    Saves external intelligence evaluation to MongoDB.
    """
    try:
        db = get_mongodb()
        if db is None:
            return json.dumps({"error": "No db"})
        import datetime
        eval_dict = json.loads(external_eval_json)
        eval_dict["evaluated_at"] = datetime.datetime.now().isoformat()
        
        await db["candidates"].update_one(
            {"_id": candidate_id},
            {"$set": {"external_evaluation": eval_dict}}
        )
        return json.dumps({"status": "success"})
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
async def tool_get_memory_clusters(role_category: str) -> str:
    """
    Fetches all learning rules grouped by role.
    """
    try:
        db = get_mongodb()
        pipeline = [
            {"$match": {"confidence": {"$gt": 0.1}}},
            {"$group": {"_id": "$role_category", "rules": {"$push": "$$ROOT"}}}
        ]
        clusters = await db["system_memory"].aggregate(pipeline).to_list(length=100)
        # Simplify serialization
        for c in clusters:
            for r in c.get("rules", []):
                if "_id" in r: r["_id"] = str(r["_id"])
                if "last_reinforced" in r: r["last_reinforced"] = str(r["last_reinforced"])
                if "created_at" in r: r["created_at"] = str(r["created_at"])
                
        return json.dumps(clusters)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
async def tool_http_get(url: str, params_json: str = "{}", headers_json: str = "{}") -> str:
    """
    General HTTP GET wrapper for external APIs.
    """
    import httpx
    from utils.api_helpers import safe_httpx_get
    
    try:
        params = json.loads(params_json)
        headers = json.loads(headers_json)
        res = await safe_httpx_get(url, params=params if params else None, headers=headers if headers else None)
        
        if res is None:
            return json.dumps({"error": "Max retries reached"})
            
        return json.dumps({
            "status_code": res.status_code,
            "text": res.text
        })
    except Exception as e:
        return json.dumps({"error": str(e)})
@mcp.tool()
async def run_external_scraper(candidate_id: str) -> str:
    """
    Triggers the External Scraper Agent for a given candidate.
    Automatically detects GitHub and LinkedIn URLs from their parsed resume,
    fetches public profile data from GitHub (repos, languages, bio),
    and stores the enrichment results in MongoDB under `external_intel`.

    Args:
        candidate_id (str): The unique candidate ID in MongoDB.

    Returns:
        str: A JSON summary of the enrichment results.
    """
    try:
        candidate = await get_candidate_by_id(candidate_id)
        if not candidate:
            return json.dumps({"error": f"Candidate '{candidate_id}' not found."})

        parsed_data = candidate.get("parsed_data", {})
        if not parsed_data:
            return json.dumps({"error": "No parsed data available. Run resume parsing first."})

        intel = await run_scraper_agent(candidate_id, parsed_data)
        await update_external_intel(candidate_id, intel)

        return json.dumps({
            "status": "enriched",
            "candidate_id": candidate_id,
            "github_user": intel.get("github", {}).get("username"),
            "github_status": intel.get("github", {}).get("status"),
            "linkedin_url": intel.get("linkedin_url"),
            "top_languages": intel.get("github", {}).get("top_languages", []),
            "public_repos": intel.get("github", {}).get("public_repos", 0),
        }, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
async def tool_db_save_complete_eval(candidate_id: str, report_json: str) -> str:
    """Saves complete evaluation to DB."""
    from services.db_service import save_complete_evaluation
    try:
        report_dict = json.loads(report_json)
        saved = await save_complete_evaluation(candidate_id, report_dict)
        return json.dumps({"saved": saved})
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
async def tool_db_get_active_rules(role_category: str) -> str:
    """Gets active memory rules."""
    from services.system_memory import memory_service
    try:
        rules = await memory_service.get_active_rules(role_category)
        return json.dumps([{"pattern": r.pattern, "confidence": r.confidence} for r in rules])
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def tool_fair_hiring_redact(resume_text: str) -> str:
    from services.fair_hiring_service import fair_hiring_service
    try:
        res = fair_hiring_service.redact_resume(resume_text)
        return json.dumps(res)
    except Exception as e:
        return json.dumps({"error": str(e)})

# ============================================================================
# NEW CHATBOT TOOLS FOR CANDIDATE INFORMATION
# ============================================================================

@mcp.tool()
async def tool_get_candidate_full_info(candidate_id: str) -> str:
    """
    Retrieves complete candidate information including profile, skills, education, 
    AI scores, external intelligence, and all evaluation reports.
    
    Perfect for chatbots that need comprehensive candidate data.
    
    Args:
        candidate_id (str): The unique candidate ID to fetch full information for
        
    Returns:
        str: JSON string containing all candidate information:
             - parsed_data (name, email, skills, education, etc.)
             - match_score and status
             - agent_reports (AI evaluation from all agents)
             - comprehensive_analysis (risk assessment, consistency, neo4j insights)
             - external_intel (GitHub, LinkedIn data)
             - final_score_data (overall score with breakdown)
    """
    try:
        candidate = await get_candidate_by_id(candidate_id)
        if not candidate:
            return json.dumps({
                "error": f"Candidate not found",
                "candidate_id": candidate_id,
                "status": "not_found"
            })
        
        # Convert ObjectId to string for JSON serialization
        if "_id" in candidate:
            candidate["_id"] = str(candidate["_id"])
        
        # Build comprehensive response
        response = {
            "status": "success",
            "candidate_id": candidate_id,
            
            # Basic Profile Information
            "profile": {
                "name": candidate.get("parsed_data", {}).get("name", "Unknown"),
                "email": candidate.get("parsed_data", {}).get("email", ""),
                "phone": candidate.get("parsed_data", {}).get("phone", ""),
                "location": candidate.get("parsed_data", {}).get("location", ""),
                "experience_years": candidate.get("parsed_data", {}).get("experience_years", 0),
                "current_status": candidate.get("status", "pending"),
            },
            
            # Skills & Competencies
            "skills": {
                "technical_skills": candidate.get("parsed_data", {}).get("skills", []),
                "soft_skills": candidate.get("parsed_data", {}).get("soft_skills", []),
                "tools_and_frameworks": candidate.get("parsed_data", {}).get("tools", []),
            },
            
            # Education & Certifications
            "education": {
                "degrees": candidate.get("parsed_data", {}).get("education", []),
                "certifications": candidate.get("parsed_data", {}).get("certifications", []),
            },
            
            # Experience
            "experience": {
                "total_years": candidate.get("parsed_data", {}).get("experience_years", 0),
                "projects": candidate.get("parsed_data", {}).get("projects", []),
                "hackathons": candidate.get("parsed_data", {}).get("hackathons", []),
                "extracurricular": candidate.get("parsed_data", {}).get("extracurricular_activities", []),
            },
            
            # AI Evaluation Scores
            "ai_scores": {
                "overall_score": candidate.get("match_score", 0),
                "final_decision": candidate.get("agent_reports", {}).get("final_decision", {}).get("decision", "pending"),
                "final_score": candidate.get("agent_reports", {}).get("final_decision", {}).get("final_score", 0),
                "tech_score": candidate.get("agent_reports", {}).get("tech", {}).get("technical_score", 0),
                "culture_fit": candidate.get("agent_reports", {}).get("culture", {}).get("culture_fit_score", 0),
                "screener_score": candidate.get("agent_reports", {}).get("screener", {}).get("score", 0),
            },
            
            # Risk Assessment
            "risk_assessment": candidate.get("comprehensive_analysis", {}).get("risk_assessment", {}),
            
            # Consistency Analysis
            "consistency": candidate.get("comprehensive_analysis", {}).get("consistency_analysis", {}),
            
            # Neo4j Intelligence
            "neo4j_insights": candidate.get("comprehensive_analysis", {}).get("neo4j_insights", {}),
            
            # External Intelligence
            "external_intelligence": {
                "github": candidate.get("external_intel", {}).get("github", {}),
                "linkedin": candidate.get("external_intel", {}).get("linkedin", {}),
                "enrichment_status": candidate.get("external_intel", {}).get("enrichment_status", "pending"),
            },
            
            # HR Decision
            "hr_decision": candidate.get("hr_decision", None),
            
            # Interview Details
            "interview_info": {
                "interview_date": candidate.get("interview_date"),
                "interview_time": candidate.get("interview_time"),
                "interviewer_name": candidate.get("interviewer_name"),
                "meeting_link": candidate.get("meeting_link"),
            },
            
            # Flight Risk
            "retention_risk": candidate.get("agent_reports", {}).get("flight_risk", None),
        }
        
        return json.dumps(response, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error fetching candidate full info: {e}", exc_info=True)
        return json.dumps({
            "error": str(e),
            "candidate_id": candidate_id,
            "status": "error"
        })

@mcp.tool()
async def tool_get_candidate_overall_score(candidate_id: str) -> str:
    """
    Retrieves the overall AI score and decision for a candidate.
    Includes score breakdown by category and confidence metrics.
    
    Perfect for quick chatbot queries about candidate ratings.
    
    Args:
        candidate_id (str): The unique candidate ID to fetch score for
        
    Returns:
        str: JSON containing:
             - overall_score (0-100)
             - final_decision (hire, reject, further_interview, etc.)
             - category_scores breakdown (tech, culture, screener, etc.)
             - confidence level
             - risk assessment score
             - elo ranking (percentile position)
    """
    try:
        candidate = await get_candidate_by_id(candidate_id)
        if not candidate:
            return json.dumps({
                "error": f"Candidate not found: {candidate_id}",
                "candidate_id": candidate_id,
                "status": "not_found",
                "overall_score": None
            })
        
        # Get final decision data
        agent_reports = candidate.get("agent_reports", {})
        final_decision = agent_reports.get("final_decision", {})
        
        # Extract comprehensive analysis
        comprehensive = candidate.get("comprehensive_analysis", {})
        
        # Build score response
        response = {
            "status": "success",
            "candidate_id": candidate_id,
            "candidate_name": candidate.get("parsed_data", {}).get("name", "Unknown"),
            
            # Overall Rating
            "overall_score": final_decision.get("final_score") or candidate.get("match_score", 0),
            "final_decision": final_decision.get("decision", "pending"),
            "decision_explanation": final_decision.get("explanation", "No explanation available"),
            
            # Score Breakdown by Category
            "category_scores": final_decision.get("category_scores", {
                "technical_skill": agent_reports.get("tech", {}).get("technical_score", 0),
                "screener_fit": agent_reports.get("screener", {}).get("score", 0),
                "culture_alignment": agent_reports.get("culture", {}).get("culture_fit_score", 0),
                "code_quality": agent_reports.get("code_quality", {}).get("score", 0),
            }),
            
            # Confidence Metrics
            "confidence": {
                "meta_confidence": final_decision.get("meta_confidence_score", 0),
                "confidence_factors": comprehensive.get("confidence_factors", {}),
            },
            
            # Risk Profile
            "risk_profile": {
                "overall_risk_score": comprehensive.get("risk_assessment", {}).get("overall_risk_score", 0),
                "skill_gap_risk": comprehensive.get("risk_assessment", {}).get("skill_gap_risk", 0),
                "experience_risk": comprehensive.get("risk_assessment", {}).get("experience_risk", 0),
                "consistency_risk": comprehensive.get("risk_assessment", {}).get("consistency_risk", 0),
                "red_flags_count": comprehensive.get("risk_assessment", {}).get("red_flags_count", 0),
            },
            
            # Ranking / Percentile
            "ranking": {
                "elo_ranking": agent_reports.get("elo_ranking", {}).get("rank_in_pool"),
                "percentile": agent_reports.get("elo_ranking", {}).get("percentile"),
                "pool_average": agent_reports.get("elo_ranking", {}).get("pool_avg_score"),
                "pool_highest": agent_reports.get("elo_ranking", {}).get("pool_highest_score"),
            },
            
            # Quick Recommendation
            "quick_recommendation": {
                "hire": final_decision.get("decision", "").lower() in ["hire", "selected"],
                "reject": final_decision.get("decision", "").lower() == "rejected",
                "further_interview": final_decision.get("decision", "").lower() == "further_interview",
                "score_color": "green" if final_decision.get("final_score", 0) >= 80 
                               else "yellow" if final_decision.get("final_score", 0) >= 60 
                               else "red",
            }
        }
        
        return json.dumps(response, indent=2, default=str)
        
    except Exception as e:
        logger.error(f"Error fetching candidate overall score: {e}", exc_info=True)
        return json.dumps({
            "error": str(e),
            "candidate_id": candidate_id,
            "status": "error",
            "overall_score": None
        })

if __name__ == "__main__":
    # Run the MCP server on stdio when executed directly.
    mcp.run()
