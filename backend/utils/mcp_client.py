"""
MCP Client Gateway (v2) — Enterprise-Grade Centralized Control Plane
=====================================================================
ALL agent ↔ external tool communication MUST pass through this gateway.

Features:
- Tool Registry integration (per-tool timeouts, retries, rate limits)
- RBAC v2 permission enforcement (READ/WRITE/EXECUTE/ADMIN + category access)
- Per-tool circuit breakers (prevents cascading failures)
- Per-agent/per-tool sliding window rate limiter
- Exponential backoff WITH jitter (prevents thundering herd)
- Structured JSON logging with correlation IDs
- Write-operation audit trails
- Backward compatible — agents call invoke_tool(agent_id, tool_name, args) unchanged

Architecture:
    Agent → invoke_tool() → [Permission Check] → [Rate Limit] → [Circuit Breaker]
         → [Timeout + Retry w/ Jitter] → MCP Server → [Structured Log] → Response
"""

import asyncio
import contextlib
import json
import logging
import os
import random
import time
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from utils.mcp_registry import (
    TOOL_REGISTRY,
    AGENT_ROLES,
    ToolDefinition,
    AgentRole,
    PermissionLevel,
    ToolCategory,
    get_tool,
    get_agent_role,
    is_authorized,
)
from utils.mcp_logger import (
    MCPLogEvent,
    MCPStructuredLogger,
    mcp_logger,
)

logger = logging.getLogger(__name__)

# Suppress noisy anyio task group warnings during shutdown
logging.getLogger("anyio._backends._asyncio").setLevel(logging.CRITICAL)
logging.getLogger("asyncio").setLevel(logging.ERROR)




class UnauthorizedToolException(Exception):
    """Raised when an agent attempts to access a tool outside of its authorized scope."""
    pass


class RateLimitExceededException(Exception):
    """Raised when an agent exceeds the rate limit for a tool."""
    pass


class CircuitBreakerOpenException(Exception):
    """Raised when a tool's circuit breaker is in OPEN state."""
    pass



