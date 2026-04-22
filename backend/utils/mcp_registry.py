"""
MCP Tool Registry & RBAC Permission Layer (v2)
================================================
Enterprise-grade centralized registry for ALL MCP tools.

Features:
- Per-tool metadata: rate limits, timeouts, circuit breaker thresholds
- Tool categorization (DATABASE, API, AGENT_PIPELINE, KNOWLEDGE_GRAPH, SYSTEM)
- RBAC v2: PermissionLevel (READ/WRITE/EXECUTE/ADMIN), AgentRole with category access
- Registry validation at startup
- Write-operation guardrails and audit flagging

Every call to `mcp_client_manager.invoke_tool()` consults this registry.
Agents require ZERO changes — this is purely gateway infrastructure.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set



class ToolCategory(str, Enum):
    """Categorizes MCP tools by their domain."""
    DATABASE = "database"
    API = "api"
    AGENT_PIPELINE = "agent_pipeline"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    SYSTEM = "system"
    VECTOR_DB = "vector_db"
    FAIR_HIRING = "fair_hiring"


class PermissionLevel(str, Enum):
    """Granular permission levels for RBAC enforcement."""
    READ = "read"           # Query / search operations
    WRITE = "write"         # Mutating operations (DB inserts/updates)
    EXECUTE = "execute"     # Agent pipeline triggers
    ADMIN = "admin"         # System-level operations (health check, maintenance)



@dataclass(frozen=True)
class ToolDefinition:
    """
    Complete metadata for a single MCP tool.

    Attributes:
        name: Exact tool function name on the MCP server
        category: Functional domain (DATABASE, API, etc.)
        description: Human-readable purpose
        allowed_agents: Agent IDs authorized to invoke this tool
        permission_level: Minimum permission required
        rate_limit_per_minute: Max invocations per agent per minute
        timeout_sec: Per-tool timeout (overrides global default)
        max_retries: Per-tool retry ceiling
        requires_auth: Marks tools that need elevated credentials
        is_write_operation: True for DB mutations — triggers extra audit logging
        circuit_breaker_threshold: Consecutive failures before circuit opens
    """
    name: str
    category: ToolCategory
    description: str
    allowed_agents: tuple  # frozen — use tuple instead of list
    permission_level: PermissionLevel = PermissionLevel.READ
    rate_limit_per_minute: int = 30
    timeout_sec: int = 15
    max_retries: int = 3
    requires_auth: bool = False
    is_write_operation: bool = False
    circuit_breaker_threshold: int = 5



@dataclass
class AgentRole:
    """
    Defines what an agent is authorized to do in the MCP ecosystem.

    Attributes:
        agent_id: Unique identifier matching the value passed to invoke_tool()
        permissions: Set of PermissionLevels the agent holds
        allowed_tools: Explicit tool names this agent can call
        allowed_categories: Tool categories the agent can access (category-level grant)
        rate_limit_override: Agent-specific rate limit (overrides per-tool default)
        description: Human-readable role description
    """
    agent_id: str
    permissions: Set[PermissionLevel]
    allowed_tools: List[str] = field(default_factory=list)
    allowed_categories: List[ToolCategory] = field(default_factory=list)
    rate_limit_override: Optional[int] = None
    description: str = ""



TOOL_REGISTRY: Dict[str, ToolDefinition] = {

    # ── Resume Processing ─────────────────────────────────────────────────
    "process_and_embed_resume": ToolDefinition(
        name="process_and_embed_resume",
        category=ToolCategory.AGENT_PIPELINE,
        description="Full pipeline: parse resume from GridFS → store in MongoDB → sync to Neo4j → embed in vector DB",
        allowed_agents=("lead_agent", "system"),
        permission_level=PermissionLevel.EXECUTE,
        timeout_sec=60,
        max_retries=2,
        is_write_operation=True,
        circuit_breaker_threshold=3,
    ),

    "parse_resume_only": ToolDefinition(
        name="parse_resume_only",
        category=ToolCategory.AGENT_PIPELINE,
        description="Parse resume from GridFS into structured JSON without embedding",
        allowed_agents=("lead_agent", "system"),
        permission_level=PermissionLevel.EXECUTE,
        timeout_sec=45,
        max_retries=2,
        is_write_operation=True,
        circuit_breaker_threshold=3,
    ),

    "embed_candidate_only": ToolDefinition(
        name="embed_candidate_only",
        category=ToolCategory.VECTOR_DB,
        description="Embed parsed candidate profile into ChromaDB vector store",
        allowed_agents=("lead_agent", "system"),
        permission_level=PermissionLevel.WRITE,
        timeout_sec=30,
        max_retries=2,
        is_write_operation=True,
    ),

    # ── Search & Query ────────────────────────────────────────────────────
    "search_candidate_pool": ToolDefinition(
        name="search_candidate_pool",
        category=ToolCategory.VECTOR_DB,
        description="Semantic search of candidate pool against job description",
        allowed_agents=("lead_agent", "db_chat_agent", "system"),
        permission_level=PermissionLevel.READ,
        timeout_sec=20,
        max_retries=2,
        rate_limit_per_minute=60,
    ),

    "search_similar_candidates": ToolDefinition(
        name="search_similar_candidates",
        category=ToolCategory.VECTOR_DB,
        description="Search vector DB for candidates matching a job description",
        allowed_agents=("lead_agent", "db_chat_agent", "system"),
        permission_level=PermissionLevel.READ,
        timeout_sec=20,
        max_retries=2,
        rate_limit_per_minute=60,
    ),

    "tool_search_candidates_in_mongo": ToolDefinition(
        name="tool_search_candidates_in_mongo",
        category=ToolCategory.DATABASE,
        description="Regex search of MongoDB candidates by name, email, or skills",
        allowed_agents=("db_chat_agent",),
        permission_level=PermissionLevel.READ,
        timeout_sec=10,
        max_retries=2,
        rate_limit_per_minute=60,
    ),

    # ── Knowledge Graph ───────────────────────────────────────────────────
    "tool_get_related_skills": ToolDefinition(
        name="tool_get_related_skills",
        category=ToolCategory.KNOWLEDGE_GRAPH,
        description="Query Neo4j for skills related to a given skill node",
        allowed_agents=("db_chat_agent", "lead_agent"),
        permission_level=PermissionLevel.READ,
        timeout_sec=10,
        max_retries=2,
        rate_limit_per_minute=120,
    ),

    # ── AI Review Pipeline ────────────────────────────────────────────────
    "get_candidate_ai_review": ToolDefinition(
        name="get_candidate_ai_review",
        category=ToolCategory.DATABASE,
        description="Retrieve existing AI multi-agent review report for a candidate",
        allowed_agents=("lead_agent", "db_chat_agent", "system"),
        permission_level=PermissionLevel.READ,
        timeout_sec=10,
        max_retries=2,
    ),

    "run_candidate_review": ToolDefinition(
        name="run_candidate_review",
        category=ToolCategory.AGENT_PIPELINE,
        description="Trigger full multi-agent AI evaluation pipeline for a candidate",
        allowed_agents=("lead_agent", "system"),
        permission_level=PermissionLevel.EXECUTE,
        timeout_sec=180,
        max_retries=1,
        is_write_operation=True,
        circuit_breaker_threshold=3,
    ),

    "run_external_scraper": ToolDefinition(
        name="run_external_scraper",
        category=ToolCategory.API,
        description="Trigger scraper agent to enrich candidate with GitHub/LinkedIn data",
        allowed_agents=("lead_agent", "scraper_agent", "system"),
        permission_level=PermissionLevel.EXECUTE,
        timeout_sec=90,
        max_retries=2,
        is_write_operation=True,
    ),

    # ── Database Writes ───────────────────────────────────────────────────
    "tool_db_save_external_eval": ToolDefinition(
        name="tool_db_save_external_eval",
        category=ToolCategory.DATABASE,
        description="Save external intelligence evaluation to MongoDB",
        allowed_agents=("scraper_agent", "lead_agent"),
        permission_level=PermissionLevel.WRITE,
        timeout_sec=10,
        max_retries=3,
        is_write_operation=True,
    ),

    "tool_db_save_complete_eval": ToolDefinition(
        name="tool_db_save_complete_eval",
        category=ToolCategory.DATABASE,
        description="Save complete multi-agent evaluation report to MongoDB",
        allowed_agents=("lead_agent",),
        permission_level=PermissionLevel.WRITE,
        timeout_sec=15,
        max_retries=3,
        is_write_operation=True,
    ),

    # ── System Memory ─────────────────────────────────────────────────────
    "tool_db_get_active_rules": ToolDefinition(
        name="tool_db_get_active_rules",
        category=ToolCategory.DATABASE,
        description="Retrieve active learning rules for a role category",
        allowed_agents=("lead_agent",),
        permission_level=PermissionLevel.READ,
        timeout_sec=10,
        max_retries=2,
    ),

    "tool_get_memory_clusters": ToolDefinition(
        name="tool_get_memory_clusters",
        category=ToolCategory.DATABASE,
        description="Fetch all learning rules grouped by role for maintenance",
        allowed_agents=("learning_supervisor",),
        permission_level=PermissionLevel.READ,
        timeout_sec=15,
        max_retries=2,
    ),

    # ── External API Gateway ──────────────────────────────────────────────
    "tool_http_get": ToolDefinition(
        name="tool_http_get",
        category=ToolCategory.API,
        description="General HTTP GET wrapper for external API calls (GitHub, LinkedIn, etc.)",
        allowed_agents=("scraper_agent",),
        permission_level=PermissionLevel.READ,
        timeout_sec=30,
        max_retries=4,
        requires_auth=False,
        rate_limit_per_minute=120,
        circuit_breaker_threshold=10,
    ),

    # ── Fair Hiring ───────────────────────────────────────────────────────
    "tool_fair_hiring_redact": ToolDefinition(
        name="tool_fair_hiring_redact",
        category=ToolCategory.FAIR_HIRING,
        description="Redact personally identifiable information from resume text for bias reduction",
        allowed_agents=("lead_agent",),
        permission_level=PermissionLevel.READ,
        timeout_sec=10,
        max_retries=2,
    ),

    # ── System ────────────────────────────────────────────────────────────
    "health_check": ToolDefinition(
        name="health_check",
        category=ToolCategory.SYSTEM,
        description="MCP server health check — verifies DB and vector DB connectivity",
        allowed_agents=("system", "lead_agent"),
        permission_level=PermissionLevel.ADMIN,
        timeout_sec=5,
        max_retries=1,
        rate_limit_per_minute=10,
    ),
}


# ============================================================================
# AGENT ROLES — RBAC v2 Definitions
# ============================================================================

AGENT_ROLES: Dict[str, AgentRole] = {

    "lead_agent": AgentRole(
        agent_id="lead_agent",
        permissions={PermissionLevel.READ, PermissionLevel.WRITE, PermissionLevel.EXECUTE},
        allowed_tools=[
            "tool_fair_hiring_redact",
            "tool_db_get_active_rules",
            "tool_get_related_skills",
            "tool_db_save_complete_eval",
            "tool_db_save_external_eval",
            "run_candidate_review",
            "run_external_scraper",
            "process_and_embed_resume",
            "parse_resume_only",
            "embed_candidate_only",
            "search_candidate_pool",
            "search_similar_candidates",
            "get_candidate_ai_review",
            "health_check",
        ],
        allowed_categories=[
            ToolCategory.DATABASE,
            ToolCategory.AGENT_PIPELINE,
            ToolCategory.KNOWLEDGE_GRAPH,
            ToolCategory.VECTOR_DB,
            ToolCategory.FAIR_HIRING,
        ],
        description="Orchestrator agent — has broad access to coordinate all sub-agents",
    ),

    "scraper_agent": AgentRole(
        agent_id="scraper_agent",
        permissions={PermissionLevel.READ, PermissionLevel.WRITE, PermissionLevel.EXECUTE},
        allowed_tools=[
            "tool_http_get",
            "tool_db_save_external_eval",
            "run_external_scraper",
        ],
        allowed_categories=[ToolCategory.API],
        rate_limit_override=90,  # Scraper needs higher throughput for GitHub API
        description="External data enrichment agent — GitHub/LinkedIn scraping",
    ),

    "db_chat_agent": AgentRole(
        agent_id="db_chat_agent",
        permissions={PermissionLevel.READ},
        allowed_tools=[
            "tool_search_candidates_in_mongo",
            "tool_get_related_skills",
            "search_candidate_pool",
            "search_similar_candidates",
            "get_candidate_ai_review",
        ],
        allowed_categories=[ToolCategory.DATABASE, ToolCategory.KNOWLEDGE_GRAPH, ToolCategory.VECTOR_DB],
        description="Database chat agent — READ-only access for natural language queries",
    ),

    "learning_supervisor": AgentRole(
        agent_id="learning_supervisor",
        permissions={PermissionLevel.READ},
        allowed_tools=[
            "tool_get_memory_clusters",
        ],
        allowed_categories=[ToolCategory.DATABASE],
        description="Meta-learning supervisor — reads system memory for rule optimization",
    ),

    "system": AgentRole(
        agent_id="system",
        permissions={PermissionLevel.READ, PermissionLevel.WRITE, PermissionLevel.EXECUTE, PermissionLevel.ADMIN},
        allowed_tools=list(TOOL_REGISTRY.keys()),  # Full access
        allowed_categories=list(ToolCategory),
        description="System-level / admin agent — unrestricted access for health checks and maintenance",
    ),
}


# ============================================================================
# Registry Utilities
# ============================================================================

def get_tool(tool_name: str) -> Optional[ToolDefinition]:
    """Retrieve a tool definition from the registry. Returns None if not found."""
    return TOOL_REGISTRY.get(tool_name)


def get_agent_role(agent_id: str) -> Optional[AgentRole]:
    """Retrieve an agent's role definition. Returns None if not found."""
    return AGENT_ROLES.get(agent_id)


