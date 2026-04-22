"""
Agent utilities and decorators for error handling, retry logic, and performance optimization.
Provides robust patterns for all agent operations.
"""

import asyncio
import logging
import functools
import time
from typing import Any, Callable, TypeVar, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RetryStrategy(str, Enum):
    """Retry strategy options."""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"

@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    backoff_multiplier: float = 2.0
    jitter: bool = True

def async_retry(
    config: Optional[RetryConfig] = None,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorator for async functions with automatic retry and exponential backoff.
    
    Args:
        config: RetryConfig with retry settings
        exceptions: Tuple of exceptions to catch and retry on
        on_retry: Callback function(attempt, delay, error) for logging
    
    Example:
        @async_retry(config=RetryConfig(max_retries=3))
        async def my_agent_function():
            return await expensive_llm_call()
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_retries:
                        logger.error(
                            f"Max retries exceeded for {func.__name__}",
                            extra={
                                "function": func.__name__,
                                "attempts": attempt + 1,
                                "error": str(e)
                            },
                            exc_info=True
                        )
                        raise
                    
                    # Calculate delay based on strategy
                    if config.strategy == RetryStrategy.EXPONENTIAL:
                        delay = min(
                            config.initial_delay * (config.backoff_multiplier ** attempt),
                            config.max_delay
                        )
                    elif config.strategy == RetryStrategy.LINEAR:
                        delay = min(
                            config.initial_delay * (attempt + 1),
                            config.max_delay
                        )
                    else:  # FIXED
                        delay = config.initial_delay
                    
                    # Add jitter
                    if config.jitter:
                        import random
                        delay *= (0.5 + random.random())
                    
                    # Call callback if provided
                    if on_retry:
                        on_retry(attempt + 1, delay, e)
                    
                    logger.warning(
                        f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                        f"after {delay:.2f}s: {str(e)}"
                    )
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator

class CircuitBreaker:
    """
    Circuit breaker pattern implementation for preventing cascading failures.
    
    States:
    - CLOSED: Normal operation
    - OPEN: Failing, reject requests
    - HALF_OPEN: Testing if service recovered
    """
    
    class State(Enum):
        CLOSED = "closed"
        OPEN = "open"
        HALF_OPEN = "half_open"
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = self.State.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function through circuit breaker."""
        if self.state == self.State.OPEN:
            if self._should_attempt_reset():
                self.state = self.State.HALF_OPEN
                logger.info(f"Circuit breaker entering HALF_OPEN state")
            else:
                raise RuntimeError(
                    f"Circuit breaker is OPEN. Service unavailable. "
                    f"Retry in {self.recovery_timeout}s"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function through circuit breaker."""
        if self.state == self.State.OPEN:
            if self._should_attempt_reset():
                self.state = self.State.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise RuntimeError(
                    f"Circuit breaker is OPEN. Service unavailable. "
                    f"Retry in {self.recovery_timeout}s"
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        if self.state == self.State.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:  # 2 successes = fully recovered
                self.state = self.State.CLOSED
                self.success_count = 0
                logger.info("Circuit breaker reset to CLOSED state")
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count = 0
        
        if self.failure_count >= self.failure_threshold:
            self.state = self.State.OPEN
            logger.error(
                f"Circuit breaker opened after {self.failure_count} failures"
            )
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout

def track_performance(func: Callable) -> Callable:
    """
    Decorator to track execution time and log performance metrics.
    """
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(
                f"Agent {func.__name__} completed successfully",
                extra={
                    "function": func.__name__,
                    "duration_ms": duration * 1000,
                    "status": "success"
                }
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Agent {func.__name__} failed",
                extra={
                    "function": func.__name__,
                    "duration_ms": duration * 1000,
                    "status": "error",
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(
                f"Agent {func.__name__} completed successfully",
                extra={
                    "function": func.__name__,
                    "duration_ms": duration * 1000,
                    "status": "success"
                }
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Agent {func.__name__} failed",
                extra={
                    "function": func.__name__,
                    "duration_ms": duration * 1000,
                    "status": "error",
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    # Return appropriate wrapper based on function type
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

def get_fallback_response(agent_type: str, error: Exception) -> dict:
    """
    Provides safe fallback responses when agents fail.
    Prevents entire pipeline from breaking on single agent failure.
    """
    fallback_responses = {
        "screener": {
            "visa_status": "unknown",
            "location_match": "remote_only",
            "experience_level": "unknown",
            "education_score": 5,
            "marks_percentage": 0.0,
            "internship_score": 0,
            "internship_details": {"prestige_tier": "None", "duration_months": 0, "role_relevance": 0, "summary": "Analysis unavailable"},
            "certification_score": 0,
            "certifications_found": [],
            "summary": "Screener agent failed - manual review recommended",
            "passed": None,
            "stability_score": 5,
            "consistency_checks": []
        },
        "tech": {
            "tech_stack_match": "medium",
            "system_design_experience": "N/A",
            "problem_solving_indicators": "N/A",
            "technical_red_flags": ["Analysis unavailable"],
            "key_technologies": [],
            "evaluated_skills": [],
            "project_complexity_score": 5,
            "project_category": "Student/Academic",
            "project_verification_note": "Manual review needed",
            "summary": "Tech agent failed - analysis unavailable",
            "technical_fit_score": 5,
            "potential_score": 5,
            "growth_indicators": []
        },
        "culture": {
            "communication_style": "detailed",
            "leadership_potential": False,
            "collaborative_tone": 5,
            "soft_skills": [],
            "soft_skills_score": 1,
            "summary": "Culture analysis unavailable",
            "culture_fit_score": 5,
            "adaptability_score": 5,
            "learning_curve_indicators": []
        },
        "extracurricular": {
            "activities": [],
            "leadership_roles": [],
            "social_impact": "Unknown",
            "extracurricular_score": 1,
            "summary": "No extracurricular data available"
        },
        "hackathon": {
            "hackathons_found": [],
            "wins_and_top_tier": [],
            "participation_percentage": 0,
            "hackathon_score": 0,
            "summary": "No hackathon data available"
        },
        "code_quality": {
            "source_files_found": [],
            "coding_style_note": "Unable to analyze",
            "security_awareness": "Unknown",
            "documentation_quality": "Unknown",
            "code_quality_score": 1
        }
    }
    
    response = fallback_responses.get(agent_type, {})
    response["_error"] = str(error)
    response["_fallback"] = True
    
    logger.warning(
        f"Returning fallback response for {agent_type}",
        extra={"agent": agent_type, "error": str(error)}
    )
    
    return response
