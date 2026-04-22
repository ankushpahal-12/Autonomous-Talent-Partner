# Candidate Acceptance Workflow - AI Agent Setup Guide

## Overview

This n8n workflow sends a candidate acceptance notification with:
- **Input:** Candidate name and email only
- **AI Agent:** Uses Google Gemini to generate personalized email content
- **Output:** Sends email via Gmail and creates Google Calendar event

Workflow is based on the AI Agent architecture pattern for intelligent automation.

## Workflow Architecture

```
Webhook Trigger
    ↓
Parse Webhook Data
    ↓
Generate Email Prompt
    ↓
AI Agent (Google Gemini)
    ↓
    ├─→ Send Email via Gmail
    ├─→ Create Calendar Event
    └─→ Update Backend Database
    ↓
Success Response
```

---

## Prerequisites

### 1. Google Cloud Setup

#### Create Google Cloud Project
1. Go to https://console.cloud.google.com
2. Create new project "Talent Partner - n8n"
3. Enable APIs:
   - Gmail API
   - Google Calendar API
   - Generative AI API

#### Gmail API Setup
1. APIs & Services > Credentials
2. Create OAuth 2.0 Client ID (Desktop application)
3. Download credentials JSON
4. Keep Client ID and Client Secret safe

#### Google Calendar API Setup
1. Use same project as Gmail
2. Create service account (or use OAuth 2.0 credentials)
3. Get credentials for n8n integration

#### Google Generative AI (Gemini) Setup
1. Go to makersuite.google.com
2. Create API key
3. Copy API key for n8n configuration

### 2. n8n Setup

#### Install n8n (if not already installed)
```bash
npm install -g n8n
n8n start
```

Access at: http://localhost:5678

#### Install Necessary Packages
In n8n project, install Google integration packages:
```bash
npm install n8n-nodes-base
npm install @n8n/n8n-nodes-google
```

---

## n8n Configuration

### Step 1: Add Google Credentials

#### Gmail API Credentials
1. Settings > Credentials
2. Click "+ Create new" 
3. Type: "Google Gmail"
4. Name: "Gmail API Credentials"
5. Paste your Gmail OAuth credentials
6. Save

#### Google Calendar API Credentials
1. Settings > Credentials
2. Click "+ Create new"
3. Type: "Google Calendar"
4. Name: "Google Calendar API"
5. Paste your Calendar API credentials
6. Save

#### Google Generative AI Credentials
1. Settings > Credentials
2. Click "+ Create new"
3. Type: "Google Generative AI"
4. Name: "Gemini API Key"
5. Paste your API key
6. Save

### Step 2: Import Workflow

1. Open n8n dashboard
2. New > Import from JSON
3. Paste entire content of [candidate_acceptance_ai_agent.json](candidate_acceptance_ai_agent.json)
4. Click Import

### Step 3: Configure Workflow Nodes

#### Webhook Node
- Already configured for POST /candidate-acceptance
- Test URL will appear after activation

#### Parse Webhook Data Node
- Validates required fields: candidateName, candidateEmail
- Optional fields: position, company, interviewDate, interviewTime, timezone, hrEmail
- Provides defaults if not specified

#### Generate Email Prompt Node
- Creates structured prompt for AI
- Includes: candidate name, position, company, interview details
- Customized for professional recruiter tone

#### AI Agent - Email Generation Node
- Model: gemini-pro
- Temperature: 0.7 (balanced creativity/consistency)
- Generates personalized email content
- Credentials: Gemini API Key

#### Send Email via Gmail Node
- From: noreply@company.com (update with your email)
- To: candidate email from webhook
- Subject: Congratulations! Interview Confirmed
- HTML template with professional formatting
- Credentials: Gmail API

#### Create Calendar Event Node
- Calendar: Primary
- Title: Interview: [Candidate Name] - [Position]
- Description: Position details and instructions
- Attendees: Candidate + HR email
- Duration: 60 minutes
- Timezone: From webhook data
- Credentials: Google Calendar API

#### Update Backend Database Node
- POST to http://localhost:8000/api/v1/candidates/acceptance-notification
- Sends: candidate name, email, position, interview details, status
- Logs the acceptance notification in backend

---

## Webhook Input Format

Send POST request to your n8n webhook URL with:

### Minimal Request (Only Required Fields)
```json
{
  "candidateName": "John Doe",
  "candidateEmail": "john.doe@example.com"
}
```

