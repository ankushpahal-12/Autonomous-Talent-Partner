"""
MCP Structured Logger
======================
Enterprise-grade structured JSON logging for the MCP gateway layer.

Features:
- Every log entry includes: timestamp, correlation_id, agent_id, tool_name, duration, status
- Per-tool metrics tracking (invocations, success/failure/timeout counts, avg latency)
- Dedicated methods for: invocations, permission violations, circuit breaker events, rate limits
- Thread-safe metrics accumulation

All logs are emitted as JSON via Python's standard logging module.
"""

import json
import logging
import time
import uuid
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional


logger = logging.getLogger("mcp.gateway")


@dataclass
class MCPLogEvent:
    """Structured log entry for a single MCP tool invocation."""
    event: str                                  # "mcp_tool_invocation"
    correlation_id: str                         # UUID for request tracing
    agent_id: str
    tool_name: str
    attempt: int                                # 1-based attempt number
    max_retries: int
    duration_ms: int
    status: str                                 # success | timeout | error | rate_limited | unauthorized
    timestamp: str = ""                         # ISO 8601 — auto-populated
    circuit_breaker_state: Optional[str] = None # closed | open | half_open
    is_write_operation: bool = False
    error_message: Optional[str] = None
    tool_category: Optional[str] = None
    rate_limit_remaining: Optional[int] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()




@dataclass
class ToolMetrics:
    """Running metrics for a single MCP tool."""
    tool_name: str
    total_invocations: int = 0
    success_count: int = 0
    failure_count: int = 0
    timeout_count: int = 0
    rate_limited_count: int = 0
    unauthorized_count: int = 0
    total_latency_ms: float = 0.0
    last_invoked_at: Optional[str] = None
    circuit_breaker_trips: int = 0

    @property
    def avg_latency_ms(self) -> float:
        if self.total_invocations == 0:
            return 0.0
        return round(self.total_latency_ms / self.total_invocations, 2)

    @property
    def success_rate(self) -> float:
        if self.total_invocations == 0:
            return 0.0
        return round((self.success_count / self.total_invocations) * 100, 2)

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "total_invocations": self.total_invocations,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "timeout_count": self.timeout_count,
            "rate_limited_count": self.rate_limited_count,
            "unauthorized_count": self.unauthorized_count,
            "avg_latency_ms": self.avg_latency_ms,
            "success_rate": self.success_rate,
            "last_invoked_at": self.last_invoked_at,
            "circuit_breaker_trips": self.circuit_breaker_trips,
        }


class MCPStructuredLogger:
    """
    Centralized structured logger for ALL MCP gateway operations.

    Thread-safe. Accumulates per-tool metrics and emits JSON logs.
    """

    def __init__(self):
        self._metrics: Dict[str, ToolMetrics] = {}
        self._lock = threading.Lock()

    def _ensure_metrics(self, tool_name: str) -> ToolMetrics:
        """Lazily create metrics for a tool (thread-safe)."""
        if tool_name not in self._metrics:
            with self._lock:
                if tool_name not in self._metrics:
                    self._metrics[tool_name] = ToolMetrics(tool_name=tool_name)
        return self._metrics[tool_name]

    def log_invocation(self, event: MCPLogEvent) -> None:
        """
        Log a tool invocation and update metrics.
        This is the primary logging method — called on every invoke_tool() completion.
        """
        metrics = self._ensure_metrics(event.tool_name)

        with self._lock:
            metrics.total_invocations += 1
            metrics.total_latency_ms += event.duration_ms
            metrics.last_invoked_at = event.timestamp

            if event.status == "success":
                metrics.success_count += 1
            elif event.status == "timeout":
                metrics.timeout_count += 1
            elif event.status == "rate_limited":
                metrics.rate_limited_count += 1
            elif event.status == "unauthorized":
                metrics.unauthorized_count += 1
            else:
                metrics.failure_count += 1

        log_dict = asdict(event)
        log_dict = {k: v for k, v in log_dict.items() if v is not None}

        if event.status in ("success",):
            logger.info(json.dumps(log_dict))
        elif event.status in ("timeout", "rate_limited"):
            logger.warning(json.dumps(log_dict))
        else:
            logger.error(json.dumps(log_dict))


    def log_permission_violation(
        self,
        agent_id: str,
        tool_name: str,
        reason: str,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Log an RBAC permission violation (always ERROR level)."""
        metrics = self._ensure_metrics(tool_name)
        with self._lock:
            metrics.unauthorized_count += 1

        violation = {
            "event": "mcp_permission_violation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "agent_id": agent_id,
            "tool_name": tool_name,
            "reason": reason,
            "severity": "CRITICAL",
        }
        logger.error(json.dumps(violation))

    def log_circuit_breaker_event(
        self,
        tool_name: str,
        old_state: str,
        new_state: str,
        failure_count: int,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Log a circuit breaker state transition."""
        metrics = self._ensure_metrics(tool_name)
        if new_state == "open":
            with self._lock:
                metrics.circuit_breaker_trips += 1

        cb_event = {
            "event": "mcp_circuit_breaker",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "tool_name": tool_name,
            "old_state": old_state,
            "new_state": new_state,
            "failure_count": failure_count,
        }

        if new_state == "open":
            logger.error(json.dumps(cb_event))
        elif new_state == "half_open":
            logger.warning(json.dumps(cb_event))
        else:
            logger.info(json.dumps(cb_event))

    def log_rate_limit_event(
        self,
        agent_id: str,
        tool_name: str,
        limit: int,
        window_seconds: int = 60,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Log a rate limit breach."""
        metrics = self._ensure_metrics(tool_name)
        with self._lock:
            metrics.rate_limited_count += 1

        rl_event = {
            "event": "mcp_rate_limit_exceeded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id or str(uuid.uuid4()),
            "agent_id": agent_id,
            "tool_name": tool_name,
            "limit": limit,
            "window_seconds": window_seconds,
            "severity": "WARNING",
        }
        logger.warning(json.dumps(rl_event))

    def log_write_operation(
        self,
        agent_id: str,
        tool_name: str,
        correlation_id: str,
    ) -> None:
        """Extra audit log for write operations (DB mutations)."""
        write_event = {
            "event": "mcp_write_operation",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
            "agent_id": agent_id,
            "tool_name": tool_name,
            "audit": True,
        }
        logger.info(json.dumps(write_event))

    # ── Metrics Access ────────────────────────────────────────────────────

    def get_tool_metrics(self, tool_name: str) -> Optional[Dict]:
        """Retrieve metrics for a specific tool."""
        metrics = self._metrics.get(tool_name)
        if metrics:
            return metrics.to_dict()
        return None

    def get_all_metrics(self) -> Dict[str, Dict]:
        """Retrieve metrics for all tools."""
        return {name: m.to_dict() for name, m in self._metrics.items()}

    def generate_correlation_id(self) -> str:
        """Generate a new correlation ID for request tracing."""
        return str(uuid.uuid4())


# ============================================================================
# Global Singleton
# ============================================================================

mcp_logger = MCPStructuredLogger()
