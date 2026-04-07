from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from services.vector_parser import search_candidates_by_job_description
from services.db_service import get_candidate_by_id
from services.neo4j_service import kg_service
import json

async def extract_skills_from_job(job_text: str) -> list:
    """
    Uses Gemini to extract core technical skills from a job description.
    """
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=settings.GOOGLE_API_KEY,
            temperature=0.0
        )
        
        prompt = f"""
        You are a highly accurate technical skill extractor. Identify the core technical languages, frameworks, and tools required in the following job description.
        Return ONLY a JSON list of strings representing the skills.
        
        Job Description:
        {job_text}
        """
        
        response = await llm.ainvoke(prompt)
        # Handle cases where LLM returns markdown blocks
        clean_content = response.content.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_content)
    except Exception as e:
        print(f"Skill extraction failed: {e}")
        return []

async def find_top_candidates_for_job(job_text: str, job_id: str = None, k: int = 5):
    """
    Retrieves and ranks the top k candidates for a job description using 
    a hybrid of Chroma semantic search and Knowledge Graph skill mapping.
    If job_id is provided, it uses the advanced graph-traversal matching.
    """
    # 1. Semantic Search (Retrieval)
    results = search_candidates_by_job_description(job_text, k=k)
    
    # 2. Extract Required Skills (Extraction)
    required_skills = await extract_skills_from_job(job_text)
    
    # 3. Get Advanced Graph Scores (if job_id provided)
    graph_scores = {}
    if job_id:
        graph_matches = kg_service.find_graph_candidates_for_job(job_id, limit=k*2)
        for gm in graph_matches:
            # We'll normalize the graph score (e.g. 5 skills = score 5 = 100%)
            max_possible_score = max(len(required_skills), 1)
            normalized_score = min((gm["graph_score"] / max_possible_score) * 100, 100)
            graph_scores[gm["candidate_id"]] = normalized_score
    
    # 4. Re-ranking with Knowledge Graph (Refinement)
    final_matches = []
    for res in results:
        candidate_id = res["candidate_id"]
        candidate = await get_candidate_by_id(candidate_id)
        
        if not candidate:
            continue
            
        parsed_data = candidate.get("parsed_data", {})
        skills_provided = parsed_data.get("skills", [])
        
        # Calculate Hybrid Score
        # Chroma score (distance) normalized to 0-100 (assume distance < 1 for match)
        chroma_score = min(round((1 - res["score"]) * 100, 1), 100) if res["score"] < 1 else 60
        
        # Knowledge Graph Score
        if job_id and candidate_id in graph_scores:
            kg_score = graph_scores[candidate_id]
        else:
            kg_score = kg_service.calculate_match_score(required_skills, skills_provided)
        
        # Combine (weighted 40% Chroma, 60% KG for accuracy)
        hybrid_match_percentage = round((0.4 * chroma_score) + (0.6 * kg_score), 1)
        
        match_data = {
            "id": candidate_id,
            "name": res["name"],
            "score": res["score"],
            "match_percentage": hybrid_match_percentage,
            "status": candidate.get("status", "pending"),
            "final_decision": candidate.get("final_decision", "none"),
            "matched_skills": list(set(required_skills) & set(skills_provided))
        }
        
        final_matches.append(match_data)
        
    return sorted(final_matches, key=lambda x: x["match_percentage"], reverse=True)