def is_authorized(agent_id: str, tool_name: str) -> bool:
    """
    Full RBAC authorization check.

    Checks (in order):
    1. Agent role exists
    2. Tool exists in registry
    3. Agent has the required PermissionLevel
    4. Tool is in agent's allowed_tools OR agent has access to the tool's category

    Returns:
        True if the agent is authorized to invoke the tool
    """
    role = AGENT_ROLES.get(agent_id)
    if role is None:
        return False

    tool_def = TOOL_REGISTRY.get(tool_name)
    if tool_def is None:
        return False

    # Check permission level
    if tool_def.permission_level not in role.permissions:
        return False

    # Check explicit tool grant OR category grant
    if tool_name in role.allowed_tools:
        return True
    if tool_def.category in role.allowed_categories:
        return True

    return False


def validate_registry_completeness(server_tool_names: List[str]) -> List[str]:
    """
    Validates that every tool on the MCP server is registered.

    Args:
        server_tool_names: List of tool names from the MCP server

    Returns:
        List of unregistered tool names (empty = all good)
    """
    return [name for name in server_tool_names if name not in TOOL_REGISTRY]


def get_registry_summary() -> Dict[str, dict]:
    """Returns a summary dict of all registered tools for admin dashboards."""
    return {
        name: {
            "category": td.category.value,
            "permission": td.permission_level.value,
            "timeout_sec": td.timeout_sec,
            "rate_limit": td.rate_limit_per_minute,
            "max_retries": td.max_retries,
            "is_write": td.is_write_operation,
            "agents": list(td.allowed_agents),
        }
        for name, td in TOOL_REGISTRY.items()
    }
