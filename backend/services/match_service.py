from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from services.vector_parser import search_candidates_by_job_description
from services.db_service import get_candidate_by_id
from services.neo4j_service import kg_service
import json
import logging

logger = logging.getLogger(__name__)

async def extract_skills_from_job(job_text: str) -> list:
    """
    Uses Gemini to extract core technical skills from a job description.
    """
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=settings.get_key_for_agent(11),
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
    a hybrid of Chroma semantic search, Knowledge Graph skill mapping, and Risk Assessment.
    
    Scoring Methodology:
    - Chroma Semantic Match: 40% weight (vector similarity)
    - Knowledge Graph Match: 35% weight (skill relationships via Neo4j)
    - Risk Assessment: 25% weight (inverse of risk score for penalization)
    
    If job_id is provided, uses advanced graph-traversal matching.
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
            max_possible_score = max(len(required_skills), 1)
            normalized_score = min((gm["graph_score"] / max_possible_score) * 100, 100)
            graph_scores[gm["candidate_id"]] = normalized_score
    
    # 4. Re-ranking with Knowledge Graph & Risk Assessment (Refinement)
    final_matches = []
    for res in results:
        candidate_id = res["candidate_id"]
        candidate = await get_candidate_by_id(candidate_id)
        
        if not candidate:
            continue
            
        parsed_data = candidate.get("parsed_data", {})
        skills_provided = parsed_data.get("skills", [])
        
        # Calculate baseline scores
        chroma_score = min(round((1 - res["score"]) * 100, 1), 100) if res["score"] < 1 else 60
        
        if job_id and candidate_id in graph_scores:
            kg_score = graph_scores[candidate_id]
        else:
            kg_score = kg_service.calculate_match_score(required_skills, skills_provided)
        
        # RISK ASSESSMENT SCORING (v2.0)
        # Retrieve comprehensive scoring data if available
        risk_score = 0.5  # Default neutral risk
        final_decision_data = candidate.get("final_score_data", {})
        risk_assessment = candidate.get("risk_assessment", {})
        
        if risk_assessment:
            risk_score = risk_assessment.get("overall_risk_score", 0.5)
        elif final_decision_data:
            # Fallback: use risk from final score data
            risk_score = final_decision_data.get("risk_score", 0.5)
        
        # Risk penalty: high risk reduces match score
        # Score = Base * (1 - risk_weight * risk_score)
        risk_penalty = 1 - (0.25 * risk_score)  # Max 25% deduction for risk
        
        # Hybrid Match Score with Risk Adjustment
        # 40% Chroma, 35% KG, 25% Risk Resistance
        hybrid_match_percentage = round(
            (0.40 * chroma_score) + (0.35 * kg_score) + (0.25 * (100 * risk_penalty)),
            1
        )
        
        # Get candidate status and decision
        final_status = candidate.get("final_status", "pending")
        final_decision = final_decision_data.get("decision", "unknown") if final_decision_data else "unknown"
        final_score = final_decision_data.get("final_score", 0) if final_decision_data else 0
        
        match_data = {
            "id": candidate_id,
            "name": res["name"],
            "score": res["score"],
            "match_percentage": hybrid_match_percentage,
            "status": final_status,
            "final_decision": final_decision,
            "final_score": final_score,
            "risk_score": round(risk_score, 2),
            "matched_skills": list(set(required_skills) & set(skills_provided)),
            "chroma_score": chroma_score,
            "kg_score": kg_score,
            "risk_adjusted": risk_penalty < 1.0
        }
        
        final_matches.append(match_data)
        logger.info(f"Matched {candidate_id}: match={hybrid_match_percentage}%, risk={risk_score:.2f}")
        
    return sorted(final_matches, key=lambda x: x["match_percentage"], reverse=True)
