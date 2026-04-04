import os
import json
from mcp.server.fastmcp import FastMCP

# Import the services
from services.resume_parser import parse_resume
from services.vector_parser import embed_candidate_data, search_candidates_by_job_description
from services.db_service import initial_save_candidate, update_candidate_parsed

# Create the FastMCP server
mcp = FastMCP("TalentPartner-MCP")

@mcp.tool()
async def process_and_embed_resume(pdf_path: str, candidate_id: str, gridfs_id: str = "N/A") -> str:
    """
    Parses a PDF resume, extracts structured candidate information, 
    and embeds the data into the Vector DB. Matches exactly with 
    Steps 2, 3, 4, 5, and 6 of the 1.txt architecture document.
    
    Args:
        pdf_path (str): The absolute path to the PDF resume file.
        candidate_id (str): A unique ID for this candidate.
        gridfs_id (str): The MongoDB GridFS ID where the file is stored.
        
    Returns:
        str: A JSON string of the parsed profile, indicating it was successfully embedded.
    """
    try:
        # Step 2: Store base Resume record in MongoDB with its GridFS ID
        await initial_save_candidate(candidate_id, gridfs_id)
        
        # Step 3 & 4: Parse the resume into structured JSON
        candidate_profile = parse_resume(pdf_path, candidate_id)
        
        # Step 5: Store structured JSON back into MongoDB
        await update_candidate_parsed(candidate_id, candidate_profile)
        
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
async def parse_resume_only(pdf_path: str, candidate_id: str) -> str:
    """
    Parses a PDF resume and extracts structured candidate information, 
    WITHOUT embedding it into the Vector DB. Still updates MongoDB 
    state so it matches architectural expectations.
    
    Args:
        pdf_path (str): The absolute path to the PDF resume file.
        candidate_id (str): A unique ID for this candidate.
        
    Returns:
        str: A JSON string of the parsed profile.
    """
    try:
        await initial_save_candidate(candidate_id, pdf_path)
        candidate_profile = parse_resume(pdf_path, candidate_id)
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

if __name__ == "__main__":
    # Run the MCP server on stdio when executed directly.
    # To start an inspector using FastMCP: `mcp dev backend/mcp_server.py`
    mcp.run()
