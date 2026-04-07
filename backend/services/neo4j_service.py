from typing import List, Optional, Dict, Any

class Neo4jKnowledgeGraph:
    """
    Full knowledge graph service for the Autonomous Talent Partner.

    Node model:
        (Candidate)-[:HAS_SKILL]->(Skill)
        (Job)-[:REQUIRES]->(Skill)
        (Skill)-[:RELATED_TO]-(Skill)
        (Skill)-[:HAS_CHILD]->(Skill)
        (Skill)-[:IN_DOMAIN]->(Domain)

    Falls back to a built-in in-memory graph if Neo4j is not configured.
    """

    def __init__(self):
        from app.core.config import settings
        self._connected = False
        self.graph = None

        uri      = settings.NEO4J_URI
        username = settings.NEO4J_USERNAME
        password = settings.NEO4J_PASSWORD

        if uri and password and "your-neo4j" not in uri:
            try:
                from langchain_neo4j import Neo4jGraph
                self.graph = Neo4jGraph(url=uri, username=username, password=password)
                self._connected = True
                print("Neo4j Knowledge Graph connected successfully.")
            except Exception as e:
                print(f"Neo4j connection failed — falling back to local graph. ({e})")
        else:
            print("Neo4j not configured — using built-in local skill graph.")

    def get_related_skills(self, skill: str, limit: int = 5) -> List[str]:
        """
        Expands a skill into related technologies.
        e.g. "React" → ["JavaScript", "Next.js", "Redux", "TypeScript"]
        """
        if self._connected and self.graph:
            query = """
            MATCH (s:Skill {name: $skill})-[:RELATED_TO|HAS_CHILD]-(related:Skill)
            RETURN related.name AS related_skill
            LIMIT $limit
            """
            try:
                results = self.graph.query(query, params={"skill": skill, "limit": limit})
                skills = [r["related_skill"] for r in results]
                if skills:
                    return skills
            except Exception as e:
                print(f"Neo4j query error for '{skill}': {e}")

        return self._fallback_skill_graph(skill)

    def calculate_match_score(self, required: List[str], provided: List[str]) -> float:
        """
        Hybrid score: full credit for exact skill match, 0.5 for a related skill.
        """
        if not required:
            return 100.0

        score = 0.0
        provided_lower = {p.lower() for p in provided}

        for req in required:
            if req.lower() in provided_lower:
                score += 1.0
            else:
                related = self.get_related_skills(req)
                if any(r.lower() in provided_lower for r in related):
                    score += 0.5

        return round((score / len(required)) * 100, 1)

    def sync_candidate_to_graph(
        self,
        candidate_id: str,
        name: str,
        skills: List[str],
        status: str = "pending_review"
    ) -> bool:
        """
        Upserts a Candidate node and creates (Candidate)-[:HAS_SKILL]->(Skill)
        edges for every skill parsed from their resume.

        Called automatically after resume parsing succeeds.
        Returns True on success.
        """
        if not self._connected or not self.graph:
            print(f"[KG] Neo4j offline — skipping candidate sync for '{candidate_id}'")
            return False

        try:
            # 1. Upsert Candidate node
            upsert_query = """
            MERGE (c:Candidate {candidate_id: $candidate_id})
            ON CREATE SET c.name      = $name,
                          c.status    = $status,
                          c.created_at = datetime()
            ON MATCH  SET c.name      = $name,
                          c.status    = $status
            """
            self.graph.query(upsert_query, params={
                "candidate_id": candidate_id,
                "name": name,
                "status": status
            })

            # 2. For each skill: MERGE the Skill node, then link it
            for skill in skills:
                skill_link_query = """
                MATCH (c:Candidate {candidate_id: $candidate_id})
                MERGE (s:Skill {name: $skill_name})
                MERGE (c)-[:HAS_SKILL {weight: 1.0}]->(s)
                """
                self.graph.query(skill_link_query, params={
                    "candidate_id": candidate_id,
                    "skill_name": skill
                })

            print(f"[KG] Synced candidate '{name}' ({candidate_id}) with {len(skills)} skills.")
            return True

        except Exception as e:
            print(f"[KG] Failed to sync candidate '{candidate_id}': {e}")
            return False

    def sync_job_to_graph(
        self,
        job_id: str,
        title: str,
        required_skills: List[str]
    ) -> bool:
        """
        Upserts a Job node and creates (Job)-[:REQUIRES]->(Skill)
        edges for every skill extracted from the job description.

        Called automatically after a job requirement is uploaded.
        Returns True on success.
        """
        if not self._connected or not self.graph:
            print(f"[KG] Neo4j offline — skipping job sync for '{job_id}'")
            return False

        try:
            # 1. Upsert Job node
            upsert_query = """
            MERGE (j:Job {job_id: $job_id})
            ON CREATE SET j.title       = $title,
                          j.uploaded_at = datetime()
            ON MATCH  SET j.title       = $title
            """
            self.graph.query(upsert_query, params={"job_id": job_id, "title": title})

            # 2. Link each required skill
            for skill in required_skills:
                skill_link_query = """
                MATCH (j:Job {job_id: $job_id})
                MERGE (s:Skill {name: $skill_name})
                MERGE (j)-[:REQUIRES {weight: 1.0}]->(s)
                """
                self.graph.query(skill_link_query, params={
                    "job_id": job_id,
                    "skill_name": skill
                })

            print(f"[KG] Synced job '{title}' ({job_id}) with {len(required_skills)} required skills.")
            return True

        except Exception as e:
            print(f"[KG] Failed to sync job '{job_id}': {e}")
            return False

    def find_graph_candidates_for_job(self, job_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Pure graph traversal: finds candidates whose HAS_SKILL edges
        overlap with a Job's REQUIRES edges.

        Scoring:
          +1.0  per exact skill match (direct HAS_SKILL ↔ REQUIRES)
          +0.5  per related skill match (via RELATED_TO|HAS_CHILD hop)

        Returns a ranked list of dicts: {candidate_id, name, score, matched_skills}
        """
        if not self._connected or not self.graph:
            return []

        try:
            # Query A: Exact matches
            exact_query = """
            MATCH (j:Job {job_id: $job_id})-[:REQUIRES]->(s:Skill)
            MATCH (c:Candidate)-[:HAS_SKILL]->(s)
            RETURN c.candidate_id AS candidate_id,
                   c.name         AS name,
                   collect(DISTINCT s.name) AS matched_skills,
                   count(DISTINCT s)        AS match_count
            ORDER BY match_count DESC
            LIMIT $limit
            """
            exact_results = self.graph.query(
                exact_query, params={"job_id": job_id, "limit": limit}
            )

            # Query B: Related-skill matches (1-hop expansion)
            related_query = """
            MATCH (j:Job {job_id: $job_id})-[:REQUIRES]->(req:Skill)
            MATCH (req)-[:RELATED_TO|HAS_CHILD*1..1]-(rel:Skill)
            MATCH (c:Candidate)-[:HAS_SKILL]->(rel)
            WHERE NOT (c)-[:HAS_SKILL]->(req)
            RETURN c.candidate_id AS candidate_id,
                   c.name         AS name,
                   collect(DISTINCT rel.name) AS related_skills,
                   count(DISTINCT rel)        AS related_count
            ORDER BY related_count DESC
            LIMIT $limit
            """
            related_results = self.graph.query(
                related_query, params={"job_id": job_id, "limit": limit}
            )

            # Merge results and compute hybrid score
            scores: Dict[str, Dict] = {}

            for row in exact_results:
                cid = row["candidate_id"]
                scores[cid] = {
                    "candidate_id":   cid,
                    "name":           row["name"],
                    "exact_skills":   row["matched_skills"],
                    "related_skills": [],
                    "graph_score":    float(row["match_count"]) * 1.0,
                }

            for row in related_results:
                cid = row["candidate_id"]
                if cid in scores:
                    scores[cid]["related_skills"] = row["related_skills"]
                    scores[cid]["graph_score"]   += float(row["related_count"]) * 0.5
                else:
                    scores[cid] = {
                        "candidate_id":   cid,
                        "name":           row["name"],
                        "exact_skills":   [],
                        "related_skills": row["related_skills"],
                        "graph_score":    float(row["related_count"]) * 0.5,
                    }

            return sorted(scores.values(), key=lambda x: x["graph_score"], reverse=True)

        except Exception as e:
            print(f"[KG] Graph matching failed for job '{job_id}': {e}")
            return []

    def get_skill_gaps(self, candidate_id: str, job_id: str) -> List[str]:
        """
        Returns the list of skills a Job REQUIRES that the Candidate does NOT have.
        Uses 1-hop graph expansion — a related skill counts as a partial cover.

        Returns: list of missing skill names (empty = perfect match)
        """
        if not self._connected or not self.graph:
            return []

        try:
            query = """
            MATCH (j:Job {job_id: $job_id})-[:REQUIRES]->(req:Skill)
            WHERE NOT EXISTS {
                MATCH (c:Candidate {candidate_id: $candidate_id})-[:HAS_SKILL]->(req)
            }
            AND NOT EXISTS {
                MATCH (c:Candidate {candidate_id: $candidate_id})-[:HAS_SKILL]->(owned:Skill)
                MATCH (owned)-[:RELATED_TO|HAS_CHILD*1..1]-(req)
            }
            RETURN req.name AS missing_skill
            ORDER BY req.name
            """
            results = self.graph.query(query, params={
                "candidate_id": candidate_id,
                "job_id": job_id
            })
            return [r["missing_skill"] for r in results]

        except Exception as e:
            print(f"[KG] Skill gap query failed: {e}")
            return []

    def get_top_jobs_for_candidate(self, candidate_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Reverse direction: which jobs best match a given candidate?
        Useful for the candidate re-engagement loop.
        """
        if not self._connected or not self.graph:
            return []

        try:
            query = """
            MATCH (c:Candidate {candidate_id: $candidate_id})-[:HAS_SKILL]->(s:Skill)
            MATCH (j:Job)-[:REQUIRES]->(s)
            RETURN j.job_id      AS job_id,
                   j.title       AS title,
                   collect(DISTINCT s.name) AS matched_skills,
                   count(DISTINCT s)        AS match_count
            ORDER BY match_count DESC
            LIMIT $limit
            """
            results = self.graph.query(query, params={
                "candidate_id": candidate_id, "limit": limit
            })
            return [dict(r) for r in results]

        except Exception as e:
            print(f"[KG] Top-jobs query failed for candidate '{candidate_id}': {e}")
            return []

    def _fallback_skill_graph(self, skill: str) -> List[str]:
        """In-memory graph — mirrors Neo4j HAS_CHILD + RELATED_TO edges."""
        graph: Dict[str, List[str]] = {
            "Python":          ["Django", "FastAPI", "Flask", "Pandas", "Scikit-learn", "NumPy", "LangChain", "PyTorch", "TensorFlow"],
            "JavaScript":      ["React", "Node.js", "Express", "Next.js", "TypeScript", "Vue", "Angular"],
            "TypeScript":      ["React", "Node.js", "Next.js", "Angular", "NestJS"],
            "React":           ["JavaScript", "Next.js", "Redux", "TypeScript", "React Native"],
            "Next.js":         ["React", "JavaScript", "TypeScript"],
            "Node.js":         ["JavaScript", "Express", "TypeScript", "REST API", "GraphQL"],
            "FastAPI":         ["Python", "Pydantic", "Starlette", "Uvicorn", "REST API"],
            "Django":          ["Python", "REST API"],
            "Java":            ["Spring Boot", "Hibernate", "Maven", "Gradle", "Android SDK"],
            "Kotlin":          ["Android SDK", "Spring Boot"],
            "Machine Learning":["Python", "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Deep Learning"],
            "Deep Learning":   ["TensorFlow", "PyTorch", "Keras", "NLP", "Computer Vision"],
            "LLM":             ["LangChain", "LangGraph", "RAG", "Prompt Engineering", "HuggingFace"],
            "LangChain":       ["Python", "LangGraph", "RAG", "Vector DB", "HuggingFace"],
            "RAG":             ["ChromaDB", "Pinecone", "FAISS", "Vector DB", "LangChain"],
            "Cloud":           ["AWS", "Azure", "GCP", "Kubernetes", "Docker", "Terraform"],
            "Docker":          ["Kubernetes", "DevOps", "CI/CD"],
            "AWS":             ["Docker", "Kubernetes", "Terraform", "CI/CD"],
            "SQL":             ["PostgreSQL", "MySQL", "SQLite", "Database Design"],
            "MongoDB":         ["NoSQL", "Database Design"],
            "Docker":          ["Kubernetes", "DevOps", "CI/CD"],
            "TensorFlow":      ["Python", "Keras", "PyTorch"],
            "PyTorch":         ["Python", "Keras", "TensorFlow"],
            "Kafka":           ["RabbitMQ", "Microservices", "DevOps"],
            "React Native":    ["React", "JavaScript", "Flutter"],
            "Flutter":         ["Dart", "React Native"],
            "ChromaDB":        ["Pinecone", "FAISS", "Vector DB"],
            "Pinecone":        ["ChromaDB", "FAISS", "Vector DB"],
        }
        related = list(graph.get(skill, []))
        # Reverse lookup: find parents/siblings
        for parent, children in graph.items():
            if skill in children and parent not in related:
                related.append(parent)
        return related


# Singleton — imported everywhere in the backend
kg_service = Neo4jKnowledgeGraph()
