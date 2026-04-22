# n8n Integration - Quick Reference Card

## What's New

### Backend API Endpoints
```
POST /api/v1/candidates/{id}/interview-scheduled
POST /api/v1/candidates/{id}/rejection
```

### n8n Workflow Webhooks
```
POST http://localhost:5678/webhook/candidate-acceptance
POST http://localhost:5678/webhook/candidate-rejection
```

---

## Workflow Overview

### Acceptance Flow
Candidate Accepted → n8n Webhook → Send Emails → Update DB → Log Activity

### Rejection Flow
Candidate Rejected → n8n Webhook → Send Emails → Update DB → Log Activity

---

## Key Files

| File | Purpose | Location |
|------|---------|----------|
| candidate_acceptance_workflow.json | n8n workflow for accepted candidates | backend/n8nworkflow/ |
| candidate_rejection_workflow.json | n8n workflow for rejected candidates | backend/n8nworkflow/ |
| N8N_INTEGRATION_GUIDE.md | Complete integration guide | backend/n8nworkflow/ |
| API_REFERENCE.md | API endpoint documentation | backend/n8nworkflow/ |
| WEBHOOK_GUIDE.json | Webhook payload reference | backend/n8nworkflow/ |
| IMPLEMENTATION_SUMMARY.md | Project overview | backend/n8nworkflow/ |
| candidates.py | Backend API file (modified) | backend/app/api/v1/ |

---

## Quick Setup (5 minutes)

### Step 1: Import Workflows
1. Open n8n dashboard
2. Click "Import"
3. Upload both JSON workflow files

### Step 2: Configure Email
In each workflow, set Email node credentials:
- Provider: Gmail / SendGrid / SMTP
- From: hr@company.com

### Step 3: Test
```bash
curl -X POST http://localhost:5678/webhook/candidate-acceptance \
  -H 'Content-Type: application/json' \
  -d '{"candidateId":"test","candidateName":"John","candidateEmail":"john@example.com","position":"Engineer","interviewDate":"2026-04-25","interviewTime":"2:00 PM","timezone":"EST","meetingLink":"https://meet.google.com/test","interviewerName":"Jane","hrEmail":"hr@example.com"}'
```

---

## Integration Points

### Frontend
- Call `/webhook/candidate-acceptance` when accepting
- Call `/webhook/candidate-rejection` when rejecting
- Send candidate and interview details in JSON payload

### Backend
- `/interview-scheduled` endpoint receives data from n8n
- `/rejection` endpoint receives rejection data from n8n
- Updates MongoDB and logs activities

### Database
- Adds interview details to candidate document
- Updates status to "interview_scheduled" or "rejected"
- Records in status_history array

---

## API Request Examples

### Schedule Interview
```bash
POST /api/v1/candidates/{id}/interview-scheduled

{
  "interview_date": "2026-04-25",
  "interview_time": "2:00 PM",
  "interview_duration": 60,
  "timezone": "EST",
  "meeting_link": "https://meet.google.com/...",
  "interviewer_name": "Jane Smith",
  "hr_email": "hr@company.com"
}
```

### Record Rejection
```bash
POST /api/v1/candidates/{id}/rejection

{
  "rejection_reason": "Did not meet technical requirements",
  "feedback_summary": "Strong communication but lacking technical skills",
  "hr_email": "hr@company.com",
  "allow_reapply": true,
  "reapply_after_months": 6
}
```

---

## Database Updates

### After Interview Scheduled
```javascript
{
  status: "interview_scheduled",
  interview_date: "2026-04-25",
  interview_time: "2:00 PM",
  meeting_link: "https://meet.google.com/...",
  interviewer_name: "Jane Smith",
  notification_timestamp: "2026-04-01T14:30:00Z"
}
```

### After Rejection
```javascript
{
  status: "rejected",
  rejection_reason: "Did not meet technical requirements",
  feedback_summary: "...",
  allow_reapply: true,
  reapply_eligible_date: "2026-10-01T14:30:00Z"
}
```

---

## Testing Checklist

- [ ] n8n workflows imported successfully
- [ ] Email provider credentials configured
- [ ] Webhooks respond to test requests
- [ ] Backend API endpoints accessible
- [ ] Database updates working
- [ ] Emails sending to test recipients
- [ ] Activity logs recording correctly

---

## Email Templates

### Acceptance Email (to Candidate)
- Interview date/time
- Meeting link with direct join button
- Interviewer name
- Timezone-aware display
- Professional footer

### Rejection Email (to Candidate)
- Empathetic tone
- Constructive feedback
- Reapply eligibility date
- LinkedIn profile suggestion
- Support contact

### HR Notification (Both)
- Candidate summary
- Decision details
- Action items
- Audit trail

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Webhook not triggering | Check n8n workflow is active; verify URL endpoint |
| Email not sending | Verify credentials; check spam folder; enable "Less secure apps" for Gmail |
| Database not updating | Check MongoDB connection; verify candidate ID exists |
| 404 error on API | Ensure backend server running; check candidate exists |

---

## Documentation

For detailed info, see:
- **N8N_INTEGRATION_GUIDE.md** - Complete setup guide
- **API_REFERENCE.md** - Endpoint documentation
- **WEBHOOK_GUIDE.json** - Payload structures
- **IMPLEMENTATION_SUMMARY.md** - Architecture overview

---

## Support

All files are located in: `backend/n8nworkflow/`

Each document includes:
✅ Step-by-step instructions
✅ Code examples
✅ Troubleshooting guide
✅ Testing procedures
✅ Production deployment notes
