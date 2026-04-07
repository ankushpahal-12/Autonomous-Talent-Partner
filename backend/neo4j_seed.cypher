// ============================================================
// Autonomous Talent Partner — Neo4j Knowledge Graph
// Complete Skill Graph Seed Script
//
// HOW TO RUN:
//   1. Open Neo4j Aura Console → Query tab
//   2. Paste this entire file and click Run
//   3. Run verification queries at the bottom to confirm
// ============================================================


CREATE INDEX skill_name_index IF NOT EXISTS FOR (s:Skill) ON (s.name);
CREATE INDEX domain_name_index IF NOT EXISTS FOR (d:Domain) ON (d.name);

MERGE (d1:Domain  {name: "Web Development"})
MERGE (d2:Domain  {name: "Data Science & AI"})
MERGE (d3:Domain  {name: "Backend Engineering"})
MERGE (d4:Domain  {name: "DevOps & Cloud"})
MERGE (d5:Domain  {name: "Mobile Development"})
MERGE (d6:Domain  {name: "Database Engineering"});



// --- Programming Languages ---
MERGE (:Skill {name: "Python",        level: "language"})
MERGE (:Skill {name: "JavaScript",    level: "language"})
MERGE (:Skill {name: "TypeScript",    level: "language"})
MERGE (:Skill {name: "Java",          level: "language"})
MERGE (:Skill {name: "Kotlin",        level: "language"})
MERGE (:Skill {name: "Go",            level: "language"})
MERGE (:Skill {name: "Rust",          level: "language"})
MERGE (:Skill {name: "C++",           level: "language"})
MERGE (:Skill {name: "R",             level: "language"})
MERGE (:Skill {name: "Swift",         level: "language"})

// --- Python Ecosystem ---
MERGE (:Skill {name: "FastAPI",       level: "framework"})
MERGE (:Skill {name: "Django",        level: "framework"})
MERGE (:Skill {name: "Flask",         level: "framework"})
MERGE (:Skill {name: "Pydantic",      level: "library"})
MERGE (:Skill {name: "Starlette",     level: "library"})
MERGE (:Skill {name: "Uvicorn",       level: "library"})
MERGE (:Skill {name: "Pandas",        level: "library"})
MERGE (:Skill {name: "NumPy",         level: "library"})
MERGE (:Skill {name: "Scikit-learn",  level: "library"})
MERGE (:Skill {name: "TensorFlow",    level: "library"})
MERGE (:Skill {name: "PyTorch",       level: "library"})
MERGE (:Skill {name: "Keras",         level: "library"})
MERGE (:Skill {name: "LangChain",     level: "library"})
MERGE (:Skill {name: "LangGraph",     level: "library"})
MERGE (:Skill {name: "HuggingFace",   level: "library"})

// --- JavaScript / Frontend ---
MERGE (:Skill {name: "React",         level: "framework"})
MERGE (:Skill {name: "Next.js",       level: "framework"})
MERGE (:Skill {name: "Vue",           level: "framework"})
MERGE (:Skill {name: "Angular",       level: "framework"})
MERGE (:Skill {name: "Svelte",        level: "framework"})
MERGE (:Skill {name: "Redux",         level: "library"})
MERGE (:Skill {name: "Tailwind CSS",  level: "library"})
MERGE (:Skill {name: "HTML",          level: "skill"})
MERGE (:Skill {name: "CSS",           level: "skill"})

// --- Node.js / Backend JS ---
MERGE (:Skill {name: "Node.js",       level: "runtime"})
MERGE (:Skill {name: "Express",       level: "framework"})
MERGE (:Skill {name: "NestJS",        level: "framework"})
MERGE (:Skill {name: "REST API",      level: "concept"})
MERGE (:Skill {name: "GraphQL",       level: "concept"})

// --- Java Ecosystem ---
MERGE (:Skill {name: "Spring Boot",   level: "framework"})
MERGE (:Skill {name: "Hibernate",     level: "library"})
MERGE (:Skill {name: "Maven",         level: "tool"})
MERGE (:Skill {name: "Gradle",        level: "tool"})
MERGE (:Skill {name: "Android SDK",   level: "framework"})

