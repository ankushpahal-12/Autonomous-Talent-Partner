import logging
import json
from typing import Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Maps session_id to active WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Stores event history per session for the "event timeline"
        self.event_history: Dict[str, list] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        if session_id not in self.event_history:
            self.event_history[session_id] = []
        logger.info(f"WebSocket connected for session: {session_id}")
        
        # Send timeline history so UI can restore state
        if self.event_history[session_id]:
            await self.send_personal_message(
                json.dumps({"event": "TIMELINE_HISTORY", "data": {"history": self.event_history[session_id]}}), 
                session_id
            )

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session: {session_id}")

    async def send_personal_message(self, message: str, session_id: str):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to {session_id}: {e}")
                self.disconnect(session_id)

    async def send_event(self, session_id: str, event_type: str, data: Dict[str, Any] = None):
        """
        Helper method to send structured JSON events.
        Matches the spec:
        await send_event(session_id, "UPLOAD_STARTED", {"file": "resume.pdf"})
        """
        if data is None:
            data = {}
            
        payload = {
            "event": event_type,
            "data": data,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        }
        
        # Store in history
        if session_id not in self.event_history:
            self.event_history[session_id] = []
        self.event_history[session_id].append(payload)
        
        await self.send_personal_message(json.dumps(payload), session_id)

    async def send_notification(self, session_id: str, level: str, message: str):
        """
        Send specialized UI notification (info, success, warning, error).
        """
        await self.send_event(session_id, "NOTIFICATION", {
            "level": level,
            "message": message
        })

    async def send_progress(self, session_id: str, task_name: str, percentage: int, speed_mbps: float = None):
        """
        Pro Upgrade: Real-time progress percentages and upload speed tracking.
        """
        data = {
            "task": task_name,
            "progress": percentage
        }
        if speed_mbps is not None:
            data["speed_mbps"] = round(speed_mbps, 2)
            
        await self.send_event(session_id, "PROGRESS_UPDATE", data)

# Global manager instance
manager = ConnectionManager()

# Helper aliases to match the requested spec closely
async def send_event(session_id: str, event_type: str, data: dict = None):
    await manager.send_event(session_id, event_type, data)

async def send_progress(session_id: str, task_name: str, percentage: int, speed_mbps: float = None):
    await manager.send_progress(session_id, task_name, percentage, speed_mbps)

async def send_notification(session_id: str, level: str, message: str):
    await manager.send_notification(session_id, level, message)
