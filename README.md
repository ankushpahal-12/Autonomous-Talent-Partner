# Autonomous Talent Partner

An enterprise-grade, agent-native hiring funnel management system powered by LangChain, RAG, a Neo4j Knowledge Graph, and a multi-agent AI evaluation pipeline. It is fully integrated with a React dashboard and MongoDB Atlas to streamline Human Resources candidate tracking.

## Overview

The Autonomous Talent Partner is an advanced hiring funnel management tool built to drastically reduce manual candidate screening times while significantly improving match accuracy. It achieves this by shifting away from standard keyword-based filtering and instead adopting a modern AI Agentic Architecture.

When a candidate applies, the system automatically digests their resume into a chunked dataset utilizing ChromaDB and cross-references their deeply parsed profile against standard job requirements using strict Retrieval-Augmented Generation (RAG). Following this indexing, a multi-agent AI pipeline spins up dedicated evaluators (a Screener Agent, a Technical Depth Agent, and a Culture Fit Agent) that work entirely in parallel. The Technical Agent utilizes a Neo4j Knowledge Graph to deeply understand skill overlap, automatically inferring underlying technologies. Finally, a Lead Decision Agent converges all reports into an actionable numerical score out of 100, automatically rejecting poorly suited profiles to save HR time while delivering rich, interactive analytics to human reviewers for highly qualified applicants.

## Technologies Used