### Complete Request (With All Fields)
```json
{
  "candidateName": "John Doe",
  "candidateEmail": "john.doe@example.com",
  "position": "Senior Backend Developer",
  "company": "Tech Company Inc",
  "interviewDate": "2024-04-20",
  "interviewTime": "10:00 AM",
  "timezone": "EST",
  "hrEmail": "hr@company.com"
}
```

### Field Descriptions

| Field | Required | Type | Default | Description |
|-------|----------|------|---------|-------------|
| candidateName | Yes | String | - | Candidate's full name |
| candidateEmail | Yes | String | - | Candidate's email address |
| position | No | String | "Software Engineer" | Job position title |
| company | No | String | "Our Company" | Company name |
| interviewDate | No | Date (YYYY-MM-DD) | Today | Interview date |
| interviewTime | No | Time | "10:00 AM" | Interview start time |
| timezone | No | String | "EST" | Timezone (EST, PST, UTC, etc.) |
| hrEmail | No | String | "hr@company.com" | HR contact email |

---

## Testing the Workflow

### Test 1: From n8n UI
1. Open the workflow
2. Click "Test Workflow" button
3. Manually enter test data in Webhook node
4. Check execution history for success

### Test 2: From Backend
In your FastAPI backend, trigger the workflow:

```python
import aiohttp
import asyncio

async def send_acceptance_notification(candidate_name: str, candidate_email: str):
    """Trigger n8n candidate acceptance workflow."""
    
    webhook_url = "http://localhost:5678/webhook/candidate-acceptance"
    
    payload = {
        "candidateName": candidate_name,
        "candidateEmail": candidate_email,
        "position": "Senior Backend Developer",
        "company": "Tech Company Inc",
        "interviewDate": "2024-04-25",
        "interviewTime": "2:00 PM",
        "timezone": "EST",
        "hrEmail": "hr@company.com"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=payload) as response:
            result = await response.json()
            return result
```

### Test 3: Via cURL
```bash
curl -X POST http://localhost:5678/webhook/candidate-acceptance \
  -H "Content-Type: application/json" \
  -d '{
    "candidateName": "Jane Smith",
    "candidateEmail": "jane.smith@example.com",
    "position": "Frontend Developer",
    "company": "Tech Startup",
    "interviewDate": "2024-04-22",
    "interviewTime": "3:00 PM",
    "timezone": "PST"
  }'
```

---

## Expected Output

### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Acceptance notification sent",
  "email_subject": "Congratulations! Interview Confirmed - Senior Backend Developer",
  "calendar_event_created": true,
  "database_updated": true
}
```

### Candidate Receives
1. **Email with:**
   - Congratulations message
   - Position and company details
   - Interview date, time, timezone
   - Professional styling and branding

2. **Calendar Event with:**
   - Interview title and details
   - HR and candidate as attendees
   - Timezone properly configured
   - Duration set to 60 minutes

3. **Backend Database Update:**
   - Acceptance notification logged
   - Status marked as "acceptance_sent"
   - Timestamp recorded

---

## Customization

### Change Email Template

In "Send Email via Gmail" node, modify the htmlMessage parameter:

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    /* Your custom CSS */
  </style>
</head>
<body>
  <!-- Your custom HTML -->
  <p>Dear {{ $node["Parse Webhook Data"].json.candidateName }},</p>
  <!-- Add your content -->
</body>
</html>
```

### Change AI Prompt

In "Generate Email Prompt" node, modify the prompt variable:

```javascript
const prompt = `
Your custom prompt here...
Include: ${data.candidateName}, ${data.position}, ${data.interviewDate}
`;
```

### Change Calendar Details

In "Create Calendar Event" node, modify:
- Title format
- Description content
- Duration
- Attendees list

### Change Email Sender

Update the "fromEmail" parameter in Gmail node to your company email.

---

## Troubleshooting

### Error: "Gmail API credentials not found"
**Solution:**
1. Check Settings > Credentials
2. Verify Gmail API credentials are saved
3. Check Gmail API is enabled in Google Cloud Console
4. Refresh n8n and try again

### Error: "Google Calendar API not configured"
**Solution:**
1. Ensure Calendar API is enabled in Google Cloud
2. Add Google Calendar credentials in n8n Settings
3. Test Calendar API access in Google Cloud Console