// --- AI / ML Concepts ---
MERGE (:Skill {name: "Machine Learning",   level: "domain"})
MERGE (:Skill {name: "Deep Learning",      level: "domain"})
MERGE (:Skill {name: "NLP",                level: "domain"})
MERGE (:Skill {name: "Computer Vision",    level: "domain"})
MERGE (:Skill {name: "RAG",                level: "concept"})
MERGE (:Skill {name: "LLM",                level: "concept"})
MERGE (:Skill {name: "Vector DB",          level: "concept"})
MERGE (:Skill {name: "ChromaDB",           level: "tool"})
MERGE (:Skill {name: "Pinecone",           level: "tool"})
MERGE (:Skill {name: "FAISS",              level: "tool"})
MERGE (:Skill {name: "Prompt Engineering", level: "skill"})

// --- Databases ---
MERGE (:Skill {name: "SQL",           level: "skill"})
MERGE (:Skill {name: "PostgreSQL",    level: "tool"})
MERGE (:Skill {name: "MySQL",         level: "tool"})
MERGE (:Skill {name: "SQLite",        level: "tool"})
MERGE (:Skill {name: "MongoDB",       level: "tool"})
MERGE (:Skill {name: "Redis",         level: "tool"})
MERGE (:Skill {name: "Neo4j",         level: "tool"})
MERGE (:Skill {name: "Elasticsearch", level: "tool"})
MERGE (:Skill {name: "Database Design", level: "skill"})

// --- Cloud & DevOps ---
MERGE (:Skill {name: "AWS",           level: "platform"})
MERGE (:Skill {name: "Azure",         level: "platform"})
MERGE (:Skill {name: "GCP",           level: "platform"})
MERGE (:Skill {name: "Docker",        level: "tool"})
MERGE (:Skill {name: "Docker Compose",level: "tool"})
MERGE (:Skill {name: "Kubernetes",    level: "tool"})
MERGE (:Skill {name: "Helm",          level: "tool"})
MERGE (:Skill {name: "Prometheus",    level: "tool"})
MERGE (:Skill {name: "Grafana",       level: "tool"})
MERGE (:Skill {name: "ArgoCD",        level: "tool"})
MERGE (:Skill {name: "Terraform",     level: "tool"})
MERGE (:Skill {name: "Ansible",       level: "tool"})
MERGE (:Skill {name: "Chef",          level: "tool"})
MERGE (:Skill {name: "Puppet",        level: "tool"})
MERGE (:Skill {name: "CI/CD",         level: "concept"})
MERGE (:Skill {name: "DevOps",        level: "domain"})
MERGE (:Skill {name: "GitLab CI",     level: "tool"})
MERGE (:Skill {name: "Bitbucket Pipelines", level: "tool"})
MERGE (:Skill {name: "GitHub",        level: "tool"})
MERGE (:Skill {name: "GitHub Actions", level: "tool"})
MERGE (:Skill {name: "Jenkins",       level: "tool"})

// --- Mobile ---
MERGE (:Skill {name: "React Native",  level: "framework"})
MERGE (:Skill {name: "Flutter",       level: "framework"})

// --- General Engineering ---
MERGE (:Skill {name: "System Design", level: "skill"})
MERGE (:Skill {name: "Microservices", level: "concept"})
MERGE (:Skill {name: "Kafka",         level: "tool"})
MERGE (:Skill {name: "RabbitMQ",      level: "tool"})
MERGE (:Skill {name: "Git",           level: "tool"})
MERGE (:Skill {name: "Linux",         level: "skill"});


// ============================================================
// STEP 4: Link Skills to Domains (IN_DOMAIN relationships)
// ============================================================
MATCH (d:Domain {name: "Web Development"})
MATCH (s:Skill) WHERE s.name IN [
  "JavaScript","TypeScript","HTML","CSS","React","Next.js","Vue","Angular",
  "Svelte","Redux","Tailwind CSS","Node.js","Express","NestJS","GraphQL","REST API"
]
MERGE (s)-[:IN_DOMAIN]->(d);

MATCH (d:Domain {name: "Data Science & AI"})
MATCH (s:Skill) WHERE s.name IN [
  "Python","R","Machine Learning","Deep Learning","NLP","Computer Vision","RAG","LLM",
  "TensorFlow","PyTorch","Keras","Scikit-learn","Pandas","NumPy","HuggingFace",
  "LangChain","LangGraph","Vector DB","ChromaDB","Pinecone","FAISS","Prompt Engineering"
]
MERGE (s)-[:IN_DOMAIN]->(d);

MATCH (d:Domain {name: "Backend Engineering"})
MATCH (s:Skill) WHERE s.name IN [
  "Python","Java","Go","Rust","FastAPI","Django","Flask","Spring Boot","NestJS",
  "REST API","GraphQL","Microservices","Kafka","RabbitMQ","System Design"
]
MERGE (s)-[:IN_DOMAIN]->(d);

