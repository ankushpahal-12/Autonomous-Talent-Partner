"""
Hybrid Memory-Aware Agent Layer
==========================================
Provides a unified memory interface that combines:

  Branch A — Vector DB (ChromaDB)
    → Semantic similarity search for past similar candidates
    → Pattern recognition: "This profile is similar to X, who was rejected for Y"

  Branch B — MongoDB (Structured)
    → Active learning rules retrieved via system_memory.py
    → Exact filter queries for structured rules

Both branches are queried and their results are merged into a
`MemoryContext` object which is passed to agents as `past_feedback_summary`.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from app.database.mongodb import get_mongodb
from services.system_memory import memory_service
from services.vector_parser import get_vector_store

logger = logging.getLogger(__name__)


@dataclass
class SimilarCandidateRecord:
    """A past candidate similar to the current one (from vector search)."""
    candidate_id: str
    name: str
    similarity_score: float          # Lower = more similar in Chroma (L2 distance)
    decision: str                    # 'hired', 'rejected', 'shortlisted', etc.
    rejection_reason: Optional[str] = None
    final_score: Optional[float] = None
    key_skills: List[str] = field(default_factory=list)


@dataclass
class LearnedRule:
    """A structured rule learned from past decisions (from MongoDB)."""
    pattern: str
    confidence: float
    role_category: str


@dataclass
class MemoryContext:
    """
    Combined output of both memory branches.
    This is serialised into a human-readable summary and
    injected into agent prompts as `past_feedback_summary`.
    """
    similar_past_candidates: List[SimilarCandidateRecord] = field(default_factory=list)
    learned_rules: List[LearnedRule] = field(default_factory=list)
    role_category: str = "General"

    def to_prompt_summary(self) -> str:
        """
        Convert memory context into a concise text block for agent prompt injection.
        Returns empty string if no memory is available.
        """
        lines: List[str] = []

        if self.similar_past_candidates:
            lines.append("【Similar Past Candidates (Vector Similarity)】")
            for c in self.similar_past_candidates[:3]:  # top 3 only
                decision_label = c.decision.upper() if c.decision else "UNKNOWN"
                line = (
                    f"  • {c.name} [{decision_label}]"
                    f" | Score: {c.final_score or 'N/A'}"
                    f" | Similarity: {c.similarity_score:.3f}"
                )
                if c.rejection_reason:
                    line += f" | Rejected for: {c.rejection_reason}"
                if c.key_skills:
                    line += f" | Skills: {', '.join(c.key_skills[:4])}"
                lines.append(line)

        if self.learned_rules:
            lines.append("【Learned Hiring Rules (MongoDB)】")
            for rule in self.learned_rules[:4]:  # top 4 rules
                lines.append(
                    f"  • [Confidence {rule.confidence:.0%}] {rule.pattern}"
                )

        if not lines:
            return ""

        header = f"\n=== Memory Context for Role: {self.role_category} ===\n"
        return header + "\n".join(lines) + "\n"


async def _query_vector_memory(
    resume_text: str,
    k: int = 5,
) -> List[SimilarCandidateRecord]:
    """
    Query ChromaDB for the k most semantically similar past candidates.

    Returns list of SimilarCandidateRecord sorted by similarity (ascending distance).
    """
    try:
        vector_store = get_vector_store(collection_name="candidates")
        results = vector_store.similarity_search_with_score(resume_text[:2000], k=k)

        records: List[SimilarCandidateRecord] = []
        for doc, score in results:
            meta = doc.metadata or {}
            records.append(SimilarCandidateRecord(
                candidate_id=meta.get("candidate_id", "unknown"),
                name=meta.get("name", "Unknown"),
                similarity_score=float(score),
                decision=meta.get("status", "unknown"),
                rejection_reason=meta.get("rejection_reason"),
                final_score=meta.get("final_score"),
                key_skills=meta.get("skills", []) if isinstance(meta.get("skills"), list) else [],
            ))

        logger.info(f"[HybridMemory] Vector branch: found {len(records)} similar candidates.")
        return records

    except Exception as e:
        logger.warning(f"[HybridMemory] Vector branch failed (non-critical): {e}")
        return []



async def _query_relational_memory(
    role_category: str,
    limit: int = 5,
) -> List[LearnedRule]:
    """
    Query MongoDB system_memory for high-confidence hiring rules for this role.

    Returns list of LearnedRule sorted by confidence descending.
    """
    try:
        raw_rules = await memory_service.get_active_rules(
            role_category=role_category,
            limit=limit,
        )
        rules = [
            LearnedRule(
                pattern=r.pattern,
                confidence=r.confidence,
                role_category=r.role_category,
            )
            for r in raw_rules
            if r.confidence >= 0.4  # Only confident rules
        ]
        logger.info(f"[HybridMemory] MongoDB branch: found {len(rules)} active rules for '{role_category}'.")
        return rules

    except Exception as e:
        logger.warning(f"[HybridMemory] MongoDB branch failed (non-critical): {e}")
        return []


async def build_memory_context(
    resume_text: str,
    role_category: str,
    k_similar: int = 5,
    rules_limit: int = 5,
) -> MemoryContext:
    """
    Run both memory branches in parallel (conceptually) and merge results.

    Args:
        resume_text: Current candidate's resume text (used for vector similarity).
        role_category: Role category string used to look up MongoDB rules.
        k_similar: Number of similar past candidates to retrieve.
        rules_limit: Max number of learning rules to retrieve.

    Returns:
        MemoryContext with data from both branches merged.
    """
    import asyncio

    # Run both branches concurrently
    vector_task = _query_vector_memory(resume_text, k=k_similar)
    relational_task = _query_relational_memory(role_category, limit=rules_limit)

    similar_candidates, learned_rules = await asyncio.gather(
        vector_task, relational_task, return_exceptions=True
    )

    if isinstance(similar_candidates, Exception):
        logger.warning(f"[HybridMemory] Vector branch raised: {similar_candidates}")
        similar_candidates = []

    if isinstance(learned_rules, Exception):
        logger.warning(f"[HybridMemory] Relational branch raised: {learned_rules}")
        learned_rules = []

    context = MemoryContext(
        similar_past_candidates=similar_candidates,
        learned_rules=learned_rules,
        role_category=role_category,
    )

    summary = context.to_prompt_summary()
    if summary:
        logger.info(f"[HybridMemory] Memory context built ({len(similar_candidates)} similar, {len(learned_rules)} rules).")
    else:
        logger.info("[HybridMemory] No memory context available for this candidate/role.")

    return context


async def get_past_feedback_summary(
    resume_text: str,
    role_category: str,
) -> Optional[str]:
    """
    Convenience function — returns a ready-to-inject prompt string
    from the hybrid memory system, or None if no context is found.

    Use this as the `past_feedback_summary` argument to agent functions.
    """
    ctx = await build_memory_context(resume_text, role_category)
    summary = ctx.to_prompt_summary()
    return summary if summary else None


async def record_outcome_to_memory(
    candidate_id: str,
    name: str,
    resume_text: str,
    skills: List[str],
    final_score: float,
    decision: str,
    role_category: str,
    rejection_reason: Optional[str] = None,
    rule_to_learn: Optional[str] = None,
) -> None:
    """
    After a hiring decision is made, write outcomes back to both memory stores.

    - Updates the ChromaDB document's metadata (decision, score, rejection reason).
    - Optionally reinforces or creates a learning rule in MongoDB.

    Args:
        candidate_id: Unique candidate identifier.
        name: Candidate's name.
        resume_text: Full resume text (for re-embedding if needed).
        skills: List of verified skills.
        final_score: Final score (0–100).
        decision: 'hired', 'rejected', 'shortlisted'.
        role_category: Role category for MongoDB rule storage.
        rejection_reason: Why rejected (if applicable).
        rule_to_learn: If provided, this pattern is upserted into system_memory.
    """
    # Branch A: Update ChromaDB metadata
    try:
        from langchain_core.documents import Document
        vector_store = get_vector_store(collection_name="candidates")

        # Delete existing doc for this candidate and re-add with updated metadata
        try:
            vector_store.delete(where={"candidate_id": candidate_id})
        except Exception:
            pass  # It's fine if it doesn't exist yet

        skills_str = ", ".join(skills[:10])
        page_content = f"Candidate: {name}\nSkills: {skills_str}\nResume: {resume_text[:800]}"

        metadata = {
            "candidate_id": candidate_id,
            "name": name,
            "status": decision,
            "final_score": final_score,
            "rejection_reason": rejection_reason or "",
            "skills": skills[:10],
        }
        doc = Document(page_content=page_content, metadata=metadata)
        vector_store.add_documents([doc])
        logger.info(f"[HybridMemory] Outcome saved to Vector DB for candidate '{candidate_id}'.")

    except Exception as e:
        logger.warning(f"[HybridMemory] Vector write-back failed: {e}")

    # Branch B: Upsert learning rule to MongoDB
    if rule_to_learn:
        try:
            await memory_service.upsert_rule(
                rule_pattern=rule_to_learn,
                role_category=role_category,
                source_candidate_id=candidate_id,
            )
            logger.info(f"[HybridMemory] Learning rule upserted for role '{role_category}'.")
        except Exception as e:
            logger.warning(f"[HybridMemory] MongoDB rule write-back failed: {e}")
