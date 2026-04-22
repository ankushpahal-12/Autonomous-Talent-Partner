"""
Agent caching system for improved performance and reduced API costs.
Provides hash-based deduplication and TTL-based expiry.
"""

import hashlib
import json
import logging
import time
from typing import Any, Callable, Optional, Dict
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

class AgentCache:
    """
    In-memory cache for agent results with TTL support.
    """
    
    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize agent cache.
        
        Args:
            ttl_seconds: Time to live for cached entries in seconds (default: 1 hour)
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    @staticmethod
    def _hash_input(*args, **kwargs) -> str:
        """
        Create deterministic hash of function inputs for cache key.
        Excludes 'request_id' and other transient fields.
        """
        # Serialize arguments
        cache_key = {
            "args": str(args),
            "kwargs": {k: v for k, v in kwargs.items() if k not in ['request_id', '_timestamp']}
        }
        
        key_str = json.dumps(cache_key, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve cached value if not expired.
        """
        async with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            entry_age = time.time() - entry["timestamp"]
            
            if entry_age > self.ttl_seconds:
                # Expired, remove and return None
                del self._cache[key]
                logger.debug(f"Cache entry expired: {key}")
                return None
            
            logger.debug(f"Cache hit: {key} (age: {entry_age:.1f}s)")
            return entry["value"]
    
    async def set(self, key: str, value: Any) -> None:
        """
        Store value in cache with timestamp.
        """
        async with self._lock:
            self._cache[key] = {
                "value": value,
                "timestamp": time.time()
            }
            logger.debug(f"Cached value: {key}")
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            size = len(self._cache)
            self._cache.clear()
            logger.info(f"Cleared {size} cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        """
        return {
            "entries": len(self._cache),
            "ttl_seconds": self.ttl_seconds,
            "keys": list(self._cache.keys())
        }

# Global cache instance
_agent_cache = AgentCache(ttl_seconds=3600)

def cache_agent_result(ttl_seconds: Optional[int] = None):
    """
    Decorator to cache agent function results.
    
    Args:
        ttl_seconds: Override default TTL for this function
    
    Example:
        @cache_agent_result(ttl_seconds=3600)
        async def run_tech_agent(resume_text, job_requirement):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{AgentCache._hash_input(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = await _agent_cache.get(cache_key)
            if cached_value is not None:
                logger.info(f"Returning cached result for {func.__name__}")
                return cached_value
            
            # Call actual function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await _agent_cache.set(cache_key, result)
            
            return result
        
        # Non-async wrapper for sync functions
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            cache_key = f"{func.__name__}:{AgentCache._hash_input(*args, **kwargs)}"
            
            # Try to get from cache (sync version)
            if cache_key in _agent_cache._cache:
                entry = _agent_cache._cache[cache_key]
                entry_age = time.time() - entry["timestamp"]
                if entry_age <= _agent_cache.ttl_seconds:
                    logger.info(f"Returning cached result for {func.__name__}")
                    return entry["value"]
            
            # Call actual function
            result = func(*args, **kwargs)
            
            # Store in cache
            _agent_cache._cache[cache_key] = {
                "value": result,
                "timestamp": time.time()
            }
            
            return result
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def get_cache_stats() -> Dict[str, Any]:
    """
    Get global cache statistics.
    """
    return _agent_cache.get_stats()

async def clear_cache() -> None:
    """
    Clear all cached agent results.
    """
    await _agent_cache.clear()

class BatchCache:
    """
    Specialized cache for batch candidate processing.
    Tracks which candidates have been analyzed.
    """
    
    def __init__(self):
        self._processed: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def add_result(self, candidate_id: str, agent_type: str, result: Any) -> None:
        """
        Add agent result for a candidate.
        """
        async with self._lock:
            if candidate_id not in self._processed:
                self._processed[candidate_id] = {}
            
            self._processed[candidate_id][agent_type] = result
    
    async def get_result(self, candidate_id: str, agent_type: str) -> Optional[Any]:
        """
        Get cached result if available.
        """
        async with self._lock:
            if candidate_id not in self._processed:
                return None
            return self._processed[candidate_id].get(agent_type)
    
    async def is_complete(self, candidate_id: str) -> bool:
        """
        Check if all agents have analyzed this candidate.
        """
        async with self._lock:
            if candidate_id not in self._processed:
                return False
            
            required_agents = {"screener", "tech", "culture"}
            completed = set(self._processed[candidate_id].keys())
            return required_agents.issubset(completed)
    
    async def clear(self) -> None:
        """Clear batch cache."""
        async with self._lock:
            self._processed.clear()

# Global batch cache instance
_batch_cache = BatchCache()

def get_batch_cache() -> BatchCache:
    """Get global batch cache instance."""
    return _batch_cache
