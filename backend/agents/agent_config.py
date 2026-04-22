"""
Agent configuration and API key management.
Centralizes all agent-specific settings and provides intelligent key rotation.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from .agent_thinking import ThinkingMode

logger = logging.getLogger(__name__)

class AgentType(str, Enum):
    """All agent types in the system."""
    CODE_QUALITY = "code_quality_agent"
    TECH = "tech_agent"
    SCREENER = "screener_agent"
    CULTURE = "culture_agent"
    EXTRACURRICULAR = "extracurricular_agent"
    HACKATHON = "hackathon_agent"
    SKILL_COUNTER = "skill_counter_agent"
    DB_CHAT = "db_chat_agent"
    SCRAPER = "scraper_agent"
    LEARNING_SUPERVISOR = "learning_supervisor_agent"

@dataclass
class AgentConfig:
    """
    Configuration for a single agent.
    Includes cognitive upgrade settings (ThinkingMode, self-reflection toggle).
    """
    name: AgentType
    api_key_index: int
    model: str = "gemini-2.5-flash"
    temperature: float = 0.0
    max_retries: int = 3
    timeout_seconds: int = 60
    description: str = ""
    thinking_mode: ThinkingMode = ThinkingMode.BALANCED
    enable_self_reflection: bool = True

    def __post_init__(self):
        """Validate configuration."""
        if self.temperature < 0 or self.temperature > 1:
            raise ValueError(f"Temperature must be between 0 and 1, got {self.temperature}")
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be non-negative, got {self.max_retries}")
        if self.timeout_seconds <= 0:
            raise ValueError(f"timeout_seconds must be positive, got {self.timeout_seconds}")

class AgentConfigManager:
    """
    Centralized manager for all agent configurations.
    Provides intelligent API key routing and rotation.
    """
    
    def __init__(self):
        """Initialize agent configurations with optimized temperature and settings."""
        self.agents: Dict[AgentType, AgentConfig] = {
            AgentType.CODE_QUALITY: AgentConfig(
                name=AgentType.CODE_QUALITY,
                api_key_index=0,
                temperature=0.2,
                description="Analyzes code quality from external projects",
                timeout_seconds=45,
                thinking_mode=ThinkingMode.STRICT,
                enable_self_reflection=True,
            ),
            AgentType.TECH: AgentConfig(
                name=AgentType.TECH,
                api_key_index=1,
                temperature=0.2,
                description="Evaluates technical depth and project complexity",
                timeout_seconds=60,
                thinking_mode=ThinkingMode.BALANCED,
                enable_self_reflection=True,
            ),
            AgentType.SCREENER: AgentConfig(
                name=AgentType.SCREENER,
                api_key_index=2,
                temperature=0.0,
                description="Checks hard requirements (visa, location, seniority)",
                timeout_seconds=45,
                thinking_mode=ThinkingMode.STRICT,
                enable_self_reflection=False,  # Purely deterministic — no reflection needed
            ),
            AgentType.CULTURE: AgentConfig(
                name=AgentType.CULTURE,
                api_key_index=3,
                temperature=0.3,
                description="Assesses soft skills and culture fit",
                timeout_seconds=45,
                thinking_mode=ThinkingMode.BALANCED,
                enable_self_reflection=True,
            ),
            AgentType.EXTRACURRICULAR: AgentConfig(
                name=AgentType.EXTRACURRICULAR,
                api_key_index=4,
                temperature=0.3,
                description="Evaluates non-technical activities",
                timeout_seconds=45,
                thinking_mode=ThinkingMode.POTENTIAL,
                enable_self_reflection=False,
            ),
            AgentType.HACKATHON: AgentConfig(
                name=AgentType.HACKATHON,
                api_key_index=5,
                temperature=0.2,
                description="Assesses hackathon & competition achievements",
                timeout_seconds=45,
                thinking_mode=ThinkingMode.POTENTIAL,
                enable_self_reflection=False,
            ),
            AgentType.SKILL_COUNTER: AgentConfig(
                name=AgentType.SKILL_COUNTER,
                api_key_index=6,
                temperature=0.0,
                description="Counts skill implementation frequency",
                timeout_seconds=45,
                thinking_mode=ThinkingMode.STRICT,
                enable_self_reflection=False,
            ),
            AgentType.DB_CHAT: AgentConfig(
                name=AgentType.DB_CHAT,
                api_key_index=7,
                temperature=0.0,
                description="Natural language database queries",
                timeout_seconds=30,
                thinking_mode=ThinkingMode.BALANCED,
                enable_self_reflection=False,
            ),
            AgentType.SCRAPER: AgentConfig(
                name=AgentType.SCRAPER,
                api_key_index=8,
                temperature=0.1,
                description="External data enrichment (GitHub, LinkedIn)",
                timeout_seconds=60,
                thinking_mode=ThinkingMode.BALANCED,
                enable_self_reflection=False,
            ),
            AgentType.LEARNING_SUPERVISOR: AgentConfig(
                name=AgentType.LEARNING_SUPERVISOR,
                api_key_index=9,
                temperature=0.1,
                description="Meta-learning and rule optimization",
                timeout_seconds=90,
                thinking_mode=ThinkingMode.BALANCED,
                enable_self_reflection=False,
            ),
        }
        
        self._key_usage_count: Dict[int, int] = {}
        self._key_error_count: Dict[int, int] = {}
    
    def get_config(self, agent_type: AgentType) -> AgentConfig:
        """
        Get configuration for a specific agent.
        
        Args:
            agent_type: The agent to get config for
            
        Returns:
            AgentConfig for the agent
        """
        if agent_type not in self.agents:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        return self.agents[agent_type]
    
    def get_api_key_index(self, agent_type: AgentType) -> int:
        """
        Get the API key index for an agent.
        With rotation enabled, intelligently selects least-used key.
        
        Args:
            agent_type: The agent type
            
        Returns:
            API key index (0-based)
        """
        from app.core.config import settings
        
        config = self.get_config(agent_type)
        base_index = config.api_key_index
        
        # If rotation is disabled, return base index
        if not settings.API_KEY_ROTATION_ENABLED:
            return base_index
        
        # Find least-used key among available keys
        available_keys = len(settings.GOOGLE_API_KEYS)
        if available_keys == 0:
            logger.error("No API keys available")
            return base_index
        
        # Get usage counts for recent keys
        min_usage = float('inf')
        best_index = base_index % available_keys
        
        for key_idx in range(available_keys):
            usage = self._key_usage_count.get(key_idx, 0)
            error_count = self._key_error_count.get(key_idx, 0)
            
            # Penalize keys with errors
            score = usage + (error_count * 5)
            
            if score < min_usage:
                min_usage = score
                best_index = key_idx
        
        return best_index
    
    def record_key_usage(self, key_index: int) -> None:
        """Record successful API key usage."""
        self._key_usage_count[key_index] = self._key_usage_count.get(key_index, 0) + 1
    
    def record_key_error(self, key_index: int) -> None:
        """Record API key error."""
        self._key_error_count[key_index] = self._key_error_count.get(key_index, 0) + 1
    
    def get_temperature_for_agent(self, agent_type: AgentType) -> float:
        """
        Get optimized temperature for an agent.
        
        Temperature rationale:
        - 0.0: Screener, Skill Counter, DB Chat (deterministic)
        - 0.2: Tech, Code Quality, Hackathon (needs factual accuracy)
        - 0.3: Culture, Extracurricular (analyzing subjective qualities)
        - 0.1: Scraper, Learning Supervisor (mostly factual with slight variation)
        """
        return self.get_config(agent_type).temperature
    
    def get_all_configs(self) -> Dict[AgentType, AgentConfig]:
        """Get all agent configurations."""
        return self.agents
    
    def validate_agent_type(self, agent_type: str) -> bool:
        """Check if agent type is valid."""
        try:
            AgentType(agent_type)
            return True
        except ValueError:
            return False
    
    def get_agent_summary(self) -> Dict[str, str]:
        """Get summary of all agents."""
        return {
            agent.name.value: agent.description
            for agent in self.agents.values()
        }

# Global agent config manager instance
_config_manager = AgentConfigManager()

def get_agent_config_manager() -> AgentConfigManager:
    """Get global agent config manager."""
    return _config_manager

def get_agent_config(agent_type: AgentType) -> AgentConfig:
    """
    Get configuration for an agent.
    
    Args:
        agent_type: The agent type
        
    Returns:
        AgentConfig for the agent
    """
    return _config_manager.get_config(agent_type)

def get_temperature(agent_type: AgentType) -> float:
    """
    Get optimized temperature for an agent.
    """
    return _config_manager.get_temperature_for_agent(agent_type)

def get_api_key_index(agent_type: AgentType) -> int:
    """
    Get API key index for an agent (with rotation support).
    """
    return _config_manager.get_api_key_index(agent_type)

def print_agent_configurations() -> None:
    """
    Print all agent configurations for documentation.
    Useful for debugging and understanding agent setup.
    """
    print("\n" + "="*80)
    print("AGENT CONFIGURATIONS")
    print("="*80)
    
    manager = get_agent_config_manager()
    for agent_type, config in manager.get_all_configs().items():
        print(f"\n{agent_type.value.upper()}")
        print(f"  Model: {config.model}")
        print(f"  Temperature: {config.temperature}")
        print(f"  Max Retries: {config.max_retries}")
        print(f"  Timeout: {config.timeout_seconds}s")
        print(f"  API Key Index: {config.api_key_index}")
        print(f"  Description: {config.description}")
    
    print("\n" + "="*80)
