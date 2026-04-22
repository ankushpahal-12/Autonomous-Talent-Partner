# n8n Agentic AI - sessionId Configuration Guide

## The Error Message

```
Expected to find the session ID in an input field called 'sessionId' 
(this is what the chat trigger node outputs). To use something else, 
change the 'Session ID' parameter
```

This occurs when using n8n's **Chat Trigger Node** with **Agentic AI**.

---

## What is sessionId?

The `sessionId` is a unique identifier that maintains conversation context across multiple messages:
- Enables multi-turn conversations with the AI agent
- Stores conversation history
- Allows resuming conversations
- Tracks user sessions separately

---

## How to Fix It

### Option 1: Use Default sessionId (Recommended)

Add `sessionId` to your webhook payload:

```json
{
  "sessionId": "user-123-session",
  "candidateName": "John Doe",
  "candidateEmail": "john@example.com",
  "message": "Send acceptance email"
}
```

### Option 2: Change the Field Name in n8n

1. Open your n8n workflow
2. Go to **Chat Trigger Node**
3. Click **Parameters**
4. Look for **Session ID** setting
5. Change from `sessionId` to your custom field:
   ```
   customSessionField
   ```

---

## Implementation in Test Script

Update payload to include sessionId:

```python
payload = {
    "sessionId": "candidate-001",  # NEW: Required for chat trigger
    "candidateName": "John Doe",
    "candidateEmail": "john@example.com"
}
```

---

## sessionId Best Practices

### Option A: UUID-based (Recommended)
```python
import uuid

payload = {
    "sessionId": str(uuid.uuid4()),  # Unique ID
    "candidateName": "John Doe",
    "candidateEmail": "john@example.com"
}
```

### Option B: User Email-based
```python
payload = {
    "sessionId": f"session-{candidate_email}",
    "candidateName": "John Doe",
    "candidateEmail": "john@example.com"
}
```

### Option C: Timestamp-based
```python
import time

payload = {
    "sessionId": f"session-{int(time.time())}",
    "candidateName": "John Doe",
    "candidateEmail": "john@example.com"
}
```

### Option D: Database ID-based
```python
payload = {
    "sessionId": candidate_db_id,  # From MongoDB
    "candidateName": "John Doe",
    "candidateEmail": "john@example.com"
}
```

---

## n8n Chat Trigger Configuration

### Setup Steps

1. **Add Chat Trigger Node**
   - Right-click > Add node
   - Search "Chat Trigger"
   - Select it

2. **Configure Parameters**
   - **Webhook Path**: `/candidates-acceptance-chat`
   - **HTTP Method**: POST
   - **Session ID**: `sessionId` (default)

3. **Connect to AI Agent Node**
   - Click output of Chat Trigger
   - Connect to Agentic AI Node
   - The AI node will automatically use the sessionId

---

## Frontend Integration

### React Component with sessionId

```javascript
import { useState } from 'react';
import { v4 as uuidv4 } from 'uuid';

export function CandidateAcceptanceChat({ candidate }) {
  const [sessionId] = useState(uuidv4());
  const [message, setMessage] = useState('');

  const sendMessage = async () => {
    const payload = {
      sessionId,  // NEW: Include session ID
      candidateName: candidate.name,
      candidateEmail: candidate.email,
      message: message,
      position: candidate.position
    };

    const response = await fetch(
      'https://ankushpahal.app.n8n.cloud/webhook-test/webhooks/candidate-acceptance',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      }
    );

    const result = await response.json();
    console.log('AI Response:', result);
  };

  return (
    <div>
      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Ask AI agent..."
      />
      <button onClick={sendMessage}>Send</button>
    </div>
  );
}
```

---

## Backend Integration (FastAPI)

```python
from fastapi import APIRouter
from uuid import uuid4
import aiohttp

router = APIRouter()

@router.post("/chat/acceptance")
async def chat_with_acceptance_agent(
    candidate_name: str,
    candidate_email: str,
    message: str,
    session_id: str = None
):
    """Chat with AI agent about candidate acceptance."""
    
    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid4())
    
    # Prepare n8n webhook payload
    payload = {
        "sessionId": session_id,  # REQUIRED for chat trigger
        "candidateName": candidate_name,
        "candidateEmail": candidate_email,
        "message": message
    }
    
    # Send to n8n
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://ankushpahal.app.n8n.cloud/webhook-test/webhooks/candidate-acceptance",
            json=payload
        ) as response:
            result = await response.json()
            return {
                "session_id": session_id,
                "response": result
            }
```

