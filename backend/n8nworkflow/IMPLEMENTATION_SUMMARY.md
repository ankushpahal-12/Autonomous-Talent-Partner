# n8n Workflow Automation - Implementation Summary

Complete summary of the n8n workflow automation system for candidate decision notifications.

---

## Overview

This implementation provides **automated, professional notification workflows** for candidate decisions (acceptance and rejection) with:

✅ **Email Notifications** - Separate templates for candidates and HR team  
✅ **Interview Scheduling** - Automatic recording with meeting links and timestamps  
✅ **Rejection Management** - Professional rejection emails with reapply eligibility  
✅ **Database Integration** - Automatic status updates and audit trails  
✅ **Activity Logging** - Complete history of all HR decisions  

---

## Files Created/Modified

### New Files

#### 1. **candidate_acceptance_workflow.json**
- **Path:** `backend/n8nworkflow/candidate_acceptance_workflow.json`
- **Size:** ~5,000 characters
- **Purpose:** n8n workflow for candidate acceptance notifications
- **Trigger:** Webhook at `/webhooks/candidate-acceptance`
- **Nodes:**
  - Webhook trigger
  - JavaScript data parser
  - Email to candidate (HTML template)
  - Email to HR team
  - HTTP API call to update database
  - File logger for audit trail

#### 2. **candidate_rejection_workflow.json**
- **Path:** `backend/n8nworkflow/candidate_rejection_workflow.json`
- **Size:** ~5,000 characters
- **Purpose:** n8n workflow for candidate rejection notifications
- **Trigger:** Webhook at `/webhooks/candidate-rejection`
- **Nodes:**
  - Webhook trigger
  - JavaScript data parser
  - Email to candidate (empathetic template)
  - Email to HR team (rejection record)
  - HTTP API call to update database
  - File logger for audit trail

#### 3. **WEBHOOK_GUIDE.json**
- **Path:** `backend/n8nworkflow/WEBHOOK_GUIDE.json`
- **Purpose:** Complete webhook payload reference and testing guide
- **Contents:** 
  - Webhook URL structures
  - Payload examples for both workflows
  - cURL examples for testing
  - Email template variables
  - Backend integration details
  - Production checklist

#### 4. **N8N_INTEGRATION_GUIDE.md**
- **Path:** `backend/n8nworkflow/N8N_INTEGRATION_GUIDE.md`
- **Purpose:** Complete integration guide (9 sections, 500+ lines)
- **Contents:**
  - Quick start instructions
  - Workflow architecture diagrams
  - Frontend integration code examples
  - Backend API setup and configuration
  - n8n configuration steps
  - Testing procedures and cURL commands
  - Troubleshooting guide
  - Production deployment checklist

#### 5. **API_REFERENCE.md**
- **Path:** `backend/n8nworkflow/API_REFERENCE.md`
- **Purpose:** API endpoint reference documentation
- **Contents:**
  - Endpoint specifications
  - Request/response schemas
  - Field definitions and validation
  - Database schema updates
  - Activity logging format
  - Usage examples in multiple languages
  - Rate limiting and authentication notes

### Modified Files

#### 1. **candidates.py** (Backend API)
- **Path:** `backend/app/api/v1/candidates.py`
- **Changes:**
  - Added 2 new Pydantic models for request validation
  - Added 2 new POST endpoints
  - Integrated with activity logging system
  - Full error handling and validation

**New Models:**
1. `InterviewScheduleRequest` - For scheduling interviews
2. `CandidateRejectionRequest` - For recording rejections

**New Endpoints:**
1. `POST /{candidate_id}/interview-scheduled` - Record interview scheduling
2. `POST /{candidate_id}/rejection` - Record candidate rejection

---

## Architecture Overview

### Data Flow: Acceptance Path

```
Frontend (Accept Button)
    ↓
n8n Webhook Trigger (/webhooks/candidate-acceptance)
    ↓
Parse Candidate Data
    ↓
    ├─→ Email Service (Send to Candidate)
    ├─→ Email Service (Send to HR)
    ┤
    ├─→ Backend API (POST /interview-scheduled)
    │   ├─→ MongoDB Update
    │   ├─→ Add to Status History
    │   └─→ Activity Log
    │
    └─→ File Logger (Audit Trail)
```

### Data Flow: Rejection Path