MATCH (d:Domain {name: "DevOps & Cloud"})
MATCH (s:Skill) WHERE s.name IN [
  "AWS","Azure","GCP","Docker","Docker Compose","Kubernetes","Helm","Prometheus","Grafana","ArgoCD",
  "Terraform","Ansible","Chef","Puppet","CI/CD","DevOps","GitLab CI","Bitbucket Pipelines",
  "GitHub","GitHub Actions","Jenkins","Linux","Git"
]
MERGE (s)-[:IN_DOMAIN]->(d);

MATCH (d:Domain {name: "Mobile Development"})
MATCH (s:Skill) WHERE s.name IN [
  "React Native","Flutter","Swift","Kotlin","Android SDK","JavaScript","TypeScript"
]
MERGE (s)-[:IN_DOMAIN]->(d);

MATCH (d:Domain {name: "Database Engineering"})
MATCH (s:Skill) WHERE s.name IN [
  "SQL","PostgreSQL","MySQL","SQLite","MongoDB","Redis","Neo4j","Elasticsearch","Database Design"
]
MERGE (s)-[:IN_DOMAIN]->(d);


// ============================================================
// STEP 5: Parent → Child relationships (HAS_CHILD)
// ============================================================

// Python → its libraries/frameworks
MATCH (parent:Skill {name: "Python"})
MATCH (child:Skill) WHERE child.name IN [
  "FastAPI","Django","Flask","Pandas","NumPy","Scikit-learn","TensorFlow",
  "PyTorch","Keras","LangChain","LangGraph","HuggingFace","Pydantic"
]
MERGE (parent)-[:HAS_CHILD]->(child);

// JavaScript → its ecosystem
MATCH (parent:Skill {name: "JavaScript"})
MATCH (child:Skill) WHERE child.name IN [
  "React","Next.js","Vue","Angular","Svelte","Node.js","TypeScript","Express",
  "NestJS","Redux","Tailwind CSS"
]
MERGE (parent)-[:HAS_CHILD]->(child);

// TypeScript → typed JS frameworks
MATCH (parent:Skill {name: "TypeScript"})
MATCH (child:Skill) WHERE child.name IN ["React","Node.js","Next.js","Angular","NestJS"]
MERGE (parent)-[:HAS_CHILD]->(child);

// React → ecosystem
MATCH (parent:Skill {name: "React"})
MATCH (child:Skill) WHERE child.name IN ["Next.js","Redux","React Native","Tailwind CSS"]
MERGE (parent)-[:HAS_CHILD]->(child);

// Node.js → ecosystem
MATCH (parent:Skill {name: "Node.js"})
MATCH (child:Skill) WHERE child.name IN ["Express","NestJS","REST API","GraphQL"]
MERGE (parent)-[:HAS_CHILD]->(child);

// FastAPI → components
MATCH (parent:Skill {name: "FastAPI"})
MATCH (child:Skill) WHERE child.name IN ["Pydantic","Starlette","Uvicorn","REST API"]
MERGE (parent)-[:HAS_CHILD]->(child);

// Java → ecosystem
MATCH (parent:Skill {name: "Java"})
MATCH (child:Skill) WHERE child.name IN ["Spring Boot","Hibernate","Maven","Gradle","Android SDK"]
MERGE (parent)-[:HAS_CHILD]->(child);

// Kotlin → ecosystem
MATCH (parent:Skill {name: "Kotlin"})
MATCH (child:Skill) WHERE child.name IN ["Android SDK","Spring Boot"]
MERGE (parent)-[:HAS_CHILD]->(child);

// Machine Learning → techniques
MATCH (parent:Skill {name: "Machine Learning"})
MATCH (child:Skill) WHERE child.name IN [
  "Deep Learning","NLP","Computer Vision","Scikit-learn","TensorFlow","PyTorch","Keras"
]
MERGE (parent)-[:HAS_CHILD]->(child);

// LLM → tooling
MATCH (parent:Skill {name: "LLM"})
MATCH (child:Skill) WHERE child.name IN [
  "LangChain","LangGraph","RAG","Prompt Engineering","HuggingFace","Vector DB"
]
MERGE (parent)-[:HAS_CHILD]->(child);

// RAG → vector stores
MATCH (parent:Skill {name: "RAG"})
MATCH (child:Skill) WHERE child.name IN ["ChromaDB","Pinecone","FAISS","Vector DB","LangChain"]
MERGE (parent)-[:HAS_CHILD]->(child);

