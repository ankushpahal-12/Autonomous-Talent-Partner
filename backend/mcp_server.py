import os
import json
from mcp.server.fastmcp import FastMCP

# Import the services
from services.resume_parser import parse_resume_from_gridfs
from services.vector_parser import embed_candidate_data, search_candidates_by_job_description
from services.db_service import initial_save_candidate, update_candidate_parsed, get_candidate_by_id, update_candidate_review
from services.requirement_service import get_all_requirements
from services.neo4j_service import kg_service
from agents.lead_agent import run_full_candidate_review

import sys
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP
from app.database.mongodb import connect_to_mongo, close_mongo_connection
from app.database.vectordb import init_vector_db, shutdown_vector_db

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Initializes both MongoDB and Vector DB connections on server start."""
    sys.stderr.write("MCP Server Starting: Connecting to Database and Vector Store...\n")
    connect_to_mongo()
    init_vector_db()
    yield
    sys.stderr.write("MCP Server Shutting down: Closing connections...\n")
    close_mongo_connection()
    shutdown_vector_db()

# Create the FastMCP server with lifespan support
mcp = FastMCP("TalentPartner-MCP", lifespan=app_lifespan)

@mcp.tool()
async def process_and_embed_resume(candidate_id: str, gridfs_id: str) -> str:
    """
    Parses a resume from GridFS, extracts structured information, 
    and embeds the data into the Vector DB. Strictly in-memory.
    
    Args:
        candidate_id (str): A unique ID for this candidate.
        gridfs_id (str): The MongoDB GridFS ID where the file is stored.
        
    Returns:
        str: A JSON string of the parsed profile.
    """
    try:
        # Step 2: Store base Resume record in MongoDB
        await initial_save_candidate(candidate_id, gridfs_id)
        
        # Step 3 & 4: Parse the resume into structured JSON (In-Memory)
        candidate_profile = await parse_resume_from_gridfs(gridfs_id, candidate_id)
        
        # Step 5: Store structured JSON back into MongoDB
        await update_candidate_parsed(candidate_id, candidate_profile)
        
        # Step 5b: Sync to Neo4j Knowledge Graph
        # Creates (Candidate)-[:HAS_SKILL]->(Skill) edges
        kg_service.sync_candidate_to_graph(
            candidate_id=candidate_id,
            name=candidate_profile.get("name", candidate_id),
            skills=candidate_profile.get("skills", []),
            status="pending_review"
        )
        
        # Step 6: Embed into Vector DB
        success = embed_candidate_data(candidate_profile)
        
        if success:
            candidate_profile["_embedded"] = True
            return json.dumps(candidate_profile, indent=2)
        else:
            return json.dumps({"error": "Failed to embed candidate data in Chroma."})
            
    except Exception as e:
        return json.dumps({"error": str(e)})

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
        candidate_profile = await parse_resume_from_gridfs(gridfs_id, candidate_id)
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
            "rag_reasoning": report.rag_reasoning,
            "final_decision": report.final_decision,
            "rejection_feedback": report.rejection_feedback,
        }
        
        await update_candidate_review(candidate_id, report_dict)
        return json.dumps(report_dict, indent=2, default=str)
        
    except Exception as e:
        return f"Error executing review: {str(e)}"

if __name__ == "__main__":
    # Run the MCP server on stdio when executed directly.
    # To start an inspector using FastMCP: `mcp dev backend/mcp_server.py`
    mcp.run()
