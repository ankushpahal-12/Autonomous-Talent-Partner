# System Architecture Documentation

## High-Level System Overview

The Autonomous Talent Partner system follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  React Application (Port 5173)                               │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │  │
│  │  │  Upload.jsx │  │ Dashboard   │  │  Components │          │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │  │
│  │         │                │               │                   │  │
│  │         └────────────────┴───────────────┘                   │  │
│  │                      │                                        │  │
│  │           ┌──────────┴──────────┐                            │  │
│  │           │    API Client       │                            │  │
│  │           │   (HTTP + WS)       │                            │  │
│  │           └──────────┬──────────┘                            │  │
│  └────────────────────────┼─────────────────────────────────────┘  │
└─────────────────────────────┼────────────────────────────────────────┘
                              │
              ┌───────────────┴──────────────┐
              │                              │
              ▼                              ▼
    ┌──────────────────┐          ┌──────────────────┐
    │  HTTP Requests   │          │  WebSocket       │
    │  (REST API)      │          │  (Real-time)     │
    └────────┬─────────┘          └────────┬─────────┘
             │                             │
┌────────────┴─────────────────────────────┴──────────────────────────┐
│                      BACKEND LAYER                                   │
│                   (FastAPI - Port 8000)                              │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    API ROUTES (v1)                            │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │ │
│  │  │  jobs.py │  │candidates│  │   req.   │  │analytics │     │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │ │
│  │       │             │             │             │           │ │
│  │       └─────────────┴─────────────┴─────────────┘           │ │
│  │                     │                                        │ │
│  ├─────────────────────┼────────────────────────────────────────┤ │
│  │                                                              │ │
│  │         SERVICE LAYER (Business Logic)                      │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │ │
│  │  │  job_    │  │  llm_    │  │  neo4j_  │  │  match_  │   │ │
│  │  │ service  │  │ service  │  │ service  │  │ service  │   │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │ │
│  │  │  fair_   │  │   elo_   │  │  n8n_    │                  │ │
│  │  │ hiring   │  │ ranking  │  │ trigger  │                  │ │
│  │  └──────────┘  └──────────┘  └──────────┘                  │ │
│  │                                                              │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │                     AGENT LAYER                             │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │ │
│  │  │  lead_   │  │  tech_   │  │behavioral│  │ fairness │   │ │
│  │  │ agent    │  │ agent    │  │ agent    │  │ agent    │   │ │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │ │
│  │                                                              │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │            MIDDLEWARE & UTILITIES                           │ │
│  │      Logging | Error Handling | WebSocket Handler           │ │
│  │                                                              │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────┬───────────────────┬───────────────┬────────────────┘
                  │                   │               │
                  ▼                   ▼               ▼
        ┌──────────────────┐  ┌──────────────┐  ┌─────────────┐
        │    MongoDB       │  │   Neo4j      │  │   Chroma    │
        │  (Primary Data)  │  │  (Graph DB)  │  │  (Vector)   │
        │  Jobs            │  │  Skills      │  │  Embeddings │
        │  Candidates      │  │  Relationships│  │  Search     │
        │  Requirements    │  │              │  │             │
        │  Activity Logs   │  │              │  │             │
        └──────────────────┘  └──────────────┘  └─────────────┘
                  │                   │               │
                  └───────────────────┴───────────────┘
                              │
                              ▼
                ┌──────────────────────────┐
                │  External Services       │
                │  • Google Gemini AI      │
                │  • N8N Workflows         │
                │  • File Storage (GridFS) │
                └──────────────────────────┘