// Docker → orchestration
MATCH (parent:Skill {name: "Docker"})
MATCH (child:Skill) WHERE child.name IN ["Kubernetes","DevOps","CI/CD","Docker Compose"]
MERGE (parent)-[:HAS_CHILD]->(child);

// Kubernetes → ecosystem
MATCH (parent:Skill {name: "Kubernetes"})
MATCH (child:Skill) WHERE child.name IN ["Helm","ArgoCD","Prometheus","Grafana"]
MERGE (parent)-[:HAS_CHILD]->(child);

// CI/CD → tools
MATCH (parent:Skill {name: "CI/CD"})
MATCH (child:Skill) WHERE child.name IN ["GitHub Actions","Jenkins","GitLab CI","Bitbucket Pipelines","ArgoCD"]
MERGE (parent)-[:HAS_CHILD]->(child);

// Git → platforms
MATCH (parent:Skill {name: "Git"})
MATCH (child:Skill) WHERE child.name IN ["GitHub","GitLab CI","Bitbucket Pipelines"]
MERGE (parent)-[:HAS_CHILD]->(child);

// Cloud → services
MATCH (parent:Skill {name: "AWS"})
MATCH (child:Skill) WHERE child.name IN ["Docker","Kubernetes","Terraform","CI/CD"]
MERGE (parent)-[:HAS_CHILD]->(child);

// SQL → relational DBs
MATCH (parent:Skill {name: "SQL"})
MATCH (child:Skill) WHERE child.name IN ["PostgreSQL","MySQL","SQLite","Database Design"]
MERGE (parent)-[:HAS_CHILD]->(child);


// ============================================================
// STEP 6: Peer relationships (RELATED_TO — bidirectional)
// ============================================================

// Python ↔ Data Science
MATCH (a:Skill {name:"Python"}), (b:Domain {name:"Data Science & AI"}) MERGE (a)-[:RELATED_TO]->(b);

// JavaScript ↔ TypeScript
MATCH (a:Skill {name:"JavaScript"}), (b:Skill {name:"TypeScript"}) MERGE (a)-[:RELATED_TO]-(b);

// React ↔ Vue ↔ Angular (frontend peers)
MATCH (a:Skill {name:"React"}), (b:Skill {name:"Vue"}) MERGE (a)-[:RELATED_TO]-(b);
MATCH (a:Skill {name:"React"}), (b:Skill {name:"Angular"}) MERGE (a)-[:RELATED_TO]-(b);
MATCH (a:Skill {name:"Vue"  }), (b:Skill {name:"Angular"}) MERGE (a)-[:RELATED_TO]-(b);

// FastAPI ↔ Django ↔ Flask (Python web peers)
MATCH (a:Skill {name:"FastAPI"}), (b:Skill {name:"Django"}) MERGE (a)-[:RELATED_TO]-(b);
MATCH (a:Skill {name:"FastAPI"}), (b:Skill {name:"Flask"})  MERGE (a)-[:RELATED_TO]-(b);
MATCH (a:Skill {name:"Django" }), (b:Skill {name:"Flask"})  MERGE (a)-[:RELATED_TO]-(b);

// TensorFlow ↔ PyTorch ↔ Keras
MATCH (a:Skill {name:"TensorFlow"}), (b:Skill {name:"PyTorch"}) MERGE (a)-[:RELATED_TO]-(b);
MATCH (a:Skill {name:"TensorFlow"}), (b:Skill {name:"Keras"})   MERGE (a)-[:RELATED_TO]-(b);
MATCH (a:Skill {name:"PyTorch"   }), (b:Skill {name:"Keras"})   MERGE (a)-[:RELATED_TO]-(b);

// Docker ↔ Kubernetes
MATCH (a:Skill {name:"Docker"}), (b:Skill {name:"Kubernetes"}) MERGE (a)-[:RELATED_TO]-(b);

// Terraform ↔ Ansible ↔ Chef ↔ Puppet (Infra as Code peers)
MATCH (a:Skill {name:"Terraform"}), (b:Skill {name:"Ansible"}) MERGE (a)-[:RELATED_TO]-(b);
MATCH (a:Skill {name:"Ansible"}), (b:Skill {name:"Chef"}) MERGE (a)-[:RELATED_TO]-(b);
MATCH (a:Skill {name:"Ansible"}), (b:Skill {name:"Puppet"}) MERGE (a)-[:RELATED_TO]-(b);
MATCH (a:Skill {name:"Chef"}), (b:Skill {name:"Puppet"}) MERGE (a)-[:RELATED_TO]-(b);

