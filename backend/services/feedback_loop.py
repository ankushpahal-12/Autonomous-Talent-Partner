import os
from langchain_google_genai import ChatGoogleGenerativeAI
from app.database.mongodb import get_mongodb
from app.core.config import settings
from datetime import datetime
from services.system_memory import memory_service
import logging

logger = logging.getLogger(__name__)

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
            api_key=settings.get_key_for_agent(13),
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
        1. Analyze why the AI and HR disagreed.
        2. Provide a 2-3 sentence 'Learning Note' for the audit log.
        3. Identify a single 'Learning Pattern' or 'Rule' that would have prevented this mismatch.
           Format the rule as a concise instruction.
           Example: "Prioritize candidates with startup experience even if academic scores are lower."
        4. Identify the 'Role Category' this rule applies to (e.g., 'Frontend', 'DevOps', 'Machine Learning').
        """
        
        response = await llm.ainvoke(prompt)
        raw_text = response.content
        
        # Simple extraction logic (could be improved with structured output tool)
        learning_note = raw_text
        extracted_rule = ""
        role_category = "General"

        if "Rule:" in raw_text:
            extracted_rule = raw_text.split("Rule:")[1].split("\n")[0].strip()
        if "Role Category:" in raw_text:
            role_category = raw_text.split("Role Category:")[1].split("\n")[0].strip()
        
        # If extraction failed, use LLM to clean it up for our memory
        if not extracted_rule:
             clean_res = await llm.ainvoke(f"Extract just the core instruction from this audit note as a single sentence for an AI system rule:\n{learning_note}")
             extracted_rule = clean_res.content.strip()

        # 5. Store Learning Note in Logs
        feedback_entry = {
            "candidate_id": candidate_id,
            "timestamp": datetime.utcnow(),
            "ai_recommendation": ai_recommendation,
            "ai_score": ai_match_score,
            "hr_decision": final_decision,
            "hr_reason": hr_reason,
            "learning_note": learning_note,
            "extracted_rule": extracted_rule,
            "role_category": role_category,
            "gap_type": "selection_bias" if is_selection_gap else "overconfidence"
        }
        
        await db["feedback_logs"].insert_one(feedback_entry)

        # 6. ENROLL IN SYSTEM MEMORY (Real AI Evolution)
        if extracted_rule:
            await memory_service.upsert_rule(
                rule_pattern=extracted_rule,
                role_category=role_category,
                source_candidate_id=candidate_id
            )
        print(f"System Feedback Recorded for {candidate_id}: {learning_note[:50]}...")

    except Exception as e:
        print(f"Failed to generate feedback loop analysis: {e}")



async def record_comprehensive_feedback(
    candidate_id: str,
    ai_final_score: int,
    ai_risk_score: float,
    ai_decision: str,
    hr_decision: str,
    hr_reason: str = "",
    comprehensive_analysis: dict = None
):
    """
    Records feedback loop with comprehensive scoring data.
    Analyzes gap between AI comprehensive analysis and HR decision.
    Generates learning notes to improve future evaluations.
    
    Args:
        candidate_id: Candidate ID
        ai_final_score: AI final score (0-100)
        ai_risk_score: AI risk assessment (0-1)
        ai_decision: AI recommendation (hire/reject/further_interview)
        hr_decision: HR final decision (selected/rejected/pending)
        hr_reason: Reason for HR decision
        comprehensive_analysis: Full comprehensive analysis data
    """
    db = get_mongodb()
    if db is None:
        logger.warning("Database not connected for comprehensive feedback loop")
        return

    try:
        candidate = await db["candidates"].find_one({"_id": candidate_id})
        if not candidate:
            logger.warning(f"Candidate {candidate_id} not found for feedback")
            return

        # Determine gap types
        is_score_gap = abs(ai_final_score - (100 if hr_decision == "selected" else 0)) > 30
        is_risk_gap = ai_risk_score > 0.6 and hr_decision == "selected"
        is_confidence_gap = ai_final_score > 80 and hr_decision == "rejected"

        if not (is_score_gap or is_risk_gap or is_confidence_gap):
            logger.info(f"No significant gap for {candidate_id}, skipping detailed feedback")
            return

        # Generate comprehensive gap analysis
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=settings.get_key_for_agent(16),  # Unique key for second feedback (was 13, now 16)
            temperature=0.2
        )

        # Prepare analysis context
        analysis_context = ""
        if comprehensive_analysis:
            risk_assessment = comprehensive_analysis.get("risk_assessment", {})
            consistency = comprehensive_analysis.get("consistency_analysis", {})
            neo4j = comprehensive_analysis.get("neo4j_insights", {})
            
            analysis_context = f"""
