import httpx
import os
from app.core.config import settings
from services.db_service import get_candidate_by_id
import logging

logger = logging.getLogger(__name__)

async def trigger_n8n_selected(
    candidate_id: str,
    candidate_name: str,
    candidate_email: str,
    final_score: int = 0,
    confidence: float = 0.0,
    interview_type: str = "technical"
):
    """
    Triggers the n8n webhook for a selected candidate to send an interview link.
    
    Includes comprehensive scoring data for downstream workflows:
    - Final score and confidence
    - Interview recommendations
    - Skill gaps for interviewer preparation
    
    Args:
        candidate_id: Candidate ID
        candidate_name: Candidate name
        candidate_email: Candidate email
        final_score: Final score (0-100)
        confidence: Confidence in decision (0-1)
        interview_type: Type of interview (technical/culture/full)
    """
    url = settings.N8N_WEBHOOK_URL_SELECTED
    if not url:
        logger.warning("n8n 'Selected' webhook URL not configured")
        return
    
    try:
        # Fetch comprehensive analysis if available
        candidate = await get_candidate_by_id(candidate_id)
        neo4j_insights = {}
        skill_gaps = []
        
        if candidate:
            analysis = candidate.get("neo4j_analysis", {})
            neo4j_insights = {
                "learning_curve": analysis.get("learning_curve", "unknown"),
                "domain_specialization": analysis.get("domain_specialization"),
                "skill_gaps": analysis.get("skill_gaps", [])
            }
            skill_gaps = analysis.get("skill_gaps", [])[:3]  # Top 3 gaps for interviewer
        
        payload = {
            "event": "candidate_selected",
            "candidate_id": candidate_id,
            "name": candidate_name,
            "email": candidate_email,
            "project": settings.PROJECT_NAME,
            "scoring": {
                "final_score": final_score,
                "confidence": round(confidence * 100, 1),
                "score_version": "2.0"
            },
            "interview": {
                "type": interview_type,
                "learning_curve": neo4j_insights.get("learning_curve", "unknown"),
                "skill_gaps_for_prep": skill_gaps
            },
            "timestamp": None  # Will be set by n8n
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"✓ n8n Selected webhook triggered for {candidate_name} (score: {final_score})")
            return True
            
    except httpx.HTTPError as e:
        logger.error(f"✗ n8n Selected webhook failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error triggering Selected webhook: {e}")
        return False


async def trigger_n8n_rejected(
    candidate_id: str,
    candidate_name: str,
    candidate_email: str,
    reason: str = "",
    final_score: int = 0,
    risk_score: float = 0.0,
    feedback_message: str = ""
):
    """
    Triggers the n8n webhook for a rejected candidate to send feedback.
    
    Includes scoring details for constructive feedback:
    - Why candidate wasn't selected (score/risk factors)
    - Suggestions for improvement
    - Alternative pathways if applicable
    
    Args:
        candidate_id: Candidate ID
        candidate_name: Candidate name
        candidate_email: Candidate email
        reason: HR reason for rejection
        final_score: Final score (0-100)
        risk_score: Risk assessment score (0-1)
        feedback_message: Constructive feedback message
    """
    url = settings.N8N_WEBHOOK_URL_REJECTED
    if not url:
        logger.warning("n8n 'Rejected' webhook URL not configured")
        return
    
    try:
        # Fetch insights for feedback personalization
        candidate = await get_candidate_by_id(candidate_id)
        neo4j_insights = {}
        recommendations = []
        
        if candidate:
            analysis = candidate.get("neo4j_analysis", {})
            skill_gaps = analysis.get("skill_gaps", [])[:3]
            neo4j_insights = {
                "learning_curve": analysis.get("learning_curve", "unknown"),
                "skill_gaps": skill_gaps,
                "transferable_skills": analysis.get("transferable_skills", [])[:3]
            }
            
            # Generate improvement recommendations based on gaps
            if skill_gaps:
                recommendations.append(f"Focus on improving skills in: {', '.join(skill_gaps)}")
            if neo4j_insights.get("learning_curve") == "short":
                recommendations.append("With targeted training, you could be a strong fit for similar roles")
        
        payload = {
            "event": "candidate_rejected",
            "candidate_id": candidate_id,
            "name": candidate_name,
            "email": candidate_email,
            "project": settings.PROJECT_NAME,
            "decision": {
                "reason": reason,
                "final_score": final_score,
                "risk_assessment": round(risk_score * 100, 1)
            },
            "feedback": {
                "message": feedback_message or "Thank you for your interest. We've decided to move forward with other candidates.",
                "skill_gaps": neo4j_insights.get("skill_gaps", []),
                "recommendations": recommendations,
                "score_version": "2.0"
            },
            "timestamp": None  # Will be set by n8n
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"✓ n8n Rejected webhook triggered for {candidate_name} (score: {final_score}, risk: {risk_score:.2f})")
            return True
            
    except httpx.HTTPError as e:
        logger.error(f"✗ n8n Rejected webhook failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error triggering Rejected webhook: {e}")
        return False


async def trigger_n8n_further_review(
    candidate_id: str,
    candidate_name: str,
    candidate_email: str,
    final_score: int = 0,
    review_reason: str = ""
):
    """
    Triggers webhook for candidates requiring further review/interview.
    
    Args:
        candidate_id: Candidate ID
        candidate_name: Candidate name
        candidate_email: Candidate email
        final_score: Final score (0-100)
        review_reason: Reason for further review
    """
    url = settings.N8N_WEBHOOK_URL_SELECTED  # Use same endpoint, different event type
    if not url:
        logger.warning("n8n workflow URL not configured")
        return
    
    try:
        candidate = await get_candidate_by_id(candidate_id)
        risk_assessment = {}
        
        if candidate:
            risk_data = candidate.get("risk_assessment", {})
            risk_assessment = {
                "overall_risk": round(risk_data.get("overall_risk_score", 0.5) * 100, 1),
                "red_flags": risk_data.get("red_flags", [])[:3]
            }
        
        payload = {
            "event": "candidate_further_review",
            "candidate_id": candidate_id,
            "name": candidate_name,
            "email": candidate_email,
            "project": settings.PROJECT_NAME,
            "review": {
                "final_score": final_score,
                "reason": review_reason,
                "risk_assessment": risk_assessment,
                "next_step": "Schedule technical interview"
            },
            "timestamp": None  # Will be set by n8n
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"✓ n8n Further Review webhook triggered for {candidate_name} (score: {final_score})")
            return True
            
    except httpx.HTTPError as e:
        logger.error(f"✗ n8n Further Review webhook failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error triggering Further Review webhook: {e}")
        return False
