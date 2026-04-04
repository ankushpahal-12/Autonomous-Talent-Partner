# The Autonomous Talent Partner

This project is a system of specialized AI agents that work together to manage the entire hiring funnel instead of just acting as a static chatbot.

## Core Architecture Overview

The system utilizes advanced technology to automate the recruiting process seamlessly:
- **Frontend:** React (HR dashboard + review panel)
- **Backend:** FastAPI (Python) for AI processing and orchestration
- **Database:** MongoDB (structured JSON storage)
- **Vector DB:** Pinecone / ChromaDB (semantic embeddings)
- **Automation Engine:** n8n (for email communication and interview scheduling)

## How it Works
The pipeline automates the journey from resume ingestion to automated communication.

1. **Resume Ingestion & Parsing:** The system extracts text from uploaded resumes and uses LLMs to parse context, skills, projects, and achievements, storing them as structured JSON in MongoDB.
2. **Embedding & RAG Matching:** The extracted capabilities are converted to vector embeddings and stored in a Vector DB. Candidates are evaluated against job requirements using RAG-based hybrid semantic scoring.
3. **Explainable AI Decision Making:** The system assesses candidate match scores and either selects or rejects them, providing detailed, explainable reasons (e.g., missing specific technical skills).
4. **Human-in-the-Loop Review & Feedback Loop :** HR teams review the AI's shortlists and decisions. If HR disagrees with the AI's choice, this feedback is captured to adjust thresholds and train future matching models, creating a self-improving system.
5. **n8n Automation:** Final outcomes trigger n8n workflows that autonomously send rejection emails or schedule interviews with selected candidates via Google/Outlook calendar integrations.

## Architectural & Technical Enhancements

To scale the system and improve accuracy, we are integrating the following advanced patterns:

*   **Knowledge Graph Integration**: Instead of exclusively relying on a Vector DB for semantic similarity, a Knowledge Graph (Neo4j or similar) maps the relationships between skills (e.g., "React" is related to "Next.js" and is a child of "JavaScript"). This allows the AI to recognize related skills intelligently, rather than demanding exact keyword matches.
*   **Event-Driven Architecture (Kafka/RabbitMQ)**: To prevent blocking FastAPI's synchronous endpoints during heavy LLM processing, a message broker is introduced. When a resume is uploaded, an event is placed in a queue. Background worker nodes process the parsing, embedding generation, and email triggers asynchronously, ensuring system scalability.
*   **Multi-Agent System for Review**: The single "Decision AI" is replaced with an agentic workflow for deeper evaluation:
    *   **Agent 1 (Screener)**: Checks hard requirements (Visas, Location).
    *   **Agent 2 (Technical Reviewer)**: Deep dives into project complexity and tech stack.
    *   **Agent 3 (Culture Fit)**: Highlights soft skills based on resume wording.
    *   **Lead Agent**: Synthesizes the reports into the final recommendation.

## Benefits and Features

- **Continuous Talent Nurturing:** Automatically re-engages rejected "silver medalist" candidates for new roles if their skills strongly match new requisitions.
- **Bias Mitigation Engine:** Analyzes screening criteria and interview questions to suggest inclusive language, ensuring objective skill evaluation.
- **Self-Improving System:** Learns continuously from recruiter feedback to perfect candidate shortlisting over time.

---

*This repository contains the architecture guidelines, backend models, and frontend setup for the Autonomous Talent Partner platform.*