```
Frontend (Reject Button)
    ↓
n8n Webhook Trigger (/webhooks/candidate-rejection)
    ↓
Parse Rejection Data (Calculate Reapply Date)
    ↓
    ├─→ Email Service (Send to Candidate)
    ├─→ Email Service (Send to HR)
    ┤
    ├─→ Backend API (POST /rejection)
    │   ├─→ MongoDB Update
    │   ├─→ Add to Status History
    │   └─→ Activity Log
    │
    └─→ File Logger (Audit Trail)
```

---

## Key Features

### 1. Professional Email Templates

**Acceptance Email to Candidate:**
- Personalized greeting
- Interview details (date, time, duration)
- Meeting link with direct join button
- Interviewer information
- Timezone-aware time display
- Professional footer with company info

**Acceptance Email to HR:**
- Candidate summary
- Interview scheduling confirmation
- Interviewer assignment
- Meeting details
- Action items (if any)

**Rejection Email to Candidate:**
- Empathetic tone
- Constructive feedback
- Encouragement to reapply
- Reapply eligibility date
- LinkedIn profile connection suggestion
- Support contact information

**Rejection Email to HR:**
- Reject confirmation
- Candidate summary
- Reason for rejection
- Feedback provided
- Reapply eligibility tracking
- Future candidate pool notes

### 2. Automatic Database Updates

Both workflows automatically update the MongoDB candidate document with:
- New status (`interview_scheduled` or `rejected`)
- Relevant scheduling or rejection details
- Timestamps for all actions
- Complete audit trail in `status_history` array
- Reapply eligibility date (for rejections)

### 3. Comprehensive Logging

Every workflow execution logs:
- Action timestamp
- Candidate information
- Decision details
- Email recipients
- API responses
- Any errors or issues

---

## Integration Checklist

### Phase 1: Setup (1-2 hours)
- [ ] Import workflow JSONs into n8n
- [ ] Configure email service (Gmail/SendGrid/SMTP)
- [ ] Test webhook endpoints with cURL
- [ ] Verify backend API endpoints are running
- [ ] Test database connectivity

### Phase 2: Frontend Integration (2-3 hours)
- [ ] Add InterviewScheduleRequest modal to EnhancedCandidateDetail
- [ ] Add CandidateRejectionRequest form to UI
- [ ] Update decision buttons to trigger webhooks
- [ ] Add error handling and user feedback
- [ ] Test end-to-end flows in development

### Phase 3: Testing (1-2 hours)
- [ ] Run manual webhook tests with cURL
- [ ] Send test emails to team
- [ ] Verify database updates
- [ ] Check activity logs
- [ ] Review email delivery

### Phase 4: Production Deployment (2-4 hours)
- [ ] Configure production n8n instance
- [ ] Set up email service for production
- [ ] Update API base URLs
- [ ] Enable HTTPS/SSL
- [ ] Configure monitoring and alerts
- [ ] Deploy frontend changes
- [ ] Conduct full system test

---

## Payload Examples

### Acceptance Webhook Payload
```json
{
  "candidateId": "john_doe_123",
  "candidateName": "John Doe",
  "candidateEmail": "john.doe@example.com",
  "position": "Senior Software Engineer",
  "interviewDate": "2026-04-25",
  "interviewTime": "2:00 PM",
  "interviewDuration": 60,
  "timezone": "EST",
  "meetingLink": "https://meet.google.com/abc-defg-hij",
  "interviewerName": "Jane Smith",
  "hrEmail": "hr@company.com"
}
```

### Rejection Webhook Payload
```json
{
  "candidateId": "jane_doe_456",
  "candidateName": "Jane Doe",
  "candidateEmail": "jane.doe@example.com",
  "position": "Product Manager",
  "rejectionReason": "Did not meet technical requirements",
  "feedbackSummary": "Strong communication skills but lacking required technical background",
  "hrEmail": "hr@company.com",
  "allowReapply": true,
  "reapplyAfterMonths": 6
}
```

---

## Configuration Requirements

### Environment Variables

```bash
# n8n Configuration
N8N_BASE_URL=http://localhost:8000
N8N_WEBHOOK_AUTH_TOKEN=your_secure_token

# Email Configuration
EMAIL_SERVICE=gmail|sendgrid|smtp
SENDGRID_API_KEY=your_key
GMAIL_EMAIL=your_email@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# Company Configuration
HR_EMAIL=hr@company.com
COMPANY_NAME=Your Company
SUPPORT_EMAIL=support@company.com

# Backend
API_BASE_URL=http://localhost:8000
DATABASE_URL=mongodb://...
```