```

## Component Architecture

### Frontend Layer (React)

Components:
- Upload.jsx: Main interface for job management, candidate uploads, past jobs view
- Dashboard: Analytics and statistics
- EventTimeline: Real-time event streaming display
- Various UI Components: Reusable form inputs, buttons, modals

State Management:
- React Hooks (useState, useRef, useEffect)
- Custom hooks (useWebSocket, useUpload)
- Local component state for forms and UI

Styling:
- Inline styles with responsive breakpoints (768px, 1024px)
- CSS animations and transitions
- Glassmorphism design pattern

WebSocket Connection:
- Real-time connection to backend
- Event streaming for AI processing progress
- Live updates for job operations

### Backend Layer (FastAPI)

API Structure:
- REST endpoints for CRUD operations
- WebSocket endpoint for real-time communication
- Middleware for logging and CORS

Main Components:

1. API Routes (app/api/v1/)
   - jobs.py: Job lifecycle management (create, edit, finalize, publish, delete)
   - candidates.py: Resume upload and candidate management
   - requirements.py: Job requirement analysis
   - analytics.py: Dashboard data and statistics
   - evaluate.py: Candidate screening and evaluation
   - websockets_api.py: Real-time event streaming

2. Services (app/services/)
   - job_service.py: Job business logic
   - llm_service.py: AI model interaction (Google Gemini)
   - neo4j_service.py: Graph database operations
   - match_service.py: Candidate-job matching
   - fair_hiring_service.py: Bias detection and fairness
   - elo_ranking_service.py: Candidate quality ranking
   - db_service.py: Database operations
   - n8n_trigger.py: Workflow automation

3. Agent Layer (app/agents/)
   - lead_agent.py: Main orchestrator
   - tech_agent.py: Technical skills evaluation
   - behavioral_agent.py: Behavioral assessment
   - culture_agent.py: Culture fit evaluation
   - fairness_agent.py: Fair hiring checks
   - code_quality_agent.py: Code review capabilities

4. Database Access (app/database/)
   - connection_manager.py: Connection pooling
   - mongodb.py: MongoDB wrapper
   - vectordb.py: Chroma vector database

5. Core Utilities (app/core/)
   - config.py: Configuration management
   - websockets.py: WebSocket handler

6. Middleware (app/middleware/)
   - logging_middleware.py: Request/response logging
   - error_handling.py: Exception middleware

### Data Layer

1. MongoDB (Primary Data Store)
   Collections:
   - jobs: Job postings with metadata
   - candidates: Candidate profiles and assessments
   - job_requirements: Extracted requirements
   - activity_logs: Audit trail
   - feedback: User feedback and ratings

2. Neo4j (Graph Database)
   Nodes:
   - Job: Job postings
   - Candidate: Candidate profiles
   - Skill: Technical and soft skills
   - Company: Company information
   - Position: Role descriptions

   Relationships:
   - REQUIRES (Job -> Skill)
   - HAS_SKILL (Candidate -> Skill)
   - MATCHES (Job -> Candidate)
   - WORKED_AT (Candidate -> Company)

3. Chroma (Vector Database)
   - Job embeddings for semantic search
   - Candidate embeddings
   - Skill embeddings
   - Used for similarity matching

4. File Storage
   - MongoDB GridFS: Resume files
   - Local filesystem: Log files

## Data Flow Diagrams

### Job Creation Flow

```
User Input (Upload/Manual Create)
    |
    v
Frontend: Upload.jsx (Step 1)
    |
    v
API: POST /api/v1/jobs
    |
    v
Backend: create_job() service
    |
    +-> Generate UUID and Display ID
    +-> Store in MongoDB
    +-> Parse content (if file)
    +-> Send WebSocket notification
    |
    v
Response: JobResponse with job_id
    |
    v
Frontend: Move to Step 2 (Suggestions)
```

### AI Suggestion Flow

```
Job Created (job_id known)
    |
    v
Frontend: Step 2 - Call Suggestions API
    |
    v
API: POST /api/v1/jobs/suggestions/{job_id}
    |
    v
Backend: get_ai_suggestions()
    |
    +-> Retrieve job from MongoDB
    +-> Create prompt for Google Gemini
    +-> Call LLM service
    +-> Generate suggestions
    +-> Store in job document
    +-> Send progress via WebSocket
    |
    v
Response: Suggestions list
    |
    v
Frontend: Display suggestions with apply option
    |
    v
User: Review and apply suggestions
    |
    v
API: POST /api/v1/jobs/apply-suggestions/{job_id}/{suggestion_id}
    |
    v
Backend: apply_suggestion()
    |
    +-> Merge suggestion into description
    +-> Update version history
    +-> Store in MongoDB
    |
    v
Frontend: Updated description displayed
```

### Job Finalization Flow

```
Job Ready (description finalized)
    |
    v
Frontend: Step 3 - Finalize Job
    |
    v
API: POST /api/v1/jobs/finalize/{job_id}
    |
    v
Backend: finalize_job()
    |
    +-> Set status to FINALIZED
    +-> Lock from editing
    +-> Send notification
    |
    v
Generate Embeddings:
    |
    +-> Extract key information
    +-> Create embeddings via LLM
    +-> Store in Chroma vector DB
    +-> Create Neo4j relationships
    |
    v
Response: Finalized job
    |
    v
Frontend: Ready for publishing
```

### Publishing and Matching Flow

```
Job Finalized
    |
    v
Frontend: Step 4 - Publish Job
    |
    v
API: POST /api/v1/jobs/publish/{job_id}
    |
    v
Backend: publish_job()
    |
    +-> Set status to PUBLISHED
    +-> Make available for matching
    +-> Trigger N8N workflow
    |
    v
Real-time Matching:
    |
    +-> For each candidate:
    +-> Calculate semantic similarity
    +-> Check skill requirements
    +-> Run fairness checks
    +-> Calculate ELO score
    +-> Store match in database
    |
    v
Candidate Receives Notification (via N8N)
    |
    v
Interview Scheduled (if match > threshold)
```

### Resume Upload & Candidate Matching

```
Candidate Uploads Resume
    |
    v
Frontend: Upload.jsx (Candidates section)
    |
    v
API: POST /api/v1/candidates/upload-resume
    |
    v
