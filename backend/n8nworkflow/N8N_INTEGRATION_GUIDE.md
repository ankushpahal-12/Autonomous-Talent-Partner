# n8n Workflow Integration Guide

Complete guide for integrating n8n automation workflows with the recruitment system.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Workflow Structure](#workflow-structure)
3. [Frontend Integration](#frontend-integration)
4. [Backend API Setup](#backend-api-setup)
5. [n8n Configuration](#n8n-configuration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)
8. [Production Deployment](#production-deployment)

---

## Quick Start

### Prerequisites
- n8n instance running (local or cloud)
- Backend API server running on port 8000
- Frontend React application

### Step 1: Import Workflows into n8n
1. Open n8n dashboard
2. Click "Import" → "From file"
3. Upload one of the workflows:
   - `candidate_acceptance_workflow.json` (v1.1.0 - Basic template-based)
   - `candidate_acceptance_ai_agent.json` (v2.0.0 - AI Agent with Gemini)
   - `candidate_rejection_workflow.json`
4. Save workflows

### Step 2: Configure Credentials (Google Services)

For AI Agent workflows (v2.0.0+):

1. **Google Generative AI (Gemini)**
   - Go to makersuite.google.com
   - Create API key
   - In n8n: Settings > Credentials > Google Generative AI
   - Add your API key

2. **Gmail API**
   - Google Cloud Console > Credentials
   - Create OAuth 2.0 Client ID
   - In n8n: Settings > Credentials > Gmail
   - Authenticate and save

3. **Google Calendar API**
   - Google Cloud Console > Enable Google Calendar API
   - In n8n: Settings > Credentials > Google Calendar
   - Authenticate and save

### Step 3: Configure Email Provider
In each workflow, configure the Email node:
- **Provider**: Gmail, SendGrid, or SMTP
- **Authentication**: Configure with your email service credentials
- **From Address**: Your HR team email (hr@company.com)

### Step 3: Test Webhooks
Use the webhook testing guide in `WEBHOOK_GUIDE.json` to test workflows with sample payloads.

### Step 4: Connect Frontend
Update your frontend decision buttons to call the workflows.

---

## Workflow Structure

### Workflow Versions

#### v1.1.0: Basic Candidate Acceptance (Original)
- Template-based email with meeting link generation
- Simple webhook trigger with data parsing
- No AI involvement
- File: `candidate_acceptance_workflow.json`

#### v2.0.0: AI Agent Candidate Acceptance (New)
- AI-powered email generation using Google Gemini
- Sends emails via Gmail API
- Creates Google Calendar events automatically
- Personalized content at scale
- File: `candidate_acceptance_ai_agent.json`
- **Setup Guide:** [CANDIDATE_ACCEPTANCE_AI_GUIDE.md](CANDIDATE_ACCEPTANCE_AI_GUIDE.md)

---

### Candidate Acceptance Workflow (v2.0.0 - AI Agent)

```
┌────────────────────────────────────────────────────────┐
│ Webhook Trigger (POST)                                 │
│ Input: candidateName, candidateEmail                   │
│ Optional: position, company, interview date/time       │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│ Parse Webhook Data                                    │
│ - Validate required fields                           │
│ - Set defaults for optional fields                   │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│ Generate Email Prompt                                │
│ - Create structured prompt for AI                    │
│ - Include: name, position, company, interview info  │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────▼─────────────────────────────────────┐
│ AI Agent (Google Gemini)                             │
│ - Generate personalized email content                │
│ - Professional tone, congratulations message         │
│ - Interview details and instructions                 │
└────────────────┬─────────────────────────────────────┘
                 │
         ┌───────┴───────────────┐
         │                       │
    ┌────▼──────┐         ┌──────▼──────┐
    │Send Email  │         │Create       │
    │via Gmail   │         │Calendar     │
    │            │         │Event        │
    └────┬──────┘         └──────┬──────┘
         │                       │
         └───────┬───────────────┘
                 │
    ┌────────────▼──────────────────┐
    │Update Backend Database        │
    │POST /candidates/acceptance-   │
    │     notification              │
    └────────────┬──────────────────┘
                 │
    ┌────────────▼──────────────────┐
    │Success Response (200 OK)      │
    └───────────────────────────────┘
```

**Advantages of AI Agent Workflow (v2.0.0):**
- Generates unique, personalized emails for each candidate
- No template editing needed
- Professional tone automatically
- Easily customizable via prompt engineering
- Scalable without maintenance

**Minimum Input Required:**
```json
{
  "candidateName": "John Doe",
  "candidateEmail": "john@example.com"
}
```

---

### Candidate Acceptance Workflow (v1.1.0 - Original)

```
┌─────────────────────────────────────────────────────────────┐
│ Webhook Trigger                                             │
│ Path: /webhooks/candidate-acceptance                        │
│ Method: POST                                                │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│ Parse Data (JavaScript)                                     │
│ - Extract interview details from payload                    │
│ - Format dates and times                                    │
│ - Prepare email variables                                  │
└────────────────┬────────────────────────────────────────────┘
                 │
         ┌───────┴───────┐
         │               │
    ┌────▼────┐    ┌─────▼──────┐
    │ Email    │    │ Email      │
    │ Candidate│    │ HR Team    │
    └────┬────┘    └─────┬──────┘
         │               │
         └───────┬───────┘
                 │
    ┌────────────▼────────────────┐
    │ HTTP Request (API Update)   │
    │ POST /candidates/{id}/      │
    │      interview-scheduled    │
    └────────────┬────────────────┘
                 │
    ┌────────────▼────────────────┐
    │ Log Activity                │
    │ Write to log file           │
    └────────────────────────────┘
```

### Candidate Rejection Workflow

```
┌──────────────────────────────────────────────────────────┐
│ Webhook Trigger                                          │
│ Path: /webhooks/candidate-rejection                      │
│ Method: POST                                             │
└────────────────┬──────────────────────────────────────────┘
                 │
┌────────────────▼──────────────────────────────────────────┐
│ Parse Data (JavaScript)                                  │
│ - Extract rejection details                             │
│ - Format feedback                                       │
│ - Calculate reapply eligibility                        │
└────────────────┬──────────────────────────────────────────┘
                 │
         ┌───────┴───────┐
         │               │
    ┌────▼────┐    ┌─────▼──────┐
    │ Email    │    │ Email      │
    │ Candidate│    │ HR Team    │
    └────┬────┘    └─────┬──────┘
         │               │
         └───────┬───────┘
                 │
    ┌────────────▼────────────────┐
    │ HTTP Request (API Update)   │
    │ POST /candidates/{id}/      │
    │      rejection              │
    └────────────┬────────────────┘
                 │
    ┌────────────▼────────────────┐
    │ Log Activity                │
    │ Write to log file           │
    └────────────────────────────┘
```

---

## Frontend Integration

### Update Decision Buttons in EnhancedCandidateDetail.jsx

```javascript
// In handleDecision function, trigger n8n webhook instead of direct API call

const triggerAcceptanceWorkflow = async (interviewDetails) => {
  try {
    const payload = {
      candidateId: candidate._id,
      candidateName: candidate.parsed_data.name,
      candidateEmail: candidate.parsed_data.email,
      position: candidate.position || "Open Position",
      interviewDate: interviewDetails.date,
      interviewTime: interviewDetails.time,
      interviewDuration: interviewDetails.duration || 60,
      timezone: interviewDetails.timezone || "EST",
      meetingLink: interviewDetails.meetingLink,
      interviewerName: interviewDetails.interviewerName,
      hrEmail: "hr@company.com" // Configure your HR email
    };

    const response = await fetch(
      "http://localhost:5678/webhook/candidate-acceptance",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }
    );

    if (response.ok) {
      console.log("Acceptance workflow triggered");
      // Show success message to user
    }
  } catch (error) {
    console.error("Failed to trigger workflow:", error);
  }
};

const triggerRejectionWorkflow = async (rejectionDetails) => {
  try {
    const payload = {
      candidateId: candidate._id,
      candidateName: candidate.parsed_data.name,
      candidateEmail: candidate.parsed_data.email,
      position: candidate.position || "Open Position",
      rejectionReason: rejectionDetails.reason,
      feedbackSummary: rejectionDetails.feedback,
      hrEmail: "hr@company.com",
      allowReapply: rejectionDetails.allowReapply || true,
      reapplyAfterMonths: rejectionDetails.reapplyAfterMonths || 6
    };

    const response = await fetch(
      "http://localhost:5678/webhook/candidate-rejection",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }
    );

    if (response.ok) {
      console.log("Rejection workflow triggered");
      // Show success message to user
    }
  } catch (error) {
    console.error("Failed to trigger workflow:", error);
  }
};
```

### Add Interview Scheduling Modal

```javascript
const [showInterviewModal, setShowInterviewModal] = useState(false);
const [interviewDetails, setInterviewDetails] = useState({
  date: "",
  time: "",
  duration: 60,
  timezone: "EST",
  meetingLink: "",
  interviewerName: ""
});

const handleAcceptance = async () => {
  if (!interviewDetails.date || !interviewDetails.time || !interviewDetails.meetingLink) {
    alert("Please fill in all interview details");
    return;
  }
  
  await triggerAcceptanceWorkflow(interviewDetails);
  setShowInterviewModal(false);
  // Refresh candidate data
};

const handleRejection = async () => {
  // Show rejection form
  const reason = prompt("Enter rejection reason:");
  const feedback = prompt("Enter feedback summary:");
  
  if (reason && feedback) {
    await triggerRejectionWorkflow({
      reason,
      feedback,
      allowReapply: true
    });
  }
};
```

---

## Backend API Setup

### Verify Endpoints are Accessible

The following endpoints were added to `backend/app/api/v1/candidates.py`:

#### 1. Interview Scheduling Endpoint
```
POST /api/v1/candidates/{candidate_id}/interview-scheduled

Request Body:
{
  "interview_date": "2026-04-20",
  "interview_time": "2:00 PM",
  "interview_duration": 60,
  "timezone": "EST",
  "meeting_link": "https://meet.google.com/...",
  "interviewer_name": "Jane Smith",
  "hr_email": "hr@company.com"
}

Response:
{
  "status": "success",
  "message": "Interview scheduled successfully",
  "data": {
    "candidate_id": "...",
    "status": "interview_scheduled",
    "interview_date": "2026-04-20",
    "interview_time": "2:00 PM",
    "meeting_link": "https://meet.google.com/..."
  }
}
```

#### 2. Rejection Endpoint
```
POST /api/v1/candidates/{candidate_id}/rejection

Request Body:
{
  "rejection_reason": "Did not meet technical requirements",
  "feedback_summary": "Strong communication but lacking technical depth",
  "hr_email": "hr@company.com",
  "allow_reapply": true,
  "reapply_after_months": 6
}

Response:
{
  "status": "success",
  "message": "Rejection recorded successfully",
  "data": {
    "candidate_id": "...",
    "status": "rejected",
    "rejection_reason": "...",
    "allow_reapply": true,
    "reapply_after_months": 6
  }
}
```

### Database Schema Updates

The following fields are automatically added to candidate documents:

**For Interview Scheduled:**
```javascript
{
  status: "interview_scheduled",
  interview_date: "YYYY-MM-DD",
  interview_time: "HH:MM",
  interview_duration: 60,
  timezone: "EST",
  meeting_link: "url",
  interviewer_name: "string",
  notification_sent: true,
  notification_timestamp: "ISO8601",
  status_history: [
    {
      status: "interview_scheduled",
      timestamp: "ISO8601",
      metadata: { interview_date, interviewer }
    }
  ]
}
```

**For Rejection:**
```javascript
{
  status: "rejected",
  rejection_reason: "string",
  feedback_summary: "string",
  allow_reapply: boolean,
  reapply_after_months: number,
  reapply_eligible_date: "ISO8601",
  notification_sent: true,
  notification_timestamp: "ISO8601",
  status_history: [
    {
      status: "rejected",
      timestamp: "ISO8601",
      metadata: { reason, allow_reapply }
    }
  ]
}
```

---

## n8n Configuration

### Step 1: Email Service Setup

#### Gmail Configuration
1. In n8n, go to Settings → Credentials
2. Create new Gmail credential
3. Authenticate with your Gmail account
4. Enable "Less secure app access" in Google Account settings

#### SendGrid Configuration
1. Get your SendGrid API key
2. Create new SendGrid credential in n8n
3. Paste API key
4. Set from address to your HR email

#### SMTP Configuration
1. Create new SMTP credential
2. Configure with your email server details:
   - Host: smtp.gmail.com or your provider
   - Port: 587 (TLS) or 465 (SSL)
   - Username: your email
   - Password: app-specific password

### Step 2: Workflow Variables

Set these as environment variables or workflow variables:

```
N8N_BASE_URL=http://localhost:8000
N8N_WEBHOOK_AUTH_TOKEN=your_secure_token
HR_EMAIL=hr@company.com
EMAIL_FROM=noreply@company.com
COMPANY_NAME=Your Company Name
SUPPORT_EMAIL=support@company.com
```

### Step 3: JavaScript parseData Node

The parseData nodes in both workflows use this structure:

```javascript
// For Acceptance Workflow
return {
  candidateId: $json.candidateId,
  candidateName: $json.candidateName,
  candidateEmail: $json.candidateEmail,
  position: $json.position,
  interviewDate: $json.interviewDate,
  interviewTime: $json.interviewTime,
  interviewDuration: $json.interviewDuration || 60,
  timezone: $json.timezone || 'EST',
  meetingLink: $json.meetingLink,
  interviewerName: $json.interviewerName,
  hrEmail: $json.hrEmail,
  emailToCandidate: {
    to: $json.candidateEmail,
    subject: `Interview Scheduled - ${$json.position}`,
    text: `Dear ${$json.candidateName}...`
  },
  emailToHr: {
    to: $json.hrEmail,
    subject: `Interview Confirmation - ${$json.candidateName}`,
    text: `Candidate interview scheduled...`
  }
};
```

---

## Testing

### Manual Webhook Testing

Using cURL:

```bash
# Test Acceptance Workflow
curl -X POST http://localhost:5678/webhook/candidate-acceptance \
  -H 'Content-Type: application/json' \
  -d '{
    "candidateId": "test_cand_001",
    "candidateName": "John Doe",
    "candidateEmail": "john@example.com",
    "position": "Senior Engineer",
    "interviewDate": "2026-04-25",
    "interviewTime": "10:00 AM",
    "interviewDuration": 60,
    "timezone": "EST",
    "meetingLink": "https://meet.google.com/test",
    "interviewerName": "Jane Smith",
    "hrEmail": "hr@example.com"
  }'

# Test Rejection Workflow
curl -X POST http://localhost:5678/webhook/candidate-rejection \
  -H 'Content-Type: application/json' \
  -d '{
    "candidateId": "test_cand_002",
    "candidateName": "Jane Doe",
    "candidateEmail": "jane@example.com",
    "position": "Senior Engineer",
    "rejectionReason": "Did not meet technical requirements",
    "feedbackSummary": "Strong communication but lacking Python expertise",
    "hrEmail": "hr@example.com",
    "allowReapply": true,
    "reapplyAfterMonths": 6
  }'
```

### Postman Testing

1. Import the provided collection (or create manually)
2. Set base URL to your n8n instance
3. Use the payload structures from `WEBHOOK_GUIDE.json`
4. Run individual requests to test workflow triggers

### Backend API Testing

```bash
# Test Interview Scheduled Endpoint
curl -X POST http://localhost:8000/api/v1/candidates/test_cand_001/interview-scheduled \
  -H 'Content-Type: application/json' \
  -d '{
    "interview_date": "2026-04-25",
    "interview_time": "10:00 AM",
    "interview_duration": 60,
    "timezone": "EST",
    "meeting_link": "https://meet.google.com/test",
    "interviewer_name": "Jane Smith",
    "hr_email": "hr@example.com"
  }'

# Test Rejection Endpoint
curl -X POST http://localhost:8000/api/v1/candidates/test_cand_002/rejection \
  -H 'Content-Type: application/json' \
  -d '{
    "rejection_reason": "Did not meet technical requirements",
    "feedback_summary": "Strong communication but lacking Python expertise",
    "hr_email": "hr@example.com",
    "allow_reapply": true,
    "reapply_after_months": 6
  }'
```

---

## Troubleshooting

### Issue: Webhook not triggering

**Solution:**
1. Check that n8n workflow is active (click "Test")
2. Verify webhook URL is correct
3. Check n8n logs for errors
4. Ensure request payload matches expected structure

### Issue: Email not sending

**Solution:**
1. Verify email credentials are correct
2. Check that recipient email is valid
3. Review email service error logs
4. For Gmail: enable "Less secure apps"
5. For SendGrid: verify API key is active

### Issue: Database update failing

**Solution:**
1. Verify database connection is active
2. Check that candidate ID exists
3. Review MongoDB connection string
4. Check user permissions on database

### Issue: API returning 404

**Solution:**
1. Verify candidate ID is correct format
2. Check that candidate exists in database
3. Verify API endpoint is spelled correctly
4. Check that backend server is running

### Issue: CORS errors in frontend

**Solution:**
1. Add CORS headers to FastAPI app:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Production Deployment

### n8n Production Setup

1. **Use managed n8n cloud** or self-host with:
   - SSL/TLS encryption
   - Firewall protection
   - Database backup
   - Monitoring and alerts

2. **Security Configuration**
   - Enable authentication tokens for webhooks
   - Use environment variables for sensitive data  
   - Enable workflow versioning
   - Set up audit logging

3. **Email Service**
   - Use dedicated email service (SendGrid, AWS SES)
   - Configure SPF/DKIM/DMARC records
   - Set up bounce handling
   - Monitor email delivery

### Backend API Production Setup

1. **Deployment**
   - Use production ASGI server (Gunicorn, Uvicorn)
   - Enable HTTPS with valid SSL certificate
   - Set up reverse proxy (Nginx)
   - Configure load balancing if needed

2. **Database**
   - Enable MongoDB replica set
   - Configure backup schedule
   - Set up monitoring alerts
   - Ensure proper indexing on frequently queried fields

3. **Monitoring**
   - Set up application logs
   - Monitor API response times
   - Track workflow execution times
   - Alert on failures

### Environment Variables (Production)

```bash
# N8N
N8N_DEPLOYMENT_TYPE=docker
N8N_ENDPOINT_REST=https://your-domain.com/n8n
N8N_ENDPOINT_WEBHOOK=https://your-domain.com/n8n/webhook
N8N_JWT_EXPIRATION=7d

# Backend API
DATABASE_URL=mongodb+srv://...
API_BASE_URL=https://api.your-domain.com
CORS_ORIGINS=https://your-domain.com

# Email
EMAIL_SERVICE=sendgrid
SENDGRID_API_KEY=...
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# Security
WEBHOOK_AUTH_TOKEN=your_secure_random_token
JWT_SECRET=your_jwt_secret
API_KEY=your_api_key

# Notifications
SLACK_WEBHOOK=... # Optional for alerts
```

---

## Summary

This integration provides:

✅ Automated candidate decision notifications  
✅ Professional email templates with styling  
✅ Interview scheduling with meeting links  
✅ Rejection notifications with reapply info  
✅ HR team notifications and coordination  
✅ Audit trail of all decisions  
✅ Scalable n8n-based automation  
✅ Database persistence of all interactions  

**Next Steps:**
1. Import workflow JSONs into n8n
2. Configure email service
3. Test workflows with sample payloads
4. Integrate frontend with webhooks
5. Deploy to production
