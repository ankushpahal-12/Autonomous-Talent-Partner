import asyncio
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from services.system_memory import memory_service, LearningRule
from utils.mcp_client import mcp_client_manager

class LearningSupervisorAgent:
    """
    The 'Learning Supervisor' (Real AI Meta-Agent).
    Tasked with monitoring all feedback, merging similar rules (Rule Clustering),
    removing redundant rules, and suggesting version upgrades.
    """

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=settings.get_key_for_agent(14),
            temperature=0.1
        )

    async def run_maintenance_cycle(self):
        """
        Periodically reviews system memory to keep rules high quality via MCP.
        """
        print("[Supervisor] Starting Meta-Learning Maintenance Cycle...")
        
        try:
            res_str = await mcp_client_manager.invoke_tool(
                agent_id="learning_supervisor",
                tool_name="tool_get_memory_clusters",
                arguments={"role_category": "ALL"} # mcp tool just fetches all right now
            )
            if not res_str:
                return
            
            import json
            clusters = json.loads(res_str)
            if isinstance(clusters, dict) and "error" in clusters:
                print(f"[Supervisor] Error from MCP: {clusters['error']}")
                return
        except Exception as e:
            print(f"[Supervisor] MCP invoke failed: {e}")
            return

        for cluster in clusters:
            role = cluster.get("_id", "Unknown")
            rules = cluster.get("rules", [])
            
            if len(rules) < 2: continue

            print(f"[Supervisor] Analyzing {len(rules)} rules for role: {role}")
            
            # 2. Ask LLM to cluster or find redundant rules
            prompt = f"""
            You are a Meta-Learning Supervisor for an AI Recruitment System.
            Below are rules the system has learned for the role category: '{role}'.
            
            RULES:
            {rules}
            
            TASK:
            1. Identify any rules that are redundant or contradictory.
            2. For redundant rules, suggest which one to keep (usually higher version or higher confidence).
            3. If multiple rules cover the same theme, suggest a single 'Clustered Rule' that merges them.
            4. Identify any objectively bad or outdated rules that should be removed.
            
            Return your findings in JSON format:
            {{
                "to_remove": ["rule_id_1", "rule_id_2"],
                "to_merge": [
                    {{
                        "source_ids": ["id3", "id4"],
                        "merged_pattern": "New unified rule pattern here",
                        "reason": "description"
                    }}
                ]
            }}
            """
            try:
                # Use structured output if possible, or parse response
                # For brevity, we assume JSON parsing or a dedicated schema
                response = await self.llm.ainvoke(prompt)
                # (Logic to parse JSON and apply changes to MongoDB would go here)
                # In this v1, we focus on the potential to merge.
                print(f"[Supervisor] Rule Optimization Report for {role}: {response.content[:100]}...")
            except Exception as e:
                print(f"[Supervisor] Error in maintenance for {role}: {e}")

    async def resolve_rule_conflicts(self, rules: List[LearningRule]) -> List[LearningRule]:
        """
        Implements the Elite Conflict Resolver: 
        rule_score = confidence * recency * relevance
        """
        if not rules: return []

        now = datetime.utcnow()
        scored_rules = []

        for rule in rules:
            # recency = 1 / (1 + days_since_last_reinforced)
            days = (now - rule.last_reinforced).days
            recency = 1.0 / (1.0 + days)
            
            # Relevance is currently 1.0 (placeholder for semantic matching)
            relevance = 1.0 
            
            weighted_score = rule.confidence * recency * relevance
            scored_rules.append((weighted_score, rule))

        # Sort by weighted score and return sorted rules
        scored_rules.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in scored_rules]

# Singleton instance
supervisor_agent = LearningSupervisorAgent()