// Prometheus ↔ Grafana (monitoring peers)
MATCH (a:Skill {name:"Prometheus"}), (b:Skill {name:"Grafana"}) MERGE (a)-[:RELATED_TO]-(b);

// AWS ↔ Azure ↔ GCP
MATCH (a:Skill {name:"AWS"}  ), (b:Skill {name:"Azure"}) MERGE (a)-[:RELATED_TO]-(b);
MATCH (a:Skill {name:"AWS"}  ), (b:Skill {name:"GCP"  }) MERGE (a)-[:RELATED_TO]-(b);
MATCH (a:Skill {name:"Azure" }), (b:Skill {name:"GCP"  }) MERGE (a)-[:RELATED_TO]-(b);

// LangChain ↔ LangGraph
MATCH (a:Skill {name:"LangChain"}), (b:Skill {name:"LangGraph"}) MERGE (a)-[:RELATED_TO]-(b);

// MongoDB ↔ Redis
MATCH (a:Skill {name:"MongoDB"}), (b:Skill {name:"Redis"}) MERGE (a)-[:RELATED_TO]-(b);

// Kafka ↔ RabbitMQ (message brokers)
MATCH (a:Skill {name:"Kafka"}), (b:Skill {name:"RabbitMQ"}) MERGE (a)-[:RELATED_TO]-(b);

// React Native ↔ Flutter (mobile peers)
MATCH (a:Skill {name:"React Native"}), (b:Skill {name:"Flutter"}) MERGE (a)-[:RELATED_TO]-(b);

// ChromaDB ↔ Pinecone ↔ FAISS (vector DB peers)
MATCH (a:Skill {name:"ChromaDB"}), (b:Skill {name:"Pinecone"}) MERGE (a)-[:RELATED_TO]-(b);
MATCH (a:Skill {name:"ChromaDB"}), (b:Skill {name:"FAISS"})    MERGE (a)-[:RELATED_TO]-(b);
MATCH (a:Skill {name:"Pinecone"}), (b:Skill {name:"FAISS"})    MERGE (a)-[:RELATED_TO]-(b);



// ============================================================
// STEP 7: Candidate and Job Nodes — Extended Schema
//
//   (Candidate)-[:HAS_SKILL]->(Skill)
//   (Job)-[:REQUIRES]->(Skill)
//
// These are created/updated at RUNTIME by the Python backend.
// The Cypher below creates the necessary indexes so those
// runtime operations are fast.
// ============================================================

// --- Indexes for runtime Candidate / Job upserts ---
CREATE INDEX candidate_id_index IF NOT EXISTS FOR (c:Candidate) ON (c.candidate_id);
CREATE INDEX job_id_index       IF NOT EXISTS FOR (j:Job)       ON (j.job_id);

// --- Constraints for uniqueness (run only once per DB) ---
CREATE CONSTRAINT candidate_unique IF NOT EXISTS
  FOR (c:Candidate) REQUIRE c.candidate_id IS UNIQUE;

CREATE CONSTRAINT job_unique IF NOT EXISTS
  FOR (j:Job) REQUIRE j.job_id IS UNIQUE;


// ============================================================
// EXAMPLE: What the backend writes when a candidate is parsed
//
// (Run manually to test — backend writes these automatically)
// ============================================================

// Upsert a Candidate node
MERGE (c:Candidate {candidate_id: "example_candidate_001"})
  ON CREATE SET c.name = "Alice Dev", c.status = "pending_review", c.created_at = datetime()
  ON MATCH  SET c.name = "Alice Dev", c.status = "pending_review";

// Link Alice to her skills (HAS_SKILL with proficiency weight)
MATCH (c:Candidate {candidate_id: "example_candidate_001"})
MATCH (s:Skill) WHERE s.name IN ["Python", "FastAPI", "React", "Docker", "LangChain"]
MERGE (c)-[:HAS_SKILL {weight: 1.0}]->(s);


// ============================================================
// EXAMPLE: What the backend writes when a job is uploaded
// ============================================================

// Upsert a Job node
MERGE (j:Job {job_id: "example_job_001"})
  ON CREATE SET j.title = "Senior AI Engineer", j.uploaded_at = datetime()
  ON MATCH  SET j.title = "Senior AI Engineer";

