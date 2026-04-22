# Technology Stack Documentation

## Backend Technologies

### Core Framework
- FastAPI 0.104+: Modern async web framework for building REST APIs
  - Automatic API documentation (Swagger/OpenAPI)
  - Built-in data validation with Pydantic
  - Excellent performance with async/await support
  
- Python 3.11+: Programming language
  - Type hints support for better code quality
  - Async/await for non-blocking I/O
  - Rich ecosystem of libraries

### Async & Concurrency
- asyncio: Python's built-in async library
- Motor: Async MongoDB driver for non-blocking database operations
- aiohttp: Async HTTP client for external API calls
- Uvicorn: ASGI web server for running FastAPI

### Database & Data Storage

1. MongoDB (Primary Data Store)
   - Cloud hosting: MongoDB Atlas
   - Collections: jobs, candidates, requirements, activity_logs, feedback
   - Features: Flexible schema, horizontal scaling, built-in replication
   - Connection: Motor (async driver)
   - Pooling: Maximum 10-50 connections

2. Neo4j (Graph Database)
   - Purpose: Relationship mapping between jobs, candidates, skills, companies
   - Driver: neo4j-python-driver
   - Features: ACID transactions, graph algorithms
   - Use cases: Skill matching, relationship analysis

3. Chroma (Vector Database)
   - Purpose: Store and search job/candidate embeddings
   - Features: Semantic similarity search, fast retrieval
   - Collections: Job embeddings, candidate embeddings, skill embeddings
   - Integration: In-memory and persistent storage options

4. MongoDB GridFS
   - Purpose: Store binary files (resumes, documents)
   - Features: Automatic chunking, metadata storage
   - Files stored: PDF resumes, document uploads

### AI & Machine Learning

1. Google Generative AI (Gemini)
   - Library: google-generativeai
   - Use cases:
     - Job description suggestions
     - Requirement extraction
     - Resume analysis
     - Fairness assessment
   - Features: Model rotation with multiple API keys for resilience
   - Models: gemini-pro, text-embedding-004

2. LangChain
   - Purpose: AI model orchestration and chains
   - Features: Prompt templates, memory management, tool integration
   - Use cases: Complex AI workflows, multi-step processing

3. Sentence Transformers
   - Purpose: Generate embeddings for semantic similarity
   - Features: GPU support, pre-trained models
   - Models: all-MiniLM-L6-v2, all-mpnet-base-v2

### API & Network

- requests: HTTP client for synchronous API calls
- httpx: HTTP client for async API calls
- python-dotenv: Environment variable management
- pydantic: Data validation and parsing (models, settings)
- pydantic-settings: Configuration management from environment

### Logging & Monitoring

- logging: Python's built-in logging module
  - Formats: Timestamped, level-based, with context
  - Handlers: Console and file output
  - Loggers: Request/response, database, AI calls

### Security & Validation

- Pydantic: Input validation and type checking
- python-multipart: Form data parsing for file uploads
- CORS middleware: Cross-origin request handling
- TLS/SSL: Encrypted MongoDB connections

### Utility Libraries

- uuid: Generate unique identifiers
- datetime: Timestamp and date handling
- pathlib: Cross-platform file paths
- re: Regular expressions for parsing
- functools: Function decorators and caching

### Development Tools

- pytest: Testing framework
- black: Code formatter
- flake8: Style checker
- isort: Import sorter
- mypy: Static type checker

## Frontend Technologies

### Core Framework
- React 18+: JavaScript UI library
  - Functional components with hooks
  - Virtual DOM for efficient rendering
  - Component composition and reusability

- JavaScript ES6+: Programming language
  - ES modules for code organization
  - Async/await for asynchronous operations
  - Arrow functions and destructuring

### Build Tools
- Vite 4+: Modern build tool and dev server
  - Fast hot module replacement (HMR)
  - Optimized production bundling
  - Native ES module support
  
- npm: Package manager for JavaScript dependencies

### HTTP & Communication
- Fetch API: Native browser HTTP client
  - Promise-based for async operations
  - Built-in support in modern browsers
  
- WebSocket: Real-time bidirectional communication
  - Native browser API
  - Custom hook: useWebSocket for abstraction

### Styling & UI

1. Inline Styles with CSS Properties
   - Responsive design breakpoints (768px, 1024px, 1280px)
   - Dynamic calculations based on window width
   - CSS variables for consistent theming

2. CSS Animations
   - Keyframe animations: slideInUp, fadeIn, pulse, spin, etc.
   - Transitions: smooth property changes (0.2s - 0.6s)
   - Transform-based animations: translateY, scale, translateX

3. Responsive Design Pattern
   - Mobile-first approach
   - Breakpoints:
     - Mobile: 480px and below
     - Tablet: 768px and below
     - Desktop: 1024px and above
   - Dynamic font sizing and padding

4. Design Patterns
   - Glassmorphism: Semi-transparent panels with blur
   - Gradient backgrounds: Linear and radial gradients
   - Hover effects: Scale, shadow, color transitions

### State Management
- React Hooks:
  - useState: Component state
  - useRef: Direct DOM access
  - useEffect: Side effects and lifecycle
  - useCallback: Memoized callbacks
  - useContext: Global state (if needed)

### API Integration
- API Client Module (api/): 
  - jobAPI: Job operations
  - candidateAPI: Candidate operations
  - analyticsAPI: Dashboard data
  - Base URL: http://127.0.0.1:8000/api/v1

### Custom Hooks
- useWebSocket: WebSocket connection management
  - Connection state tracking
  - Event listener management
  - Auto-reconnection logic
  
