# API Reference Documentation

Quick reference for all n8n-related API endpoints.

## Base URL
```
http://localhost:8000/api/v1/candidates
```

---

## Endpoints

### 1. Schedule Interview (Acceptance)

**Endpoint:** `POST /{candidate_id}/interview-scheduled`

**Purpose:** Record that an accepted candidate has been scheduled for an interview.

**Request Parameters:**
- `candidate_id` (path): Unique candidate ID

**Request Body:**
```json
{
  "interview_date": "2026-04-25",
  "interview_time": "2:00 PM",
  "interview_duration": 60,
  "timezone": "EST",
  "meeting_link": "https://meet.google.com/abc-defg-hij",
  "interviewer_name": "Jane Smith",
  "hr_email": "hr@company.com"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Interview scheduled successfully",
  "data": {
    "candidate_id": "john_doe_123",
    "status": "interview_scheduled",
    "interview_date": "2026-04-25",
    "interview_time": "2:00 PM",
    "meeting_link": "https://meet.google.com/abc-defg-hij"
  },
  "request_id": "req_123456"
}
```

**Error Responses:**
- `404`: Candidate not found
- `500`: Failed to schedule interview
- `400`: Invalid request format

**Used By:** n8n Acceptance Workflow (final HTTP request node)

---

### 2. Record Rejection

**Endpoint:** `POST /{candidate_id}/rejection`

**Purpose:** Record that a candidate has been rejected with feedback.

**Request Parameters:**
- `candidate_id` (path): Unique candidate ID

**Request Body:**
```json
{
  "rejection_reason": "Did not meet technical requirements",
  "feedback_summary": "Strong communication skills but lacking required ML expertise",
  "hr_email": "hr@company.com",
  "allow_reapply": true,
  "reapply_after_months": 6
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Rejection recorded successfully",
  "data": {
    "candidate_id": "jane_doe_456",
    "status": "rejected",
    "rejection_reason": "Did not meet technical requirements",
    "allow_reapply": true,
    "reapply_after_months": 6
  },
  "request_id": "req_789012"
}
```

**Error Responses:**
- `404`: Candidate not found
- `500`: Failed to record rejection
- `400`: Invalid request format

**Used By:** n8n Rejection Workflow (final HTTP request node)

---

## Field Definitions

### Interview Schedule Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| interview_date | string | Yes | ISO 8601 date format (YYYY-MM-DD) |
| interview_time | string | Yes | Time string (HH:MM or with AM/PM) |
| interview_duration | integer | No | Duration in minutes (default: 60) |
| timezone | string | No | Candidate's timezone (default: EST) |
| meeting_link | string | Yes | URL to video conference (Google Meet, Zoom, etc.) |
| interviewer_name | string | Yes | Name of hiring manager/interviewer |
| hr_email | string | Yes | HR team email for notification |

### Rejection Request

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| rejection_reason | string | Yes | Brief reason (e.g., "Skill mismatch") |
| feedback_summary | string | Yes | Detailed feedback for candidate |
| hr_email | string | Yes | HR team email for notification |
| allow_reapply | boolean | No | Can candidate reapply? (default: true) |
| reapply_after_months | integer | No | Months before eligible (default: 6) |

---

## Database Schema

### Candidate Document Updates

#### After Interview Scheduling
```javascript
{
  _id: ObjectId,
  status: "interview_scheduled",
  interview_date: "2026-04-25",
  interview_time: "2:00 PM",
  interview_duration: 60,
  timezone: "EST",
  meeting_link: "https://meet.google.com/...",
  interviewer_name: "Jane Smith",
  notification_sent: true,
  notification_timestamp: "2026-04-01T14:30:00.000Z",
  status_history: [
    {
      status: "interview_scheduled",
      timestamp: "2026-04-01T14:30:00.000Z",
      metadata: {
        interview_date: "2026-04-25",
        interviewer: "Jane Smith"
      }
    }
  ],
  // ... other candidate fields
}
```

#### After Rejection
```javascript
{
  _id: ObjectId,
  status: "rejected",
  rejection_reason: "Did not meet technical requirements",
  feedback_summary: "Strong communication but lacking ML expertise",
  allow_reapply: true,
  reapply_after_months: 6,
  reapply_eligible_date: "2026-10-01T14:30:00.000Z",
  notification_sent: true,
  notification_timestamp: "2026-04-01T14:30:00.000Z",
  status_history: [
    {
      status: "rejected",
      timestamp: "2026-04-01T14:30:00.000Z",
      metadata: {
        reason: "Did not meet technical requirements",
        allow_reapply: true
      }
    }
  ],
  // ... other candidate fields
}
```