// Link the job to its required skills (REQUIRES with importance weight)
MATCH (j:Job {job_id: "example_job_001"})
MATCH (s:Skill) WHERE s.name IN ["Python", "LangChain", "FastAPI", "Docker", "Machine Learning"]
MERGE (j)-[:REQUIRES {weight: 1.0}]->(s);


// ============================================================
// STEP 8: Graph-Traversal Matching Queries
// (These are what the backend calls at runtime for smart matching)
// ============================================================

// ── Query A: Direct match ─────────────────────────────────
// "Which candidates have the skills a specific job requires?"
//
// MATCH (j:Job {job_id: $job_id})-[:REQUIRES]->(s:Skill)
// MATCH (c:Candidate)-[:HAS_SKILL]->(s)
// RETURN c.candidate_id, c.name,
//        count(DISTINCT s) AS direct_skill_matches
// ORDER BY direct_skill_matches DESC;


// ── Query B: Related skills match (graph expansion) ────────
// "Which candidates have related/equivalent skills via the KG?"
//
// MATCH (j:Job {job_id: $job_id})-[:REQUIRES]->(req_skill:Skill)
// MATCH (req_skill)-[:RELATED_TO|HAS_CHILD*1..2]-(related:Skill)
// MATCH (c:Candidate)-[:HAS_SKILL]->(related)
// RETURN c.candidate_id, c.name,
//        count(DISTINCT related) AS related_skill_matches
// ORDER BY related_skill_matches DESC;


// ── Query C: Full hybrid score ──────────────────────────────
// "Score each candidate: 1.0 per exact skill, 0.5 per related skill"
//
// MATCH (j:Job {job_id: $job_id})-[:REQUIRES]->(req_skill:Skill)
// OPTIONAL MATCH (c:Candidate)-[:HAS_SKILL]->(req_skill)
// WITH j, req_skill, collect(DISTINCT c) AS exact_candidates
// OPTIONAL MATCH (req_skill)-[:RELATED_TO|HAS_CHILD*1..1]-(related:Skill)
// OPTIONAL MATCH (c2:Candidate)-[:HAS_SKILL]->(related)
// WITH exact_candidates, collect(DISTINCT c2) AS related_candidates
// UNWIND exact_candidates + related_candidates AS candidate
// MATCH (candidate)-[:HAS_SKILL]->(any_skill:Skill)
// RETURN candidate.candidate_id,
//        candidate.name,
//        count(DISTINCT any_skill) AS total_skills,
//        candidate.status
// ORDER BY total_skills DESC
// LIMIT 10;


// ── Query D: Skill gap analysis ────────────────────────────
// "What skills is a specific candidate MISSING for a job?"
//
// MATCH (j:Job {job_id: $job_id})-[:REQUIRES]->(req:Skill)
// WHERE NOT EXISTS {
//   MATCH (c:Candidate {candidate_id: $candidate_id})-[:HAS_SKILL]->(req)
// }
// RETURN req.name AS missing_skill, req.level AS level;


// ──  Query E: Top jobs for a candidate ────────────────────
// "Which jobs best match a given candidate?"
//
// MATCH (c:Candidate {candidate_id: $candidate_id})-[:HAS_SKILL]->(s:Skill)
// MATCH (j:Job)-[:REQUIRES]->(s)
// RETURN j.job_id, j.title,
//        count(DISTINCT s) AS matched_skills
// ORDER BY matched_skills DESC;


// ============================================================
// STEP 9: Verification Queries (run individually)
// ============================================================

// Node counts:
// MATCH (n) RETURN labels(n) AS label, count(n) AS count ORDER BY count DESC;

// Relationship counts:
// MATCH ()-[r]->() RETURN type(r) AS rel_type, count(r) AS count ORDER BY count DESC;

// Test Skill expansion:
// MATCH (s:Skill {name: "React"})-[:RELATED_TO|HAS_CHILD]-(related:Skill)
// RETURN related.name AS related_skill LIMIT 10;

// Test HAS_SKILL:
// MATCH (c:Candidate)-[:HAS_SKILL]->(s:Skill)
// RETURN c.name, collect(s.name) AS skills;

// Test REQUIRES:
// MATCH (j:Job)-[:REQUIRES]->(s:Skill)
// RETURN j.title, collect(s.name) AS required_skills;

// Test full graph match (Candidate ↔ Job via shared Skills):
// MATCH (c:Candidate)-[:HAS_SKILL]->(s:Skill)<-[:REQUIRES]-(j:Job)
// RETURN c.name, j.title, collect(s.name) AS shared_skills
// ORDER BY size(collect(s.name)) DESC;

