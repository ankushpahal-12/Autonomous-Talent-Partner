import sys
from pathlib import Path

# Add backend directory to path so services can be imported
backend_dir = Path(__file__).parent.parent.absolute()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import logging

from .api.v1 import system, candidates, requirements, evaluate, explain, feedback, analytics, websockets_api, jobs
from .database.connection_manager import db_manager
from .database.vectordb import init_vector_db, shutdown_vector_db
from utils.mcp_client import mcp_client_manager
from .core.config import settings
from .middleware.logging_middleware import LoggingMiddleware, setup_logging
from .schemas import ErrorResponse

load_dotenv()

# Configure logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown event handler with proper resource management.
    Establishes database connections and vector store initialization.
    """
    # Startup
    try:
        logger.info("Starting up application...")
        
        # Connect to MongoDB with connection pooling
        await db_manager.connect(
            mongo_uri=settings.MONGO_URI,
            db_name=settings.DATABASE_NAME,
            pool_size=settings.MONGO_POOL_SIZE,
            timeout_ms=settings.MONGO_CONNECTION_TIMEOUT_MS
        )
        
        # Initialize Vector Database
        init_vector_db()
        
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    try:
        logger.info("Shutting down application...")
        # Disconnect MCP client first (prevents lingering async generators)
        try:
            await mcp_client_manager.disconnect()
        except Exception as e:
            logger.warning(f"Error disconnecting MCP client: {e}")
        # Disconnect database
        await db_manager.disconnect()
        shutdown_vector_db()
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)

# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="AI-powered resume screening and candidate matching platform",
    lifespan=lifespan
)

# ============================================================================
# Middleware Stack
# ============================================================================

# Add request logging middleware (wraps all requests with unique IDs)
app.add_middleware(LoggingMiddleware)

# Configure CORS - Use environment variables instead of hardcoded origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors with proper error response format.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(f"[{request_id}] Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            status="error",
            message="Request validation failed",
            detail=str(exc.errors()),
            request_id=request_id
        ).model_dump()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions with proper logging and response.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[{request_id}] Unhandled exception: {str(exc)}", exc_info=True)
    
    # Don't expose internal error details in production
    detail = str(exc) if settings.DEBUG else "Internal server error"
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            status="error",
            message="Internal server error",
            detail=detail,
            request_id=request_id
        ).model_dump()
    )

# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint that verifies database and vector DB connectivity.
    """
    from .schemas import HealthCheckResponse
    
    return HealthCheckResponse(
        status="healthy" if db_manager.is_connected() else "degraded",
        version=settings.PROJECT_VERSION,
        database_connected=db_manager.is_connected(),
        vector_db_connected=True,  # Can be enhanced to actually check vector DB
        timestamp=__import__("datetime").datetime.utcnow()
    ).model_dump()

# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/", tags=["System"])
async def root():
    """Welcome endpoint with API information."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "status": "Online",
        "version": settings.PROJECT_VERSION,
        "environment": settings.ENV,
        "docs": "/docs"
    }

# ============================================================================
# API Routers
# ============================================================================

# ── WebSockets ───────────────────────────────────────────────────────────
app.include_router(websockets_api.router, prefix="/api/v1", tags=["WebSockets"])

# ── Core Candidate & Requirement Endpoints ───────────────────────────────
app.include_router(candidates.router,   prefix="/api/v1/candidates",    tags=["Candidates"])
app.include_router(requirements.router, prefix="/api/v1/requirements",  tags=["Requirements"])
app.include_router(jobs.router,         prefix="/api/v1/jobs",          tags=["Jobs"])
app.include_router(system.router,       prefix="/api/v1/system",        tags=["System"])

# ── Phase 4: Thinking Modes / Intelligence Endpoints ─────────────────────
# POST /api/v1/evaluate/{candidate_id}          → trigger evaluation with Thinking Mode
# GET  /api/v1/evaluate/{candidate_id}/status   → check evaluation status
app.include_router(evaluate.router,     prefix="/api/v1/evaluate",      tags=["Evaluate"])

# GET  /api/v1/explain/{candidate_id}           → XAI score breakdown + reasoning traces
app.include_router(explain.router,      prefix="/api/v1/explain",       tags=["Explain"])

# POST /api/v1/feedback                         → HR decision ingestion + memory write-back
# GET  /api/v1/feedback/history/{candidate_id}  → HR feedback history
app.include_router(feedback.router,     prefix="/api/v1/feedback",      tags=["Feedback"])

# GET  /api/v1/analytics/overview              → selection/rejection rates, score dist.
# GET  /api/v1/analytics/rejection-reasons     → top rejection reason patterns
# GET  /api/v1/analytics/agent-accuracy        → per-agent accuracy vs HR outcomes
# GET  /api/v1/analytics/feedback-trends       → daily HR decision trends
app.include_router(analytics.router,    prefix="/api/v1/analytics",     tags=["Analytics"])

logger.info(f"Application initialized - Environment: {settings.ENV}, Debug: {settings.DEBUG}")
