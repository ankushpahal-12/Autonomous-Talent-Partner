import asyncio
import httpx
import sys
from typing import Optional, Dict, Any

async def safe_httpx_get(
    url: str, 
    params: Optional[Dict[str, Any]] = None, 
    headers: Optional[Dict[str, Any]] = None, 
    max_retries: int = 4, 
    initial_delay: float = 2.0
) -> Optional[httpx.Response]:
    """
    HTTP GET with Exponential Backoff for 429 (Rate Limit) errors.
    Starts at initial_delay, doubles each time.
    """
    delay = initial_delay
    async with httpx.AsyncClient(timeout=75.0) as client:
        for attempt in range(max_retries):
            try:
                res = await client.get(url, params=params, headers=headers)
                
                # If rate limited, wait and retry
                if res.status_code == 429:
                    sys.stderr.write(f"[API Resilience] Rate Limit (429) hit at {url}. Retrying in {delay}s (Attempt {attempt+1}/{max_retries})...\n")
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                
                # If success, return response
                return res
            
            except httpx.RequestError as e:
                sys.stderr.write(f"[API Resilience] Request error at {url}: {e}. Retrying in {delay}s...\n")
                await asyncio.sleep(delay)
                delay *= 2
        
        # Max retries reached
        sys.stderr.write(f"[API Resilience] CRITICAL: Max retries ({max_retries}) reached for {url}\n")
        return None
