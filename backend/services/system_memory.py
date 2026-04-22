from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.database.mongodb import get_mongodb

class LearningRule(BaseModel):
    rule_id: str = Field(..., description="Unique ID for the rule pattern")
    pattern: str = Field(..., description="The learned behavior/rule (e.g., 'Prioritize ML projects')")
    role_category: str = Field(..., description="The job category this rule applies to (e.g., 'Machine Learning')")
    confidence: float = Field(default=0.8, description="Confidence score (0.0 to 1.0)")
    version: int = Field(default=1, description="Rule version")
    previous_version: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_reinforced: datetime = Field(default_factory=datetime.utcnow)
    decay_factor: float = Field(default=0.95, description="Daily decay multiplier")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SystemMemoryService:
    """
    Manages the 'Real AI' memory: storing, decaying, and retrieving learned rules.
    """
    COLLECTION = "system_memory"

    async def get_active_rules(self, role_category: str, limit: int = 5) -> List[LearningRule]:
        """
        Retrieves top rules for a specific role, applying confidence decay on the fly.
        """
        db = get_mongodb()
        if db is None: return []

        # Find rules for this role (or generic rules)
        query = {"role_category": role_category, "confidence": {"$gt": 0.1}}
        cursor = db[self.COLLECTION].find(query).sort("confidence", -1).limit(limit)
        
        rules = []
        async for doc in cursor:
            # Apply time-based decay logic
            rule = LearningRule(**doc)
            rule = self._apply_decay(rule)
            
            # Update DB if confidence dropped significantly
            if rule.confidence < float(doc.get("confidence", 0)):
                await db[self.COLLECTION].update_one(
                    {"_id": doc["_id"]}, 
                    {"$set": {"confidence": rule.confidence}}
                )
            
            if rule.confidence > 0.3: # Only return rules with enough 'memory'
                rules.append(rule)
        
        return rules

    async def upsert_rule(self, rule_pattern: str, role_category: str, source_candidate_id: Optional[str] = None):
        """
        Learns a new rule or reinforces an existing one.
        Handles versioning and confidence boosting.
        """
        db = get_mongodb()
        if db is None: return

        # Try to find an existing rule with similar pattern (basic check)
        # In a real 'Elite' system, we'd use semantic similarity here.
        existing = await db[self.COLLECTION].find_one({
            "pattern": {"$regex": rule_pattern[:20], "$options": "i"},
            "role_category": role_category
        })

        if existing:
            # REINFORCE: Increase confidence and bump version
            new_confidence = min(1.0, existing["confidence"] + 0.1)
            new_version = existing["version"] + 1
            await db[self.COLLECTION].update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "confidence": new_confidence,
                        "version": new_version,
                        "previous_version": existing["version"],
                        "last_reinforced": datetime.utcnow()
                    },
                    "$push": {"metadata.reinforcements": {
                        "candidate_id": source_candidate_id,
                        "timestamp": datetime.utcnow()
                    }}
                }
            )
            print(f"[Memory] Reinforced Rule: {rule_pattern[:30]} (v{new_version})")
        else:
            # NEW RULE
            new_rule = LearningRule(
                rule_id=f"rule_{datetime.utcnow().timestamp()}",
                pattern=rule_pattern,
                role_category=role_category,
                metadata={"source_candidate": source_candidate_id}
            )
            await db[self.COLLECTION].insert_one(new_rule.model_dump())
            print(f"[Memory] Learned New Rule: {rule_pattern[:30]}")

    def _apply_decay(self, rule: LearningRule) -> LearningRule:
        """
        Calculates time-decayed confidence: Confidence = OldConfidence * (Decay ^ DaysPassed)
        """
        days_passed = (datetime.utcnow() - rule.last_reinforced).days
        if days_passed > 0:
            rule.confidence = round(rule.confidence * (rule.decay_factor ** days_passed), 3)
        return rule

# Decision History Tracking for Continuous Learning
async def save_hiring_decision_history(candidate_id: str, decision_data: dict) -> bool:
    """
    Tracks hiring decisions for continuous learning and rule refinement.
    Stores comprehensive decision data with all scores.
    """
    db = get_mongodb()
    if db is None:
        return False
    
    try:
        collection = db["decision_history"]
        history_entry = {
            "candidate_id": candidate_id,
            "decision": decision_data.get("decision"),
            "final_score": decision_data.get("final_score"),
            "confidence": decision_data.get("meta_confidence_score"),
            "category_scores": decision_data.get("category_scores", {}),
            "explanation": decision_data.get("explanation"),
            "recorded_at": datetime.utcnow(),
            "role_category": decision_data.get("role_category"),
            "risk_assessment": decision_data.get("risk_assessment", {}),
            "neo4j_insights": decision_data.get("neo4j_insights", {}),
            "skill_gaps": decision_data.get("skill_gaps", [])
        }
        
        result = await collection.insert_one(history_entry)
        return result.inserted_id is not None
    except Exception as e:
        import logging
        logging.error(f"Failed to save decision history: {e}")
        return False

# Singleton
memory_service = SystemMemoryService()