---

## Conversation Flow with sessionId

```
User Message 1
├─ sessionId: "abc-123"
├─ message: "Send acceptance email"
└─ AI processes and responds

User Message 2 (SAME SESSION)
├─ sessionId: "abc-123"  ← Same ID maintains context
├─ message: "Add interview date April 25"
└─ AI remembers previous context

Result: Conversation maintains state across messages
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `sessionId not found` | Missing in payload | Add `"sessionId": "string"` to payload |
| `Invalid sessionId format` | Wrong data type | Use string, not number or object |
| `Conversation lost` | Different sessionId each time | Reuse same ID for multi-turn |
| `Session not found` | Old/expired session | Regenerate new sessionId |

---

## Example Payloads

### Minimal with sessionId
```json
{
  "sessionId": "session-001",
  "candidateName": "John Doe",
  "candidateEmail": "john@example.com"
}
```

### With Chat Message
```json
{
  "sessionId": "session-001",
  "candidateName": "John Doe",
  "candidateEmail": "john@example.com",
  "message": "Please send acceptance email with interview on April 25 at 2 PM"
}
```

### Maintaining Conversation
```json
{
  "sessionId": "session-001",
  "candidateName": "John Doe",
  "candidateEmail": "john@example.com",
  "message": "Can we change the time to 3 PM instead?"
}
```
← Uses same sessionId for context awareness

---

## Testing with curl

### Without sessionId (Will Fail)
```bash
curl -X POST https://ankushpahal.app.n8n.cloud/webhook-test/webhooks/candidate-acceptance \
  -H "Content-Type: application/json" \
  -d '{
    "candidateName": "John Doe",
    "candidateEmail": "john@example.com"
  }'
```

**Error:** `Expected to find the session ID in an input field called 'sessionId'`

### With sessionId (Will Work)
```bash
curl -X POST https://ankushpahal.app.n8n.cloud/webhook-test/webhooks/candidate-acceptance \
  -H "Content-Type: application/json" \
  -d '{
    "sessionId": "user-session-123",
    "candidateName": "John Doe",
    "candidateEmail": "john@example.com"
  }'
```

**Success:** `200 OK`

---

## Advanced: Session Management

### Store Sessions in Database

```python
from datetime import datetime, timedelta

class SessionManager:
    """Manage AI agent sessions"""
    
    async def create_session(self, candidate_id: str):
        """Create new session for candidate"""
        session_id = str(uuid4())
        
        session = {
            "sessionId": session_id,
            "candidateId": candidate_id,
            "createdAt": datetime.utcnow(),
            "expiresAt": datetime.utcnow() + timedelta(hours=24),
            "messages": [],
            "status": "active"
        }
        
        await db.sessions.insert_one(session)
        return session_id
    
    async def get_session(self, session_id: str):
        """Retrieve session with all messages"""
        return await db.sessions.find_one({"sessionId": session_id})
    
    async def add_message(self, session_id: str, role: str, content: str):
        """Add message to session"""
        await db.sessions.update_one(
            {"sessionId": session_id},
            {
                "$push": {
                    "messages": {
                        "role": role,
                        "content": content,
                        "timestamp": datetime.utcnow()
                    }
                }
            }
        )
    
    async def expire_old_sessions():
        """Clean up expired sessions"""
        await db.sessions.delete_many({
            "expiresAt": {"$lt": datetime.utcnow()}
        })
```

---

## Summary

| Item | Details |
|------|---------|
| **Required** | Yes, add `sessionId` to payload |
| **Format** | String (UUID, email-based, or custom) |
| **Purpose** | Maintain conversation context |
| **Unique per** | User/Candidate/Workflow |
| **Expires** | Configure based on business needs |

---

**Last Updated:** April 2026