- useUpload: File upload handling
  - Progress tracking
  - Error handling
  - File validation

### Components Structure

1. Page Components (pages/)
   - Upload.jsx: Main job management and candidate upload interface
   - Dashboard.jsx: Analytics and overview
   - Full responsive design with state management

2. UI Components (components/)
   - EventTimeline: Real-time event display
   - Forms: Input fields, text areas, dropdowns
   - Modals: Confirmation dialogs, alerts
   - Cards: Information display cards

3. Utility Components
   - Loading spinners
   - Error messages
   - Success notifications
   - Progress bars

### Data Flow
- Component props for unidirectional data flow
- State lifting for shared state
- Event callbacks for parent-child communication
- WebSocket for global real-time events

### Browser APIs Used
- Fetch API: HTTP requests
- WebSocket API: Real-time communication
- File API: Resume upload handling
- Drag and Drop API: File drop zones
- localStorage: Client-side storage (optional)

### Development & Testing
- npm scripts for build and dev
- Vite dev server with HMR
- Browser DevTools for debugging
- Console logging for troubleshooting

## DevOps & Infrastructure

### Version Control
- Git: Distributed version control
- GitHub: Repository hosting
- .gitignore: Exclude unnecessary files

### Environment Configuration
- .env files: Local environment variables
- Environment-specific configs: development, staging, production
- Configuration files:
  - vite.config.js: Frontend build configuration
  - requirements.txt: Python dependencies

### Containerization (Optional)
- Docker: Container runtime (if deployed via containers)
- docker-compose: Multi-container orchestration

### Database Hosting
- MongoDB Atlas: Cloud MongoDB service
  - Shared tier: Development
  - Dedicated tier: Production
  - Automated backups and monitoring

### External Services
- Google Cloud: Generative AI API
- N8N: Workflow automation
- Neo4j Aura: Cloud graph database (optional)

## Dependencies Summary

### Backend (Python)

Core:
- fastapi
- uvicorn
- pydantic
- pydantic-settings
- python-dotenv
- python-multipart

Database:
- motor
- pymongo
- neo4j
- chromadb

AI:
- google-generativeai
- langchain
- sentence-transformers

Network:
- requests
- httpx
- aiohttp

Utilities:
- python-dateutil
- pytz

Development:
- pytest
- black
- flake8
- mypy

### Frontend (JavaScript)

Core:
- react
- react-dom

Build:
- @vitejs/plugin-react
- vite

Icons:
- lucide-react

Utilities:
- axios (optional, for HTTP)

## Database Schema

### MongoDB Collections

1. jobs
   - _id (ObjectId): Primary key
   - job_id (String): Unique identifier
   - display_id (String): User-friendly ID
   - title (String): Job title
   - description (String): Full job description
   - requirements (Array): Job requirements
   - status (String): DRAFT, REVIEWING, FINALIZED, PUBLISHED
   - source (String): upload, manual, ai_generated
   - created_by (String): Creator identifier
   - created_at (DateTime): Creation timestamp
   - version (Number): Description version
   - suggestions (Array): AI-generated suggestions
   - embeddings_generated (Boolean): Flag for embeddings
   - is_active (Boolean): Active status

2. candidates
   - _id (ObjectId): Primary key
   - candidate_id (String): Unique identifier
   - email (String): Contact email
   - name (String): Full name
   - skills (Array): Extracted skills
   - experience (Array): Work experience
   - education (Array): Educational background
   - resume_text (String): Parsed resume content
   - elo_score (Number): Quality ranking
   - created_at (DateTime): Upload timestamp
   - assessments (Object): Behavioral assessments

3. job_requirements
   - _id (ObjectId): Primary key
   - job_id (String): Associated job
   - required_skills (Array): Technical requirements
   - nice_to_have (Array): Optional requirements
   - min_experience (Number): Years required
   - education_required (String): Education level

4. activity_logs
   - _id (ObjectId): Primary key
   - action (String): Action performed
   - entity_type (String): Type of entity (job, candidate)
   - entity_id (String): Entity identifier
   - user_id (String): User who performed action
   - timestamp (DateTime): When action occurred
   - metadata (Object): Additional information

5. feedback
   - _id (ObjectId): Primary key
   - job_id (String): Associated job
   - candidate_id (String): Associated candidate
   - rating (Number): 1-5 star rating
   - comment (String): Feedback text
   - timestamp (DateTime): Feedback timestamp

## Third-Party API Integrations

### Google Generative AI
- Endpoint: generativelanguage.googleapis.com
- Authentication: API_KEY in headers
- Models: gemini-pro, text-embedding-004
- Rate limits: Multiple keys for load distribution

### N8N Workflow
- Endpoint: N8N instance URL
- Authentication: Bearer token
- Trigger endpoints:
  - /webhook/job-published
  - /webhook/candidate-matched
  - /webhook/interview-scheduled

## Technology Comparison Rationale

### Why MongoDB?
- Flexible schema for evolving job structures
- Horizontal scalability
- Full-text search capabilities
- GridFS for binary file storage

### Why Neo4j?
- Superior relationship querying
- Graph algorithms for matching
- Cypher query language clarity
- Real-time relationship inference

### Why Chroma?
- Simple vector database
- No separate infrastructure required
- Langchain integration
- Efficient similarity search

### Why FastAPI?
- Automatic API documentation
- Built-in async support
- Type safety with Pydantic
- Excellent performance metrics

### Why React?
- Component reusability
- Large ecosystem and community
- Virtual DOM efficiency
- Good for real-time applications

### Why Vite?
- Faster development experience
- Optimized production builds
- Native ESM support
- Better HMR implementation

---

Last Updated: April 2026
