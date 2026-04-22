# Autonomous Talent Partner - AI-Powered Resume Screening Platform

## 📚 Quick Documentation Links

- **[System Architecture](docs/ARCHITECTURE.md)** - Detailed architecture design and component relationships
- **[Setup Guide](docs/SETUP_GUIDE.md)** - Installation and configuration instructions
- **[API Documentation](docs/API_DOCUMENTATION.md)** - Complete REST API reference
- **[Tech Stack](docs/TECH_STACK.md)** - Technologies and libraries used
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Contributing Guide](docs/CONTRIBUTING.md)** - Development guidelines
- **[N8N Integration](docs/N8N_QUICK_START.md)** - Workflow automation setup

## Project Overview

Autonomous Talent Partner is an intelligent resume screening and candidate matching platform that leverages artificial intelligence to automate and enhance the hiring process. The system analyzes job descriptions, evaluates candidate resumes, and provides AI-powered suggestions to improve job postings and match candidates with relevant positions.

## Key Features

1. Job Description Management
   - Upload job descriptions from PDF, DOCX, or TXT files
   - Create job descriptions manually or via AI generation
   - Apply AI-powered suggestions to improve job postings
   - Version control and status tracking for jobs

2. AI-Powered Capabilities
   - Intelligent job description suggestions using Google Gemini API
   - Vector embeddings for semantic search and matching
   - Real-time processing with WebSocket notifications
   - Fuzzy matching for candidate requirements

3. Candidate Management
   - Resume upload and parsing
   - Candidate profile creation with ELO ranking
   - Skills extraction and analysis
   - Behavioral assessment and feedback

4. Job Matching & Ranking
   - Semantic similarity matching between jobs and candidates
   - ELO-based ranking system for candidate quality
   - Fair hiring algorithms
   - Neo4j graph database for relationship mapping

5. Workflow Automation
   - N8N integration for interview scheduling
   - Candidate acceptance/rejection workflows
   - Activity logging and audit trails
   - Real-time notifications

## Project Statistics

- Backend: Python FastAPI with async/await
- Frontend: React with responsive design
- Database: MongoDB Atlas (Jobs, Candidates, Requirements)
- Graph Database: Neo4j (Skills, Relationships)
- Vector Database: Chroma (Job embeddings)
- Real-time: WebSocket support for live updates
- AI Engine: Google Gemini API with multiple API keys
- Workflow: N8N for process automation

## Quick Start

### For Developers

1. Setup Backend:
   ```
   cd backend
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python -m uvicorn app.main:app --reload
   ```

2. Setup Frontend:
   ```
   cd frontend
   npm install
   npm run dev
   ```

3. Access the Application:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### For Non-Technical Users

1. Open http://localhost:5173 in your browser
2. Use the Job Management Hub to:
   - Upload job descriptions
   - Create new job postings
   - View AI suggestions
   - Manage candidates
   - View past jobs and delete as needed

## Project Structure

