import os
from langchain_google_genai import ChatGoogleGenerativeAI
from app.database.mongodb import get_mongodb
from app.core.config import settings
from datetime import datetime

async def record_system_feedback(candidate_id: str, final_decision: str, hr_reason: str = ""):
    """
    Analyzes the gap between AI recommendation and HR decision, 
    generating learning notes to refine future evaluations.
    Supports both old (lead.recommendation) and new (final_decision.decision) report schemas.
    """
    db = get_mongodb()
    if db is None:
        print("Database not connected for feedback loop.")
        return

    # 1. Fetch Candidate Data
    candidate = await db["candidates"].find_one({"_id": candidate_id})
    if not candidate:
        print(f"Candidate {candidate_id} not found for feedback analysis.")
        return

    # 2. Extract AI Recommendation — supports new (final_decision) and old (lead) schema
    agent_reports = candidate.get("agent_reports", {})

    # New schema
    ai_decision_block = agent_reports.get("final_decision", {})
    ai_recommendation = ai_decision_block.get("decision", "")
    ai_match_score = ai_decision_block.get("final_score", 0)

    # Fallback to old schema if new fields are missing
    if not ai_recommendation:
        lead_block = agent_reports.get("lead", {})
        ai_recommendation = lead_block.get("recommendation", "N/A")
        ai_match_score = lead_block.get("overall_match_score", 0)

    # 3. Identify if there's a significant gap
    is_selection_gap = (ai_recommendation in ("reject", "Reject") and final_decision == "selected")
    is_confidence_gap = (ai_match_score > 80 and final_decision == "rejected")

    if not (is_selection_gap or is_confidence_gap):
        # AI and HR were mostly in sync, no deep analysis needed
        return

    # 4. Generate AI Gap Analysis (Learning Note)
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=settings.GOOGLE_API_KEY,
            temperature=0.2
        )

        prompt = f"""
        You are a recruitment bias and quality auditor. 
        A candidate evaluation process just finished, and there was a discrepancy between the AI and the HR Lead.
        
        Candidate ID: {candidate_id}
        AI Match Score: {ai_match_score}/100
        AI Recommends: {ai_recommendation}
        HR Decision: {final_decision}
        HR Reason: {hr_reason}
        
        Resume Details: 
        {candidate.get('parsed_data', {})}
        
        TASK:
        1. Analyze why the AI might have missed the candidate's value (if HR selected) OR why the AI was overconfident (if HR rejected).
        2. Provide a 2-3 sentence 'Learning Note' for the recruitment system to refine its future evaluations.
        3. Identify any specific skill or project the AI likely undervalued.
        """
        
        response = await llm.ainvoke(prompt)
        learning_note = response.content

        # 5. Store Learning Note
        feedback_entry = {
            "candidate_id": candidate_id,
            "timestamp": datetime.utcnow(),
            "ai_recommendation": ai_recommendation,
            "ai_score": ai_match_score,
            "hr_decision": final_decision,
            "hr_reason": hr_reason,
            "learning_note": learning_note,
            "gap_type": "selection_bias" if is_selection_gap else "overconfidence"
        }
        
        await db["feedback_logs"].insert_one(feedback_entry)
        print(f"System Feedback Recorded for {candidate_id}: {learning_note[:50]}...")

    except Exception as e:
        print(f"Failed to generate feedback loop analysis: {e}")
