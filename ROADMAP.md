# 4-Week Project Implementation Roadmap

This document outlines the step-by-step development plan for the Autonomous Talent Partner, divided into four distinct phases.

## Week 1: Foundation and Data Parsing

**Goal**: Establish the core backend infrastructure and get the AI to successfully read and remember candidate data.

- Set up the FastAPI server architecture and environment variables.
- Connect the backend to the MongoDB cluster for data storage.
- Connect the backend to the Vector Database for semantic search.
- Implement the resume_parser.py to successfully extract raw text from PDF uploads using Large Language Models.
- Implement the vector_parser.py to convert parsed skills and job descriptions into semantic embeddings and store them.

## Week 2: The Multi-Agent Engine

**Goal**: Build the intelligent logic that actually evaluates the candidates against the job descriptions.

- Develop the screener_agents.py to evaluate hard requirements like visas and base location.
- Develop the tech_agent.py to analyze the depth and complexity of technical projects.
- Develop the culture_agent.py to evaluate soft skills and communication style.
- Develop the lead_agent.py to synthesize all three reports into one final, explainable decision.
- Build the core API endpoints that trigger this entire agentic pipeline when a resume is uploaded.

## Week 3: Human Interface and Frontend Integration

**Goal**: Build the React dashboard so Human Resources personnel can interact with the system.

- Initialize the React Vite project and set up the routing structure.
- Build the Candidate Upload interface to push resumes to the FastAPI backend.
- Build the Dashboard Table Component to view all processed candidates and their AI fit scores.
- Build the Deep Dive View to show the explainable AI decision reports.
- Connect all frontend React services to the FastAPI backend endpoints.

## Week 4: Automation, Feedback Loop, and Polish

**Goal**: Make the system self-improving and automate all external communication.

- Implement the feedback_loop.py backend service to capture times when HR disagrees with the AI.
- Configure the system logic to learn from this human feedback.
- Build the n8n_trigger.py logic to send HTTP requests to n8n Cloud webhooks.
- In n8n Cloud, build the workflows to send automated rejection emails.
- In n8n Cloud, build the workflows to send automated calendar availability links for selected candidates.
- Conduct final end-to-end testing of the entire pipeline from resume upload to final email delivery.