class ToolCircuitBreaker:
    """
    Circuit breaker for a single MCP tool.

    States:
    - CLOSED: Normal operation — requests pass through
    - OPEN:   Too many failures — requests rejected immediately
    - HALF_OPEN: Testing recovery — one request allowed through
    """

    def __init__(self, tool_name: str, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.tool_name = tool_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"

    def can_execute(self) -> bool:
        """Check if a request can pass through the circuit breaker."""
        if self.state == "closed":
            return True

        if self.state == "open":
            if self._should_attempt_reset():
                old_state = self.state
                self.state = "half_open"
                mcp_logger.log_circuit_breaker_event(
                    self.tool_name, old_state, "half_open", self.failure_count
                )
                return True
            return False

        # half_open — allow one request
        return True

    def record_success(self) -> None:
        """Record a successful call."""
        self.failure_count = 0
        if self.state == "half_open":
            self.success_count += 1
            if self.success_count >= 2:
                old_state = self.state
                self.state = "closed"
                self.success_count = 0
                mcp_logger.log_circuit_breaker_event(
                    self.tool_name, old_state, "closed", 0
                )

    def record_failure(self) -> None:
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count = 0

        if self.failure_count >= self.failure_threshold:
            old_state = self.state
            self.state = "open"
            mcp_logger.log_circuit_breaker_event(
                self.tool_name, old_state, "open", self.failure_count
            )

    def _should_attempt_reset(self) -> bool:
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout




class SlidingWindowRateLimiter:
    """
    Per-agent/per-tool sliding window rate limiter.

    Tracks invocation timestamps in a 60-second window.
    Rejects calls that exceed the configured limit.
    """

    def __init__(self):
        # Key: "{agent_id}:{tool_name}" → list of timestamps
        self._windows: Dict[str, List[float]] = defaultdict(list)

    def check_rate_limit(self, agent_id: str, tool_name: str, limit: int, window_sec: int = 60) -> bool:
        """
        Check if the agent is within the rate limit for this tool.

        Returns:
            True if the request is allowed, False if rate limited
        """
        key = f"{agent_id}:{tool_name}"
        now = time.time()
        cutoff = now - window_sec

        # Prune expired timestamps
        self._windows[key] = [ts for ts in self._windows[key] if ts > cutoff]

        if len(self._windows[key]) >= limit:
            return False

        self._windows[key].append(now)
        return True

    def get_remaining(self, agent_id: str, tool_name: str, limit: int, window_sec: int = 60) -> int:
        """Get remaining requests in the current window."""
        key = f"{agent_id}:{tool_name}"
        now = time.time()
        cutoff = now - window_sec
        active = [ts for ts in self._windows[key] if ts > cutoff]
        return max(0, limit - len(active))


# ============================================================================
# MCPClientManager — The Central Gateway
# ============================================================================

class MCPClientManager:
    """
    Singleton Manager for the MCP stdio Client with enterprise features:
    - Tool Registry integration (per-tool configs)
    - RBAC v2 Permission enforcement
    - Per-tool circuit breakers
    - Per-agent/per-tool rate limiting
    - Exponential backoff with jitter
    - Structured JSON logging with correlation IDs
    - Write-operation audit trails
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MCPClientManager, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return

        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        mcp_script_path = os.path.join(script_dir, "mcp_server.py")

        self.server_params = StdioServerParameters(
            command="python",
            args=[mcp_script_path],
            env=os.environ.copy()
        )
        self.exit_stack = None
        self.session: Optional[ClientSession] = None
        self.read_stream = None
        self.write_stream = None

        # Infrastructure
        self._circuit_breakers: Dict[str, ToolCircuitBreaker] = {}
        self._rate_limiter = SlidingWindowRateLimiter()
        self._logger = mcp_logger

        self.initialized = True

    # ── Connection Management ─────────────────────────────────────────────

    async def connect(self):
        """Initializes the MCP ClientSession using the stdio transport."""
        if self.session:
            return

        logger.info("[MCPClient] Initializing strict MCP stdio client connection...")
        self.exit_stack = contextlib.AsyncExitStack()

        try:
            self.read_stream, self.write_stream = await self.exit_stack.enter_async_context(
                stdio_client(self.server_params)
            )

            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.read_stream, self.write_stream)
            )

            await self.session.initialize()
            logger.info("[MCPClient] Connected to mcp_server.py successfully")

            # Validate registry completeness against live server tools
            await self._validate_registry()

        except Exception as e:
            logger.error(f"[MCPClient] Connection failed: {e}")
            raise

    async def disconnect(self):
        """Gracefully tears down the MCP client session."""
        if self.exit_stack:
            try:
                await self.exit_stack.aclose()
            except RuntimeError as e:
                # anyio task group cancel scope error during shutdown — suppress and continue
                # This is a harmless cleanup issue that occurs when the event loop is shutting down
                # and the cancel scope is being exited in a different task context
                if "Attempted to exit cancel scope in a different task" in str(e):
                    logger.warning(f"[MCPClient] Harmless cleanup error during shutdown (ignored): {e}")
                else:
                    logger.error(f"[MCPClient] Error during disconnect: {e}", exc_info=True)
                    raise
            except Exception as e:
                logger.error(f"[MCPClient] Unexpected error during disconnect: {e}", exc_info=True)
            finally:
                self.session = None
                self.read_stream = None
                self.write_stream = None
                logger.info("[MCPClient] Disconnected.")

    async def _validate_registry(self):
        """Validate that every live MCP server tool is in our registry."""
        try:
            tools_result = await self.session.list_tools()
            if tools_result and hasattr(tools_result, 'tools'):
                server_tool_names = [t.name for t in tools_result.tools]
                from utils.mcp_registry import validate_registry_completeness
                unregistered = validate_registry_completeness(server_tool_names)
                if unregistered:
                    logger.warning(
                        f"[MCPClient] REGISTRY GAP: {len(unregistered)} tools on server "
                        f"are NOT in the registry: {unregistered}"
                    )
                else:
                    logger.info(
                        f"[MCPClient] Registry validated — all {len(server_tool_names)} "
                        f"server tools are registered"
                    )
        except Exception as e:
            logger.warning(f"[MCPClient] Registry validation skipped: {e}")

    # ── Circuit Breaker Management ────────────────────────────────────────

    def _get_circuit_breaker(self, tool_name: str) -> ToolCircuitBreaker:
        """Get or create a circuit breaker for a tool."""
        if tool_name not in self._circuit_breakers:
            tool_def = get_tool(tool_name)
            threshold = tool_def.circuit_breaker_threshold if tool_def else 5
            self._circuit_breakers[tool_name] = ToolCircuitBreaker(
                tool_name=tool_name,
                failure_threshold=threshold,
                recovery_timeout=60.0,
            )
        return self._circuit_breakers[tool_name]

    # ── Rate Limit Resolution ─────────────────────────────────────────────

    def _resolve_rate_limit(self, agent_id: str, tool_name: str) -> int:
        """
        Determine the effective rate limit for this agent + tool.
        Priority: agent override > tool-specific > global default (30/min)
        """
        agent_role = get_agent_role(agent_id)
        if agent_role and agent_role.rate_limit_override is not None:
            return agent_role.rate_limit_override

        tool_def = get_tool(tool_name)
        if tool_def:
            return tool_def.rate_limit_per_minute

        return 30  # Global default

    # ── Main Invocation Method ────────────────────────────────────────────

    async def invoke_tool(
        self,
        agent_id: str,
        tool_name: str,
        arguments: dict,
        max_retries: Optional[int] = None,
        timeout_sec: Optional[int] = None,
    ) -> Any:
        """
        Invokes an MCP tool with full enterprise enforcement chain.

        Pipeline:
        1. RBAC permission check (registry-based)
        2. Rate limit enforcement (sliding window)
        3. Circuit breaker check
        4. Timeout + retry with exponential backoff + jitter
        5. Structured logging + metrics accumulation
        6. Write-operation audit trail

        Args:
            agent_id: Identifier of the calling agent
            tool_name: MCP tool to invoke
            arguments: Tool arguments dict
            max_retries: Override per-tool retry count (optional)
            timeout_sec: Override per-tool timeout (optional)

        Returns:
            Tool result text, or None if the tool returned empty content

        Raises:
            UnauthorizedToolException: If RBAC check fails
            RateLimitExceededException: If rate limit exceeded
            CircuitBreakerOpenException: If circuit breaker is open
            Exception: On max retries exhausted
        """
        correlation_id = self._logger.generate_correlation_id()

        # ── Resolve tool config from registry ─────────────────────────────
        tool_def = get_tool(tool_name)
        effective_retries = max_retries if max_retries is not None else (tool_def.max_retries if tool_def else 3)
        effective_timeout = timeout_sec if timeout_sec is not None else (tool_def.timeout_sec if tool_def else 15)
        tool_category = tool_def.category.value if tool_def else "unknown"
        is_write = tool_def.is_write_operation if tool_def else False

        # ── 1. RBAC PERMISSION CHECK ──────────────────────────────────────
        if not is_authorized(agent_id, tool_name):
            reason = self._build_denial_reason(agent_id, tool_name, tool_def)
            self._logger.log_permission_violation(
                agent_id=agent_id,
                tool_name=tool_name,
                reason=reason,
                correlation_id=correlation_id,
            )
            raise UnauthorizedToolException(
                f"Agent '{agent_id}' is NOT AUTHORIZED to use tool '{tool_name}'. {reason}"
            )

        # ── 2. RATE LIMIT ENFORCEMENT ─────────────────────────────────────
        rate_limit = self._resolve_rate_limit(agent_id, tool_name)
        if not self._rate_limiter.check_rate_limit(agent_id, tool_name, rate_limit):
            self._logger.log_rate_limit_event(
                agent_id=agent_id,
                tool_name=tool_name,
                limit=rate_limit,
                correlation_id=correlation_id,
            )
            raise RateLimitExceededException(
                f"Agent '{agent_id}' exceeded rate limit ({rate_limit}/min) for tool '{tool_name}'"
            )

        # ── 3. CIRCUIT BREAKER CHECK ──────────────────────────────────────
        cb = self._get_circuit_breaker(tool_name)
        if not cb.can_execute():
            self._logger.log_invocation(MCPLogEvent(
                event="mcp_tool_invocation",
                correlation_id=correlation_id,
                agent_id=agent_id,
                tool_name=tool_name,
                attempt=0,
                max_retries=effective_retries,
                duration_ms=0,
                status="circuit_breaker_open",
                circuit_breaker_state="open",
                tool_category=tool_category,
            ))
            raise CircuitBreakerOpenException(
                f"Circuit breaker OPEN for tool '{tool_name}'. Service unavailable."
            )

        # ── 4. WRITE OPERATION AUDIT ──────────────────────────────────────
        if is_write:
            self._logger.log_write_operation(agent_id, tool_name, correlation_id)

        # ── 5. AUTO-CONNECT ───────────────────────────────────────────────
        if not self.session:
            await self.connect()

        # ── 6. TIMEOUT + RETRY WITH EXPONENTIAL BACKOFF + JITTER ──────────
        attempt = 0
        backoff = 1.0  # Initial backoff in seconds

        while attempt <= effective_retries:
            attempt += 1
            start_time = time.time()

            try:
                result = await asyncio.wait_for(
                    self.session.call_tool(tool_name, arguments),
                    timeout=effective_timeout,
                )

                duration_ms = int((time.time() - start_time) * 1000)
                status = "success"
                if getattr(result, "isError", False):
                    status = "tool_error"

                cb.record_success()

                remaining = self._rate_limiter.get_remaining(agent_id, tool_name, rate_limit)

                self._logger.log_invocation(MCPLogEvent(
                    event="mcp_tool_invocation",
                    correlation_id=correlation_id,
                    agent_id=agent_id,
                    tool_name=tool_name,
                    attempt=attempt,
                    max_retries=effective_retries,
                    duration_ms=duration_ms,
                    status=status,
                    circuit_breaker_state=cb.state,
                    is_write_operation=is_write,
                    tool_category=tool_category,
                    rate_limit_remaining=remaining,
                ))

                # Extract response text
                if result.content and len(result.content) > 0:
                    return result.content[0].text
                return None

            except asyncio.TimeoutError:
                duration_ms = int((time.time() - start_time) * 1000)
                cb.record_failure()

                self._logger.log_invocation(MCPLogEvent(
                    event="mcp_tool_invocation",
                    correlation_id=correlation_id,
                    agent_id=agent_id,
                    tool_name=tool_name,
                    attempt=attempt,
                    max_retries=effective_retries,
                    duration_ms=duration_ms,
                    status="timeout",
                    circuit_breaker_state=cb.state,
                    tool_category=tool_category,
                ))

                if attempt > effective_retries:
                    raise Exception(
                        f"Tool '{tool_name}' timed out after {effective_retries} retries "
                        f"(timeout={effective_timeout}s). [cid={correlation_id}]"
                    )

                # Exponential backoff with jitter
                jitter = random.uniform(0.5, 1.5)
                sleep_time = min(backoff * jitter, 30.0)
                await asyncio.sleep(sleep_time)
                backoff *= 2

            except (UnauthorizedToolException, RateLimitExceededException, CircuitBreakerOpenException):
                raise  # Don't retry auth/rate/cb errors

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                cb.record_failure()

                self._logger.log_invocation(MCPLogEvent(
                    event="mcp_tool_invocation",
                    correlation_id=correlation_id,
                    agent_id=agent_id,
                    tool_name=tool_name,
                    attempt=attempt,
                    max_retries=effective_retries,
                    duration_ms=duration_ms,
                    status="error",
                    circuit_breaker_state=cb.state,
                    tool_category=tool_category,
                    error_message=str(e),
                ))

                if attempt > effective_retries:
                    raise Exception(
                        f"Tool '{tool_name}' failed after {effective_retries} retries: "
                        f"{str(e)} [cid={correlation_id}]"
                    )

                # Exponential backoff with jitter
                jitter = random.uniform(0.5, 1.5)
                sleep_time = min(backoff * jitter, 30.0)
                await asyncio.sleep(sleep_time)
                backoff *= 2

    # ── RBAC Denial Reason Builder ────────────────────────────────────────

    def _build_denial_reason(self, agent_id: str, tool_name: str, tool_def: Optional[ToolDefinition]) -> str:
        """Construct a detailed denial reason for logging and error messages."""
        role = get_agent_role(agent_id)

        if role is None:
            return f"Agent '{agent_id}' has no role defined in AGENT_ROLES."

        if tool_def is None:
            return f"Tool '{tool_name}' is not registered in TOOL_REGISTRY."

        if tool_def.permission_level not in role.permissions:
            return (
                f"Agent has permissions {[p.value for p in role.permissions]} "
                f"but tool requires '{tool_def.permission_level.value}'."
            )

        return (
            f"Tool '{tool_name}' is not in agent's allowed_tools "
            f"and category '{tool_def.category.value}' is not in agent's allowed_categories."
        )

    # ── Metrics & Introspection ───────────────────────────────────────────

    def get_tool_metrics(self, tool_name: str) -> Optional[Dict]:
        """Get metrics for a specific tool."""
        return self._logger.get_tool_metrics(tool_name)

    def get_all_metrics(self) -> Dict[str, Dict]:
        """Get metrics for all tools."""
        return self._logger.get_all_metrics()

    def get_circuit_breaker_states(self) -> Dict[str, str]:
        """Get current state of all circuit breakers."""
        return {name: cb.state for name, cb in self._circuit_breakers.items()}


# ============================================================================
# Global Singleton
# ============================================================================

mcp_client_manager = MCPClientManager()