---

## Activity Logging

Both endpoints automatically log activities via the `log_activity` service:

### Interview Scheduling Log
```
Component: HR
Message: "Interview scheduled: [Candidate Name]"
Metadata: {
  candidate_id: "...",
  interview_date: "2026-04-25",
  interview_time: "2:00 PM",
  interviewer: "Jane Smith",
  meeting_link: "https://meet.google.com/..."
}
```

### Rejection Log
```
Component: HR
Message: "Candidate rejected: [Candidate Name]"
Metadata: {
  candidate_id: "...",
  rejection_reason: "Did not meet technical requirements",
  allow_reapply: true,
  reapply_after_months: 6
}
```

---

## Response Codes

| Code | Status | Meaning |
|------|--------|---------|
| 200 | Success | Operation completed successfully |
| 400 | Bad Request | Invalid request format or missing required fields |
| 404 | Not Found | Candidate does not exist |
| 500 | Server Error | Database or processing error |

---

## Example Usage

### cURL

```bash
# Schedule Interview
curl -X POST http://localhost:8000/api/v1/candidates/john_doe_123/interview-scheduled \
  -H 'Content-Type: application/json' \
  -d '{
    "interview_date": "2026-04-25",
    "interview_time": "2:00 PM",
    "interview_duration": 60,
    "timezone": "EST",
    "meeting_link": "https://meet.google.com/abc-defg-hij",
    "interviewer_name": "Jane Smith",
    "hr_email": "hr@company.com"
  }'

# Record Rejection
curl -X POST http://localhost:8000/api/v1/candidates/jane_doe_456/rejection \
  -H 'Content-Type: application/json' \
  -d '{
    "rejection_reason": "Did not meet technical requirements",
    "feedback_summary": "Strong communication but lacking Python expertise",
    "hr_email": "hr@company.com",
    "allow_reapply": true,
    "reapply_after_months": 6
  }'
```

### JavaScript/Fetch

```javascript
// Schedule Interview
const scheduleInterview = async (candidateId, details) => {
  const response = await fetch(
    `http://localhost:8000/api/v1/candidates/${candidateId}/interview-scheduled`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(details)
    }
  );
  return response.json();
};

// Record Rejection
const rejectCandidate = async (candidateId, details) => {
  const response = await fetch(
    `http://localhost:8000/api/v1/candidates/${candidateId}/rejection`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(details)
    }
  );
  return response.json();
};
```

### Python/Requests

```python
import requests

# Schedule Interview
def schedule_interview(candidate_id, details):
    response = requests.post(
        f"http://localhost:8000/api/v1/candidates/{candidate_id}/interview-scheduled",
        json=details
    )
    return response.json()

# Record Rejection
def reject_candidate(candidate_id, details):
    response = requests.post(
        f"http://localhost:8000/api/v1/candidates/{candidate_id}/rejection",
        json=details
    )
    return response.json()
```

---

## Integration Points

### n8n Workflows
- **Acceptance Workflow**: Calls interview-scheduled endpoint after sending emails
- **Rejection Workflow**: Calls rejection endpoint after sending emails

### Frontend Application
- Decision buttons in EnhancedCandidateDetail.jsx
- Interview scheduling modal triggers acceptance workflow
- Rejection form triggers rejection workflow

### Database
- MongoDB stores all scheduling and rejection data
- Status history tracks all state changes
- Activity logging records all HR actions

---

## Rate Limiting

Currently, no rate limiting is enforced. For production, consider adding:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/{candidate_id}/interview-scheduled")
@limiter.limit("100/minute")
async def schedule_interview(...):
    ...
```

---

## Authentication

Currently, endpoints use request context authentication. For production, implement:

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredential

security = HTTPBearer()

@router.post("/{candidate_id}/interview-scheduled")
async def schedule_interview(
    ...,
    auth: HTTPAuthCredential = Depends(security)
):
    # Validate JWT token
    ...
```

---

## Versioning

Current API version: **v1**

Future versions may include:
- Bulk scheduling operations
- Webhook callbacks to external systems
- Advanced filtering and analytics
- Interview feedback recording
- Candidate follow-up scheduling

---

## Support & Troubleshooting

See [N8N_INTEGRATION_GUIDE.md](./N8N_INTEGRATION_GUIDE.md) for:
- Detailed configuration instructions
- Workflow setup and testing
- Frontend integration examples
- Troubleshooting common issues
- Production deployment guide