![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![MongoDB](https://img.shields.io/badge/MongoDB-%234ea94b.svg?style=for-the-badge&logo=mongodb&logoColor=white)
![Neo4j](https://img.shields.io/badge/Neo4j-018bff?style=for-the-badge&logo=neo4j&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![Vite](https://img.shields.io/badge/vite-%23646CFF.svg?style=for-the-badge&logo=vite&logoColor=white)

---

## System Architecture and Flow Diagram

```mermaid
graph TD
    subgraph Frontend [React Frontend]
        UI1[Resume Upload]
        UI2[Job Requirement Upload]
        UI3[Candidate Detail Dashboard]
    end

    subgraph Backend API [FastAPI Backend]
        API1[Upload Endpoints]
        API2[Resume Parsing Chain]
        API3[Evaluation Trigger]
    end

    subgraph Data Stores
        DB1[(MongoDB Atlas + GridFS)]
        DB2[(ChromaDB Vector Store)]
        DB3[(Neo4j Knowledge Graph)]
    end

    subgraph AI Pipeline [LangChain Multi-Agent System]
        RAG[RAG Chain: Context Retrieval]
        A1[Screener Agent: Hard Requirements]
        A2[Technical Agent: Stack Depth]
        A3[Culture Agent: Soft Skills]
        DC[Decision Chain: Final Score]
    end

    UI1 -->|Upload PDF| API1
    API1 -->|Store File| DB1
    API1 -->|Trigger Parsing| API2
    API2 -->|Extract JSON| DB1
    API2 -->|Embed Profile| DB2

    UI2 -->|Upload Requirement| API1
    API1 -->|Embed Job Needs| DB2

    UI3 -->|Trigger AI Review| API3
    API3 -->|Query Job Context| DB2
    DB2 -->|Return Context| RAG
    RAG -->|Provide Context| A1
    RAG -->|Provide Context| A2
    RAG -->|Provide Context| A3

    A2 -->|Expand Skills| DB3
    DB3 -->|Return Related Skills| A2

    A1 -->|Report| DC
    A2 -->|Report| DC
    A3 -->|Report| DC

    DC -->|Save Final Evaluation| DB1
    DB1 -->|Display Full Report| UI3
```

---

## Core Pipeline Step-By-Step Detail

1.  Resume Upload Phase:
    The HR representative uploads a candidate's resume (PDF) through the React frontend dashboard. The file is sent over the network to the FastAPI backend where it is securely stored in MongoDB GridFS, keeping the original document accessible.

2.  LangChain Parsing Phase:
    The backend runs a LangChain Expressive Language (LCEL) chain to parse the raw resume text into a structured JSON profile holding names, emails, skills, and past projects. This structured JSON acts as the core candidate identity going forward.

3.  Vector Database Ingestion:
    The parsed candidate profile is immediately chunked and embedded using Google Generative AI embeddings, and inserted into ChromaDB.

4.  Job Requirement Processing:
    HR uploads the job requirement text (e.g., Software Engineer job description). The system embeds this document into a separate ChromaDB collection, acting as the grounded truth for evaluation.

5.  RAG Context Retrieval:
    When HR triggers a candidate review, a Retrieval-Augmented Generation (RAG) chain pulls relevant chunks of the job requirements from ChromaDB and aligns them with the candidate's profile to understand specific capability demands.

6.  Multi-Agent Evaluation Execution:
    Three dedicated AI agents run entirely in parallel to analyze the candidate:
    -   Screener Agent assesses formatting, grammar, and critical chronological gaps.
    -   Technical Agent assesses the domain experience, system design background, and exact stack matching. It communicates with a Neo4j Knowledge Graph to expand known skills (e.g., detecting "React" and inherently knowing it implies "JavaScript").
    -   Culture Agent searches for collaborative indicators to determine soft-skill appropriateness.

7.  Final Decision Synthesis:
    A final Lead Decision chain gathers all sub-reports and the RAG context to formulate a definitive Match Score (out of 100). If the score is extremely low (under 60), the candidate is rejected automatically. If above 60, the application is presented to HR. Support systems generate tailored rejection feedback automatically if necessary.

---

## Project Structure and File Roles

```text
.
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── candidates.py       (Handles candidate upload and listing endpoints)
│   │   │   ├── requirements.py     (Handles job requirement upload endpoints)
│   │   │   └── system.py           (Serves standard system activity logs)
│   │   ├── core/config.py          (Loads system environment variables and keys)
│   │   ├── database/
│   │   │   ├── mongodb.py          (Initializes MongoDB and GridFS connectivity)
│   │   │   └── vectordb.py         (Initializes the local ChromaDB stores)
│   │   └── main.py                 (Main FastAPI entry point governing CORS and routers)
│   ├── agents/
│   │   ├── lead_agent.py           (The primary orchestrator launching RAG, sub-agents, and Neo4j queries)
│   │   ├── screener_agents.py      (Evaluates raw resumes formatting and grammar)
│   │   ├── tech_agent.py           (Analyzes stack alignment and engineering depths)
│   │   └── culture_agent.py        (Measures overall cultural and team fit indicators)
│   ├── services/
│   │   ├── resume_parser.py        (Orchestrates LCEL chain parsing text into JSON)
│   │   ├── vector_parser.py        (Manages document embeddings and contextual RAG logic)
│   │   ├── neo4j_service.py        (Interfaces with Knowledge Graph for skill expansion)
│   │   ├── decision_service.py     (Calculates the final AI decision and generates feedback)
│   │   ├── match_service.py        (Retrieves hybrid scoring using ChromaDB matches)
│   │   ├── db_service.py           (Handles CRUD operations on candidate data)
│   │   ├── storage_service.py      (Controls PDF storage in GridFS storage)
│   │   └── n8n_trigger.py          (Fires automation workflows for selected/rejected users)
│   ├── requirements.txt            (Lists Python dependencies)
│   └── .env                        (Local backend environment configuration)
├── frontend/
│   └── src/
│       ├── api.js                  (Houses backend endpoint routes mapping)
│       ├── pages/
│       │   ├── Dashboard.jsx       (Visual interface summarizing candidate analytics)
│       │   ├── Upload.jsx          (Interface to accept drag-and-drop resume PDFs)
│       │   ├── Applicants.jsx      (Renders all applicants in a clean list format)
│       │   ├── CandidateDetail.jsx (Shows interactive tabs for multi-agent evaluation reports)
│       │   └── Requirements.jsx    (Area to submit raw text for job requirements)
│       └── components/             (Shared shell elements like navigation sidebars)
└── README.md
```

---

## Getting Started: Installation and Configuration

### Prerequisites
- Python 3.11 or higher
- Node.js 18 or higher
- MongoDB Atlas cluster URL (free tier is supported)
- Google AI Studio API Key

### 1. Environment Configuration

Create a file named `.env` in the `backend/` directory with the following variables:

```env
# AI Services
GOOGLE_API_KEY="your_google_ai_key_here"

# MongoDB Connectivity
MONGO_URI="mongodb+srv://user:password@cluster.mongodb.net/?appName=Cluster0"
MONGO_DB_NAME="talent_partner_db"

# Neo4j Knowledge Graph integration
NEO4J_URI="neo4j+s://xxxx.databases.neo4j.io"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="your_neo4j_password"

# n8n Automation Webhooks
N8N_WEBHOOK_URL_SELECTED="https://your-n8n-instance/webhook/selected"
N8N_WEBHOOK_URL_REJECTED="https://your-n8n-instance/webhook/rejected"
```

### 2. MongoDB Atlas Detailed Configuration

To ensure the backend connects successfully to the database, follow these specific network configuration steps:

1. Log into your MongoDB Atlas Dashboard.
2. Navigate to "Network Access" under the "Security" sidebar menu.
3. Click "Add IP Address".
4. To allow immediate development, select "Allow Access From Anywhere" (which writes 0.0.0.0/0). For stricter security, select "Add Current IP Address".
5. Click "Confirm" and wait for the status to change from "Pending" to "Active".
6. Navigate to "Database Access" and ensure you have created a database user with "Read and write to any database" privileges.
7. Under the "Database" cluster section, click "Connect", select "Drivers", and copy the connection string. 
8. Replace the username and password explicitly in your `.env` file under `MONGO_URI`. Avoid using special characters like `@` directly in the password without URL-encoding them (for example, replace `@` with `%40`).

### 3. Backend Virtual Environment Setup

Configuring an isolated Python virtual environment ensures that the project's dependencies do not conflict with other system libraries.

```bash
# Navigate to the backend folder
cd backend

# Create a virtual environment named 'venv'
python -m venv venv

# Activate the virtual environment
# For Windows:
venv\Scripts\activate
# For macOS or Linux:
source venv/bin/activate

# Install required dependencies inside the virtual environment
pip install -r requirements.txt

# Start the FastAPI backend server
uvicorn app.main:app --reload --port 8000
```

The backend API documentation will immediately become available at `http://127.0.0.1:8000/docs`.

### 3. Frontend Setup

The frontend operates using React and Vite. Open a separate terminal window and run:

```bash
# Navigate to the frontend folder
cd frontend

# Install necessary node packages
npm install

# Start the Vite development server
npm run dev
```

The frontend application will be available at `http://localhost:5173`. If you need to adjust the backend URL targeting, modify the `frontend/src/api.js` file.

---

## Troubleshooting Guide

Problem: MongoDB SSL handshake failed
Fix: Whitelist your current IP address in MongoDB Atlas under the Network Access tab.

Problem: CORS policy blocked
Fix: Ensure the backend is strictly running on `http://127.0.0.1:8000` rather than `localhost:8000`.

Problem: AI review returns empty score
Fix: Ensure at least one standard job requirement is uploaded before running the candidate review.

Problem: RAG reasoning is null
Fix: Upload a job requirement first so ChromaDB holds indexed documents to retrieve context from.

Problem: Neo4j connection error
Fix: Ensure correct credentials in `.env`, or leave the NEO4J fields entirely blank to allow the system to use the built-in local fallback graph structure.

---

Autonomous Talent Partner — Self-improving AI-driven recruitment.
