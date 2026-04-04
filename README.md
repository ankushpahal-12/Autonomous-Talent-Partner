# The Autonomous Talent Partner

## Description

The Autonomous Talent Partner is an advanced Artificial Intelligence recruitment system designed to automate the entire hiring funnel. Unlike traditional applicant tracking systems or simple chatbots, this platform utilizes a multi-agent AI architecture, Retrieval-Augmented Generation, and hybrid memory systems to evaluate resumes conceptually. It parses unformatted resumes, cross-references skills against company job descriptions, and autonomously makes screening decisions. Furthermore, the system includes a Human-in-the-Loop feedback mechanism where recruiter corrections are used to train and refine the AI logic. All communication and scheduling are handled entirely by n8n Cloud webhooks, providing a seamless experience for both recruiters and candidates without blocking main application resources.

## Project Structure and File Responsibilities

### Frontend Application

- frontend/src/components/
Contains reusable User Interface elements such as tables for candidate lists and modal windows for screening reports.

- frontend/src/pages/
Contains the main views, including the recruiter dashboard, individual candidate deep-dive profiles, and the human review panel.

- frontend/src/services/
Handles the API client logic, communicating to the backend application.

### Backend Application

- backend/app/main.py
The main entry point for the FastAPI server. It initializes server routes and middleware.

- backend/app/api/
Contains the route definitions. This handles incoming HTTP requests such as file uploads or retrieving candidate lists.

- backend/app/core/
Stores configuration logic, environment variable parsing, and database connection setups.

- backend/app/database/
Manages connections to the MongoDB cluster and holds query logic for structured data.

- backend/app/models/
Defines data validation schemas using Pydantic to ensure incoming data formatting is correct.

### Core Backend Services

- backend/app/services/resume_parser.py
Communicates with Large Language Models to extract text from resumes and structure the unstructured data.

- backend/app/services/vector_parser.py
Handles the creation of semantic embeddings and queries a Vector Database to match candidates against job descriptions.

- backend/app/services/feedback_loop.py
Manages the Human-in-the-Loop logic. If a human recruiter disagrees with the AI decision, this file processes that mismatch to adjust future weighting.

- backend/app/services/n8n_trigger.py
Responsible for sending webhook payloads to n8n Cloud, triggering external workflows like sending emails or scheduling calendar events.

### Multi-Agent Evaluators

- backend/app/agents/screener_agents.py
The first pass AI agent. Evaluates the resume for hard requirements like visa status and location.

- backend/app/agents/tech_agent.py
The technical AI agent. Dives deep into the candidate reported technology stack and project complexities.

- backend/app/agents/culture_agent.py
The soft-skills AI agent. Reviews the wording and communication style of the resume to determine cultural fit.

- backend/app/agents/lead_agent.py
Synthesizes the reports from the screener, tech, and culture agents to generate a single, explainable final recommendation report.

- backend/app/knowledge_graph/
Contains logic to query graph databases for skill relationships, allowing the model to know related concepts.

### Data and Configuration

- n8n_workflows/
A directory used purely for version control to back up the JSON exports of the n8n Cloud workflows.

- backend/data/
Stores local testing data, such as internal company policy documents or mock resumes.

- backend/requirements.txt
Lists the Python dependencies required to run the backend server.

- backend/.env
A securely ignored file where API keys for databases and language models are stored.

# The Autonomous Talent Partner

The Autonomous Talent Partner is an advanced Artificial Intelligence recruitment system designed to automate the entire hiring funnel. Unlike traditional applicant tracking systems or simple chatbots, this platform utilizes a multi-agent AI architecture, Retrieval-Augmented Generation, and hybrid memory systems to evaluate resumes conceptually. It parses unformatted resumes, cross-references skills against company job descriptions, and autonomously makes screening decisions. Furthermore, the system includes a Human-in-the-Loop feedback mechanism where recruiter corrections are used to train and refine the AI logic. All communication and scheduling are handled entirely by n8n Cloud webhooks, providing a seamless experience for both recruiters and candidates without blocking main application resources.

## Core Architecture Overview
The system utilizes advanced technology to automate the recruiting process seamlessly:
- **Frontend:** React (HR dashboard + review panel)
- **Backend:** FastAPI (Python) for AI processing and orchestration
- **Database:** MongoDB (structured JSON storage)
- **Vector DB:** Pinecone / ChromaDB (semantic embeddings)
- **Automation Engine:** n8n (for email communication and interview scheduling)

## Project Structure and File Responsibilities
### Frontend Application
- frontend/src/components/
Contains reusable User Interface elements such as tables for candidate lists and modal windows for screening reports.
- frontend/src/pages/
Contains the main views, including the recruiter dashboard, individual candidate deep-dive profiles, and the human review panel.
- frontend/src/services/
Handles the API client logic, communicating to the backend application.

### Backend Application
- backend/app/main.py
The main entry point for the FastAPI server. It initializes server routes and middleware.
- backend/app/api/
Contains the route definitions. This handles incoming HTTP requests such as file uploads or retrieving candidate lists.
- backend/app/core/
Stores configuration logic, environment variable parsing, and database connection setups.
- backend/app/database/
Manages connections to the MongoDB cluster and holds query logic for structured data.
- backend/app/models/
Defines data validation schemas using Pydantic to ensure incoming data formatting is correct.

### Core Backend Services
- backend/app/services/resume_parser.py
Communicates with Large Language Models to extract text from resumes and structure the unstructured data.
- backend/app/services/vector_parser.py
Handles the creation of semantic embeddings and queries a Vector Database to match candidates against job descriptions.
- backend/app/services/feedback_loop.py
Manages the Human-in-the-Loop logic. If a human recruiter disagrees with the AI decision, this file processes that mismatch to adjust future weighting.
- backend/app/services/n8n_trigger.py
Responsible for sending webhook payloads to n8n Cloud, triggering external workflows like sending emails or scheduling calendar events.

### Multi-Agent Evaluators
- backend/app/agents/screener_agents.py
The first pass AI agent. Evaluates the resume for hard requirements like visa status and location.
- backend/app/agents/tech_agent.py
The technical AI agent. Dives deep into the candidate reported technology stack and project complexities.
- backend/app/agents/culture_agent.py
The soft-skills AI agent. Reviews the wording and communication style of the resume to determine cultural fit.
- backend/app/agents/lead_agent.py
Synthesizes the reports from the screener, tech, and culture agents to generate a single, explainable final recommendation report.
- backend/app/knowledge_graph/
Contains logic to query graph databases for skill relationships, allowing the model to know related concepts.

### Data and Configuration
- n8n_workflows/
A directory used purely for version control to back up the JSON exports of the n8n Cloud workflows.
- backend/data/
Stores local testing data, such as internal company policy documents or mock resumes.
- backend/requirements.txt
Lists the Python dependencies required to run the backend server.
- backend/.env
A securely ignored file where API keys for databases and language models are stored.

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