### Error: "Authentication failed for Gemini API"
**Solution:**
1. Verify API key is correct
2. Check API key has access to Generative AI API
3. Ensure quota is not exceeded
4. Regenerate API key if necessary

### Emails not sending
**Solution:**
1. Check Gmail sender email is correct
2. Verify Gmail API has permission to send emails
3. Check Gmail "Less secure app access" is enabled (if applicable)
4. Test Gmail API separately in Google Cloud Console

### Calendar events not creating
**Solution:**
1. Verify Calendar API credentials are correct
2. Check primary calendar is accessible
3. Ensure timezone format is valid
4. Check calendar has available space for events

### Workflow not executing
**Solution:**
1. Ensure workflow is marked as "Active" (toggle in top right)
2. Check workflow execution logs (click execution history)
3. Verify all nodes have required connection
4. Check node conditions and filters

---

## Integration with Backend

### Add to FastAPI Backend

In `backend/services/n8n_trigger.py`:

```python
import aiohttp
from typing import Optional

class N8nService:
    """Service to trigger n8n workflows."""
    
    def __init__(self, n8n_base_url: str = "http://localhost:5678"):
        self.n8n_base_url = n8n_base_url
        self.webhook_paths = {
            "acceptance": "/webhook/candidate-acceptance",
            "rejection": "/webhook/candidate-rejection",
            "interview": "/webhook/interview-scheduler"
        }
    
    async def send_acceptance(
        self,
        candidate_name: str,
        candidate_email: str,
        position: str = "Software Engineer",
        company: str = "Our Company",
        interview_date: Optional[str] = None,
        interview_time: str = "10:00 AM",
        timezone: str = "EST",
        hr_email: str = "hr@company.com"
    ) -> dict:
        """Trigger candidate acceptance workflow."""
        
        webhook_url = f"{self.n8n_base_url}{self.webhook_paths['acceptance']}"
        
        payload = {
            "candidateName": candidate_name,
            "candidateEmail": candidate_email,
            "position": position,
            "company": company,
            "interviewDate": interview_date,
            "interviewTime": interview_time,
            "timezone": timezone,
            "hrEmail": hr_email
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, timeout=30) as response:
                    return await response.json()
        except aiohttp.ClientError as e:
            raise Exception(f"Failed to trigger acceptance workflow: {str(e)}")
```

### Add to API Endpoint

In `backend/app/api/candidates.py`:

```python
from fastapi import APIRouter, HTTPException
from services.n8n_trigger import N8nService

router = APIRouter()
n8n_service = N8nService()

@router.post("/{candidate_id}/send-acceptance")
async def send_candidate_acceptance(
    candidate_id: str,
    candidate: dict  # From database lookup
):
    """Send acceptance notification to candidate."""
    
    try:
        result = await n8n_service.send_acceptance(
            candidate_name=candidate["name"],
            candidate_email=candidate["email"],
            position=candidate.get("position_applied", "Software Engineer"),
            interview_date=candidate.get("interview_date")
        )
        
        return {
            "status": "success",
            "message": "Acceptance notification sent",
            "n8n_response": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Security Considerations

1. **Credentials:** All Google API credentials stored in n8n Settings, not in workflow
2. **Email Validation:** Backend validates email format before sending
3. **Rate Limiting:** Implement rate limiting on webhook endpoint
4. **Logging:** All workflow executions logged for audit trail
5. **SSL/TLS:** Use HTTPS for webhook URLs in production
6. **API Keys:** Rotate Google API keys periodically
7. **Access Control:** Restrict workflow editing to authorized users

---

## Performance & Monitoring

### Expected Execution Time
- Average: 5-10 seconds
- Gmail sending: 2-3 seconds
- Calendar event creation: 2-3 seconds
- AI prompt generation: 1-2 seconds
- Database update: 1-2 seconds

### Monitor Workflow
1. n8n > Executions > View logs
2. Check for errors or warnings
3. Monitor API quota usage in Google Cloud Console
4. Set up alerts for workflow failures

### Scale Considerations
- Current setup handles ~100 candidates/hour
- For higher volume: Use n8n Cloud or increase n8n resources
- Implement queue system for bulk acceptance sends
- Add retry logic for transient failures

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.0 | Apr 2026 | AI Agent workflow with Gemini integration |
| 1.1.0 | Apr 2026 | Original workflow with hardcoded templates |

---

Last Updated: April 2026