COMPREHENSIVE ANALYSIS CONTEXT:
- Risk Score: {risk_assessment.get('overall_risk_score', 'N/A')}
- Skill Consistency: {consistency.get('skill_consistency', 'N/A')}
- Red Flags: {consistency.get('red_flags', [])}
- Learning Curve: {neo4j.get('learning_curve', 'unknown')}
- Skill Gaps: {neo4j.get('skill_gaps', [])}
"""

        prompt = f"""
        You are a recruitment intelligence auditor for an autonomous hiring system.
        Analyze the discrepancy between AI evaluation and HR decision.
        
        CANDIDATE: {candidate_id}
        AI Final Score: {ai_final_score}/100
        AI Risk Assessment: {ai_risk_score:.2f} (0-1)
        AI Recommendation: {ai_decision}
        HR Decision: {hr_decision}
        HR Reason: {hr_reason}
        
        {analysis_context}
        
        TASK:
        1. Identify the PRIMARY reason for the discrepancy (score gap, risk assessment, soft factors)
        2. Generate a 2-3 sentence "Learning Note" explaining the gap
        3. Extract a single actionable "Learning Rule" that would prevent this mismatch
           Format: "When [condition], [action] even if [other metric]"
        4. Assign a "Rule Category" (e.g., 'Risk Management', 'Skill Assessment', 'Bias Detection')
        5. Rate the gap severity (low/medium/high)
        
        Return as structured text with clear labels.
        """

        response = await llm.ainvoke(prompt)
        raw_text = response.content

        # Extract structured information from response
        learning_note = raw_text
        learning_rule = ""
        rule_category = "General"
        gap_severity = "medium"
        score_difference = abs(ai_final_score - (100 if hr_decision == "selected" else 0))

        # Simple extraction logic
        if "Learning Rule:" in raw_text:
            learning_rule = raw_text.split("Learning Rule:")[1].split("\n")[0].strip()
        if "Rule Category:" in raw_text:
            rule_category = raw_text.split("Rule Category:")[1].split("\n")[0].strip()
        if "Severity:" in raw_text or "severity:" in raw_text:
            sev_line = [line for line in raw_text.split("\n") if "severity" in line.lower()][0] if any("severity" in line.lower() for line in raw_text.split("\n")) else ""
            if "high" in sev_line.lower():
                gap_severity = "high"
            elif "low" in sev_line.lower():
                gap_severity = "low"

        # Store comprehensive feedback entry
        feedback_entry = {
            "candidate_id": candidate_id,
            "timestamp": datetime.utcnow(),
            "ai_final_score": ai_final_score,
            "ai_risk_score": ai_risk_score,
            "ai_decision": ai_decision,
            "hr_decision": hr_decision,
            "hr_reason": hr_reason,
            "learning_note": learning_note,
            "learning_rule": learning_rule,
            "rule_category": rule_category,
            "gap_type": "risk" if is_risk_gap else "confidence" if is_confidence_gap else "score",
            "gap_severity": gap_severity,
            "score_difference": score_difference,
            "comprehensive_analysis_snapshot": comprehensive_analysis
        }

        await db["feedback_logs"].insert_one(feedback_entry)
        logger.info(f"Comprehensive feedback recorded for {candidate_id}: gap_type={feedback_entry['gap_type']}, severity={gap_severity}")

        # Enroll learning rule in system memory
        if learning_rule:
            await memory_service.upsert_rule(
                rule_pattern=learning_rule,
                role_category=rule_category,
                source_candidate_id=candidate_id,
                severity=gap_severity
            )
            logger.info(f"System learned rule for {rule_category}: {learning_rule[:50]}...")

    except Exception as e:
        logger.error(f"Failed to record comprehensive feedback for {candidate_id}: {e}", exc_info=True)


async def get_feedback_insights(candidate_id: str = None, limit: int = 10) -> list:
    """
    Retrieves feedback logs for analysis and continuous improvement.
    
    Args:
        candidate_id: Optional specific candidate
        limit: Number of recent feedback entries to retrieve
        
    Returns:
        List of feedback entries sorted by timestamp (newest first)
    """
    db = get_mongodb()
    if db is None:
        return []

    try:
        query = {"candidate_id": candidate_id} if candidate_id else {}
        feedback_logs = []
        
        async for log in db["feedback_logs"].find(query).sort("timestamp", -1).limit(limit):
            log["_id"] = str(log["_id"])
            log["timestamp"] = log["timestamp"].isoformat() if hasattr(log.get("timestamp"), "isoformat") else str(log["timestamp"])
            feedback_logs.append(log)
        
        return feedback_logs
    except Exception as e:
        logger.error(f"Failed to retrieve feedback insights: {e}")
        return []