```
root/
├── backend/                          # FastAPI backend application
│   ├── app/
│   │   ├── main.py                   # FastAPI application entry point
│   │   ├── core/
│   │   │   ├── config.py             # Configuration management
│   │   │   └── websockets.py         # WebSocket handler
│   │   ├── api/v1/
│   │   │   ├── jobs.py               # Job endpoints
│   │   │   ├── candidates.py         # Candidate endpoints
│   │   │   ├── requirements.py       # Requirement endpoints
│   │   │   ├── analytics.py          # Analytics endpoints
│   │   │   └── websockets_api.py     # WebSocket endpoint
│   │   ├── agents/                   # AI agent implementations
│   │   ├── services/                 # Business logic services
│   │   ├── database/                 # Data access layer
│   │   └── middleware/               # Request/response processing
│   ├── requirements.txt              # Python dependencies
│   └── test_mongodb_connection.py    # MongoDB connection test utility
│
├── frontend/                         # React frontend application
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Upload.jsx            # Main job upload and management page
│   │   │   └── Dashboard.jsx         # Analytics and overview
│   │   ├── components/               # Reusable UI components
│   │   ├── hooks/                    # Custom React hooks
│   │   ├── api/                      # API client functions
│   │   ├── index.css                 # Global styles
│   │   └── responsive-animations.css # Responsive and animation styles
│   ├── package.json                  # Node dependencies
│   ├── vite.config.js                # Vite build configuration
│   └── index.html                    # HTML entry point
│
├── n8nworkflow/                      # N8N automation workflows
│   ├── interview_scheduler.json      # Interview scheduling workflow
│   ├── candidate_acceptance_workflow.json
│   └── candidate_rejection_workflow.json
│
├── TECH_STACK.md                     # Technologies and libraries used
├── ARCHITECTURE.md                   # System architecture and design
├── SETUP_GUIDE.md                    # Installation and setup instructions
├── TROUBLESHOOTING.md                # Common errors and solutions
├── API_DOCUMENTATION.md              # REST API reference
├── MONGODB_SSL_FIX.md                # MongoDB connection troubleshooting
├── CONTRIBUTING.md                   # Development guidelines
└── README.md                         # This file
```

## Documentation Files

For comprehensive documentation, please refer to the `docs/` folder:

- **[docs/README.md](docs/)** - Documentation index
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture, data flow, and component relationships
- **[docs/TECH_STACK.md](docs/TECH_STACK.md)** - Complete list of technologies, libraries, and tools used
- **[docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)** - Detailed setup instructions for development and production
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues, error solutions, and diagnostics
- **[docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)** - Complete REST API reference for backend endpoints
- **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Guidelines for developers contributing to the project
- **[docs/N8N_QUICK_START.md](docs/N8N_QUICK_START.md)** - N8N integration and workflow automation guide

## System Requirements

Minimum Requirements:
- Python 3.8+ (3.11+ recommended)
- Node.js 18+ with npm
- 4GB RAM
- 500MB disk space

External Services Required:
- MongoDB Atlas account (or local MongoDB)
- Google AI API key (for Gemini)
- Neo4j database (optional, for graph operations)
- N8N instance (optional, for workflow automation)

## Configuration

The application uses environment variables for configuration. Create a `.env` file in the backend directory:

```
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=talent_partner_db
GOOGLE_API_KEY=your_google_ai_key_here
OPENAI_API_KEY=your_openai_key_here
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Key Endpoints

### Job Management
- POST /api/v1/jobs - Create new job
- GET /api/v1/jobs - List all jobs
- GET /api/v1/jobs/{job_id} - Get specific job
- PUT /api/v1/jobs/edit/{job_id} - Edit job description
- POST /api/v1/jobs/suggestions/{job_id} - Get AI suggestions
- POST /api/v1/jobs/finalize/{job_id} - Finalize job
- POST /api/v1/jobs/publish/{job_id} - Publish job
- DELETE /api/v1/jobs/{job_id} - Delete job

### Candidate Management
- POST /api/v1/candidates/upload-resume - Upload resume
- GET /api/v1/candidates - List candidates
- GET /api/v1/candidates/match/{job_id} - Get matching candidates

### Real-time Updates
- WebSocket /ws/{session_id} - Real-time event streaming

## Support & Debugging

For troubleshooting common issues, refer to TROUBLESHOOTING.md which includes:
- MongoDB SSL connection errors and solutions
- Python dependency issues
- Frontend build errors
- API connection problems
- Performance optimization tips

## Contributing

To contribute to the project, please refer to CONTRIBUTING.md for:
- Code style guidelines
- Testing procedures
- Pull request process
- Development workflow

## Version History

Current Version: 1.0.0
- Initial release with job management, AI suggestions, and candidate matching
- Real-time WebSocket support
- Comprehensive documentation

## License

This project is proprietary and confidential. Unauthorized copying, modification, or distribution is prohibited.

## Contact

For questions, issues, or suggestions, please contact the development team through the project repository.

---

Last Updated: April 2026
