"""
Request/Response logging middleware for FastAPI.
Provides request ID tracking and comprehensive logging.
"""

import logging
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure logger
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses with unique request IDs.
    Tracks request duration and logs errors with context.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request, log it, and log the response.
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Record start time
        start_time = time.time()
        
        # Log incoming request
        self.logger.info(
            f"[{request_id}] {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
            }
        )
        
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception with request context
            duration = time.time() - start_time
            self.logger.error(
                f"[{request_id}] Request failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration * 1000,
                    "error": str(e),
                },
                exc_info=True
            )
            raise
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Log response
        self.logger.info(
            f"[{request_id}] {request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration * 1000,
            }
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response

def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure application-wide logging.
    Suppresses verbose background connection errors from PyMongo.
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Set up main application logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("app.log"),
        ]
    )
    
    # Suppress verbose PyMongo background connection errors
    # These are not critical - the driver will retry connections
    logging.getLogger('pymongo.client').setLevel(logging.WARNING)
    logging.getLogger('pymongo.pool').setLevel(logging.WARNING)
    logging.getLogger('pymongo.server').setLevel(logging.WARNING)
    logging.getLogger('pymongo.topology').setLevel(logging.WARNING)
    logging.getLogger('motor').setLevel(logging.WARNING)
