import httpx
import os
from app.core.config import settings

async def trigger_n8n_selected(candidate_name: str, candidate_email: str):
    """
    Triggers the n8n webhook for a selected candidate to send an interview link.
    """
    url = settings.N8N_WEBHOOK_URL_SELECTED
    if not url:
        print("n8n 'Selected' webhook URL not configured.")
        return
        
    payload = {
        "event": "candidate_selected",
        "name": candidate_name,
        "email": candidate_email,
        "project": settings.PROJECT_NAME
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            print(f"Successfully triggered n8n Selected webhook for {candidate_name}")
    except Exception as e:
        print(f"Failed to trigger n8n Selected webhook: {e}")

async def trigger_n8n_rejected(candidate_name: str, candidate_email: str, reason: str = ""):
    """
    Triggers the n8n webhook for a rejected candidate to send feedback.
    """
    url = settings.N8N_WEBHOOK_URL_REJECTED
    if not url:
        print("n8n 'Rejected' webhook URL not configured.")
        return
        
    payload = {
        "event": "candidate_rejected",
        "name": candidate_name,
        "email": candidate_email,
        "reason": reason,
        "project": settings.PROJECT_NAME
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            print(f"Successfully triggered n8n Rejected webhook for {candidate_name}")
    except Exception as e:
        print(f"Failed to trigger n8n Rejected webhook: {e}")