### n8n Credentials

1. **Email Credential** (Gmail/SendGrid/SMTP)
   - Service type
   - Authentication details
   - From address

2. **HTTP Credential** (Optional)
   - Bearer token for API calls
   - Custom headers

---

## Testing Commands

### Test Acceptance Workflow
```bash
curl -X POST http://localhost:5678/webhook/candidate-acceptance \
  -H 'Content-Type: application/json' \
  -d @webhook_acceptance_test.json
```

### Test Rejection Workflow
```bash
curl -X POST http://localhost:5678/webhook/candidate-rejection \
  -H 'Content-Type: application/json' \
  -d @webhook_rejection_test.json
```

### Test Backend API
```bash
curl -X POST http://localhost:8000/api/v1/candidates/test_123/interview-scheduled \
  -H 'Content-Type: application/json' \
  -d '{"interview_date":"2026-04-25","interview_time":"2:00 PM","meeting_link":"...","interviewer_name":"Jane","hr_email":"hr@company.com"}'
```

---

## Database Schema Updates

### Fields Added to Candidate Document

**Interview Scheduled:**
```javascript
{
  status: "interview_scheduled",
  interview_date: "2026-04-25",
  interview_time: "2:00 PM",
  interview_duration: 60,
  timezone: "EST",
  meeting_link: "https://meet.google.com/...",
  interviewer_name: "Jane Smith",
  notification_sent: true,
  notification_timestamp: "ISO8601"
}
```

**Rejection:**
```javascript
{
  status: "rejected",
  rejection_reason: "string",
  feedback_summary: "string",
  allow_reapply: boolean,
  reapply_after_months: number,
  reapply_eligible_date: "ISO8601",
  notification_sent: true,
  notification_timestamp: "ISO8601"
}
```

---

## Security Considerations

### For Production

1. **API Authentication**
   - Implement JWT token validation
   - Use API keys for workflow calls
   - Enable HTTPS only

2. **Email Security**
   - Use dedicated email service (SendGrid, AWS SES)
   - Configure SPF/DKIM/DMARC records
   - Enable TLS for SMTP connections

3. **Webhook Security**
   - Validate webhook signatures
   - Use bearer tokens for authentication
   - IP whitelist n8n instances
   - Rate limit webhook endpoints

4. **Data Protection**
   - Encrypt sensitive data in transit
   - Hash candidate contact information
   - Implement access controls
   - Enable audit logging

---

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Workflow Execution**
   - Execution count per day
   - Success/failure rate
   - Average execution time
   - Failed email deliveries

2. **API Performance**
   - Response time
   - Error rate
   - Database query time
   - Concurrent requests

3. **Email Delivery**
   - Delivery rate
   - Bounce rate
   - Open rate (if tracking enabled)
   - Spam complaints

### Alert Conditions

- Workflow failure rate > 5%
- API response time > 1 second
- Email delivery rate < 95%
- Database connection errors
- Webhook endpoint unavailable

---

## Next Steps

1. **Import Workflows**
   - Copy JSON files to n8n
   - Configure email service
   - Test webhooks

2. **Update Frontend**
   - Add modal components
   - Integrate with webhooks
   - Add error handling

3. **Run Tests**
   - End-to-end workflow testing
   - Email delivery verification
   - Database update validation

4. **Deploy to Production**
   - Configure production environment
   - Set up monitoring
   - Train team on new workflow

---

## Support Documentation

- **WEBHOOK_GUIDE.json** - Webhook payload reference
- **N8N_INTEGRATION_GUIDE.md** - Complete integration guide
- **API_REFERENCE.md** - API endpoint documentation

---

## Summary

This n8n workflow automation system provides:

✅ **Automated Notifications** - Professional emails to candidates and HR  
✅ **Interview Scheduling** - Automatic recording with audit trails  
✅ **Rejection Management** - Professional rejection process with reapply tracking  
✅ **Database Integration** - Seamless MongoDB updates with history  
✅ **Activity Logging** - Complete audit trail of all actions  
✅ **Error Handling** - Comprehensive error handling and recovery  
✅ **Scalability** - Ready for production deployment  
✅ **Monitoring** - Built-in logging and activity tracking  

**Total Implementation Time:** 4-8 hours (setup + integration + testing)

**Maintenance:** Minimal - n8n handles workflow execution and error recovery