Backend: upload_resume()
    |
    +-> Parse PDF resume
    +-> Extract information
    +-> Create candidate profile
    +-> Extract skills
    +-> Store in MongoDB
    +-> Create Neo4j profile
    +-> Generate embeddings
    |
    v
Find Matching Jobs:
    |
    +-> Query matching jobs
    +-> Calculate similarity scores
    +-> Filter by requirements
    +-> Sort by relevance
    |
    v
Send Notifications (via N8N)
    |
    v
Trigger Workflow Automation
    |
    v
Interview Scheduling / Acceptance Flow
```

## Job Status Lifecycle

```
DRAFT
  |
  +-> (Ready for AI suggestions)
  |
  v
REVIEWING (After applying suggestions)
  |
  +-> (Job description finalized)
  |
  v
FINALIZED (Embeddings generated)
  |
  +-> (Ready to publish to candidates)
  |
  v
PUBLISHED (Active for matching)
  |
  +-> (Candidate matching in progress)
  |
  v
ARCHIVED (Job closed, keep for records)
```

## Error Handling Flow

```
Any API Request
    |
    v
Request Reaches FastAPI
    |
    v
Middleware: LoggingMiddleware
    |
    +-> Assign request_id
    +-> Log request details
    |
    v
Router: Find matching endpoint
    |
    v
Validation: Check input schema
    |
    +-> If invalid -> RequestValidationError
    +-> Response: 400 Bad Request
    |
    v
Business Logic: Execute service
    |
    +-> If database error -> HTTPException 500
    +-> If not found -> HTTPException 404
    +-> If validation fails -> HTTPException 400
    +-> If auth fails -> HTTPException 403
    |
    v
Response: JSON response with status code
    |
    v
Middleware: Log response
    |
    v
Client receives response
```

## Real-time WebSocket Communication

```
Client                          Server
   |                              |
   +---- Connect to /ws/{sid} --->|
   |                              |
   |<--- Connection Established --|
   |                              |
   |---- Trigger Job Create ----->|
   |                              |
   |<---- Progress Update 1 ------|
   |<---- Processing... ---------|
   |<---- Progress Update 2 ------|
   |<---- AI Suggestions... ------|
   |<---- Progress Update 3 ------|
   |<---- Complete! ------------|
   |                              |
   +---- Acknowledge ------------>|
   |                              |
   +---- Disconnect ------------>|
   |                              |
```

Event Types Sent via WebSocket:
- "progress": Processing stage updates
- "suggestion": New suggestion generated
- "complete": Operation completed
- "error": Error occurred
- "notification": General notifications

## Integration Points

### Google Gemini API Integration
- Used for job description suggestions
- AI-powered requirement extraction
- Resume content analysis
- Fairness and bias detection
- Multiple API keys for load balancing

### Neo4j Integration
- Stores skills hierarchy
- Job-to-candidate relationships
- Company and position mappings
- Supports complex matching queries

### N8N Workflow Integration
- interview_scheduler.json: Schedules interviews
- candidate_acceptance_workflow.json: Handles acceptances
- candidate_rejection_workflow.json: Handles rejections
- Triggered via n8n_trigger.py service

### Chroma Vector Database
- Stores embeddings for semantic search
- Enables similarity matching
- Supports filtering and ranking

## Security Architecture

### Authentication & Authorization
- API key-based authentication (headers)
- Session-based tracking via session_id
- Role-based access control (planned)

### Data Protection
- MongoDB user authentication
- TLS/SSL encryption for connections
- SQL injection prevention (parameterized queries)
- CORS middleware for origin validation

### Logging & Audit Trail
- Request/response logging via middleware
- Activity logs stored in MongoDB
- Request IDs for tracing
- Error logging with context

## Performance Considerations

### Caching
- Connection pooling (10-50 connections)
- Lazy loading for large datasets
- Browser caching for static assets

### Optimization Strategies
- Pagination for large result sets
- Async/await for non-blocking I/O
- Batch processing for bulk operations
- Vector index on Chroma for fast similarity search

### Monitoring
- Request duration tracking
- Error rate monitoring
- Connection pool health checks
- Database performance metrics

## Scalability Architecture

### Horizontal Scaling
- Stateless API servers (can add more instances)
- Load balancing via reverse proxy
- Session affinity for WebSocket connections
- Database connection pooling

### Vertical Scaling
- Increase pool size for more concurrent connections
- Upgrade MongoDB Atlas tier
- Increase server resources (RAM, CPU)

### Database Sharding Strategy
- MongoDB can shard by job_id
- Candidates collection by created_at
- Activity logs collection by date

## Disaster Recovery

### Backup Strategy
- MongoDB Atlas automated backups
- Point-in-time recovery available
- Regular database snapshots

### Failover Mechanism
- MongoDB Atlas replica sets
- Connection retry logic
- Graceful error handling

---

Last Updated: April 2026
