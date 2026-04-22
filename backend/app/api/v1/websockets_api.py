import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, Any
import asyncio

from ...core.websockets import manager, send_event, send_progress, send_notification

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    try:
        await manager.connect(websocket, session_id)
        logger.info(f"WebSocket connected for session: {session_id}")
        
        try:
            while True:
                try:
                    # Keep connection open, listen for client messages if needed
                    # For now, it's mostly a one-way channel to push UI notifications
                    # Use a timeout to check for disconnection regularly
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                    logger.debug(f"Received message from ws {session_id}: {data}")
                except asyncio.TimeoutError:
                    # Connection is still active, just no message from client
                    # Send a heartbeat ping to keep connection alive
                    try:
                        await websocket.send_json({"event": "PING", "data": {}})
                    except Exception as e:
                        logger.warning(f"Failed to send ping to {session_id}: {e}")
                        break
                except Exception as e:
                    logger.error(f"Error receiving message from {session_id}: {e}")
                    break
        except WebSocketDisconnect:
            logger.info(f"Client {session_id} disconnected")
        except Exception as e:
            logger.error(f"WebSocket error for {session_id}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"WebSocket connection failed for {session_id}: {e}", exc_info=True)
    finally:
        manager.disconnect(session_id)
        logger.info(f"WebSocket cleaned up for session: {session_id}")

class TestEventRequest(BaseModel):
    session_id: str
    event_type: str
    data: Dict[str, Any]

@router.post("/test-ws")
async def test_websocket_event(request: TestEventRequest):
    """
    Test endpoint to simulate triggering WebSocket events.
    Ex: {"session_id": "123", "event_type": "UPLOAD_STARTED", "data": {"file": "resume.pdf"}}
    """
    await send_event(request.session_id, request.event_type, request.data)
    return {"message": "Event dispatched", "payload": request.model_dump()}

class TestProgressRequest(BaseModel):
    session_id: str
    task_name: str
    percentage: int
    speed_mbps: float = None

@router.post("/test-ws-progress")
async def test_websocket_progress(request: TestProgressRequest):
    """Test sending explicit progress updates to a session."""
    await send_progress(request.session_id, request.task_name, request.percentage, request.speed_mbps)
    return {"message": "Progress update sent"}

class TestNotificationRequest(BaseModel):
    session_id: str
    level: str  # e.g. "info", "success", "error", "warning"
    message: str

@router.post("/test-ws-notification")
async def test_websocket_notification(request: TestNotificationRequest):
    """Test sending explicit UI notifications."""
    await send_notification(request.session_id, request.level, request.message)
    return {"message": f"Notification '{request.level}' sent"}
