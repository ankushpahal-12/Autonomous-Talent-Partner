# n8n Workflows - Complete Overview

Quick reference guide for all n8n automation workflows in the Talent Partner system.

## Available Workflows

| Workflow | Version | File | Type | Use Case |
|----------|---------|------|------|----------|
| **Candidate Acceptance** | v2.0.0 (New) | [candidate_acceptance_ai_agent.json](candidate_acceptance_ai_agent.json) | AI Agent | Send personalized acceptance emails + calendar events using Gemini AI |
| **Candidate Acceptance** | v1.1.0 | [candidate_acceptance_workflow.json](candidate_acceptance_workflow.json) | Template-based | Send acceptance emails with hardcoded templates |
| **Candidate Rejection** | v1.0.0 | [candidate_rejection_workflow.json](candidate_rejection_workflow.json) | Template-based | Send rejection emails with feedback |
| **Interview Scheduler** | v1.0.0 | [interview_scheduler.json](interview_scheduler.json) | Standard | Schedule interviews and send confirmations |

---

## Which Workflow Should I Use?

### For Candidate Acceptance

#### Choose v2.0.0 (AI Agent) if:
- You want personalized emails without templates
- You have Google Cloud setup ready
- You want professional AI-generated content
- You need calendar event creation
- You want to scale without template management
- **Setup Time:** 30 minutes (includes Google credentials)

#### Choose v1.1.0 (Template-based) if:
- You prefer consistent, templated emails
- You want simpler setup without Google services
- Email content is stable and rarely changes
- You don't need calendar integration
- **Setup Time:** 10 minutes

### For Candidate Rejection
- Use v1.0.0 with [candidate_rejection_workflow.json](candidate_rejection_workflow.json)
- Sends rejection emails with feedback
- **Setup Time:** 10 minutes

### For Interview Scheduling
- Use v1.0.0 with [interview_scheduler.json](interview_scheduler.json)
- Schedule meetings and send reminders
- **Setup Time:** 15 minutes

---

## Webhook Endpoints

### Candidate Acceptance (Both Versions)
```
POST http://localhost:5678/webhook/candidate-acceptance
```

**Minimal Payload:**
```json
{
  "candidateName": "John Doe",
  "candidateEmail": "john@example.com"
}
```

**Full Payload:**
```json
{
  "candidateName": "John Doe",
  "candidateEmail": "john@example.com",
  "position": "Senior Backend Developer",
  "company": "Tech Company Inc",
  "interviewDate": "2024-04-20",
  "interviewTime": "10:00 AM",
  "timezone": "EST",
  "hrEmail": "hr@company.com"
}
```

### Candidate Rejection
```
POST http://localhost:5678/webhook/candidate-rejection
```

**Payload:**
```json
{
  "candidateName": "Jane Smith",
  "candidateEmail": "jane@example.com",
  "position": "Frontend Developer",
  "feedback": "Strong technical skills, cultural fit needs assessment",
  "inviteReapply": true,
  "reapplyEligibilityMonths": 6
}
```

### Interview Scheduler
```
POST http://localhost:5678/webhook/interview-scheduler
```

**Payload:**
```json
{
  "candidateId": "507f1f77bcf86cd799439011",
  "candidateName": "Bob Wilson",
  "candidateEmail": "bob@example.com",
  "position": "DevOps Engineer",
  "interviewDate": "2024-04-25",
  "interviewTime": "2:00 PM",
  "interviewerName": "Tech Team Lead",
  "timezone": "PST"
}
```

---

## Setup Comparison

### v2.0.0 (AI Agent) - Recommended for Enterprise

**Setup Requirements:**
1. Google Cloud project with APIs enabled
2. Gmail API credentials
3. Google Calendar API credentials
4. Google Generative AI API key
5. n8n instance with Google integrations

**Time to Deploy:** 30-45 minutes

**Pros:**
- Personalized emails at scale
- Professional AI-generated content
- Automatic calendar event creation
- No template maintenance
- Natural language customization via prompts
- Impressive user experience

**Cons:**
- More complex setup
- Requires Google services
- Slight latency from AI generation (5-10 seconds)
- Small cost for API calls

**Cost:** ~$0.001 per request (Gemini API)

---

### v1.1.0 (Template-based) - Recommended for Simple Use

**Setup Requirements:**
1. n8n instance
2. Email provider (Gmail, SendGrid, or SMTP)

**Time to Deploy:** 10-15 minutes

**Pros:**
- Simple setup, minimal configuration
- Fast execution (1-2 seconds)
- No external AI service required
- Consistent branding and messaging
- Low cost

**Cons:**
- Template changes require workflow editing
- Less personalization
- Template bloat for multiple scenarios
- Requires manual prompt generation

**Cost:** Free (unless using paid email service)

---

## Feature Comparison

| Feature | v2.0.0 (AI Agent) | v1.1.0 (Template) |
|---------|-------------------|------------------|
| Personalized emails | ✅ Yes | ❌ No |
| Calendar event creation | ✅ Yes | ❌ No |
| Email customization | ✅ Prompt-based | ❌ Template-based |
| Setup complexity | 🔴 Medium | 🟢 Low |
| Execution speed | 🟡 5-10 seconds | 🟢 1-2 seconds |
| AI involvement | ✅ Gemini | ❌ None |
| Scalability | ✅ High | ✅ High |
| Cost | 💰 ~$0.001/request | 💰 Free-low |

---

## Getting Started

### Option 1: Quick Start with v1.1.0 (5 minutes)
1. Open n8n dashboard
2. Click "Import" → "From file"
3. Upload candidate_acceptance_workflow.json
4. Configure email provider
5. Test with sample webhook payload
6. Done!

### Option 2: Enterprise Setup with v2.0.0 (30 minutes)

1. **Setup Google Cloud:**
   - Create project
   - Enable Gmail, Calendar, Generative AI APIs
   - Create credentials

2. **Configure n8n:**
   - Add Google credentials
   - Import candidate_acceptance_ai_agent.json

3. **Test:**
   - Send test webhook payload
   - Verify email received
   - Check calendar event created

4. **Deploy:**
   - Configure webhook URL in backend
   - Monitor executions

---

## Integration with Backend

### FastAPI Integration Example

```python
# services/n8n_service.py
import aiohttp
from enum import Enum

class WorkflowType(str, Enum):
    ACCEPTANCE_V2 = "candidate-acceptance"
    ACCEPTANCE_V1 = "candidate-acceptance-legacy"
    REJECTION = "candidate-rejection"
    INTERVIEW = "interview-scheduler"

class N8nService:
    def __init__(self):
        self.base_url = "http://localhost:5678/webhook"
    
    async def send_acceptance(self, candidate: dict, use_ai: bool = True):
        """Send candidate acceptance notification."""
        
        endpoint = "candidate-acceptance"
        payload = {
            "candidateName": candidate["name"],
            "candidateEmail": candidate["email"],
            "position": candidate.get("position"),
            "interviewDate": candidate.get("interview_date"),
            "interviewTime": candidate.get("interview_time"),
            "timezone": "EST"
        }
        
        return await self._trigger_workflow(endpoint, payload)
    
    async def send_rejection(self, candidate: dict, feedback: str):
        """Send candidate rejection notification."""
        
        payload = {
            "candidateName": candidate["name"],
            "candidateEmail": candidate["email"],
            "position": candidate.get("position"),
            "feedback": feedback,
            "inviteReapply": True
        }
        
        return await self._trigger_workflow("candidate-rejection", payload)
    
    async def _trigger_workflow(self, endpoint: str, payload: dict):
        """Trigger n8n workflow."""
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/{endpoint}",
                json=payload
            ) as response:
                return await response.json()

# api/candidates.py
from services.n8n_service import N8nService

n8n = N8nService()

@router.post("/{candidate_id}/mark-accepted")
async def mark_candidate_accepted(candidate_id: str):
    """Mark candidate as accepted and send notification."""
    
    candidate = await get_candidate(candidate_id)
    
    # Send via n8n (v2.0.0 AI Agent by default)
    result = await n8n.send_acceptance(candidate, use_ai=True)
    
    # Update database
    await update_candidate_status(candidate_id, "ACCEPTED")
    
    return {"status": "success", "n8n_result": result}
```

---

## Monitoring & Logging

### View Workflow Executions
1. n8n Dashboard > Executions
2. Click workflow name to see details
3. View timestamps, status, error messages

### Monitor Google API Usage
1. Google Cloud Console
2. APIs & Services > Dashboard
3. Check quotas and usage

### Troubleshooting Execution Failures

| Error | Cause | Solution |
|-------|-------|----------|
| UNAUTHENTICATED | Gmail credentials invalid | Re-authenticate Google services |
| RESOURCE_EXHAUSTED | API quota exceeded | Wait for quota reset or upgrade plan |
| INVALID_ARGUMENT | Malformed webhook payload | Check field types and required fields |
| DEADLINE_EXCEEDED | Workflow timeout | Increase timeout, reduce complexity |
| PERMISSION_DENIED | Missing API permissions | Enable required APIs in Google Cloud |

---

## Production Deployment Checklist

- [ ] Google APIs enabled and quotas verified
- [ ] Webhook endpoint exposed securely (HTTPS)
- [ ] Rate limiting configured
- [ ] Error notifications setup
- [ ] Database logging configured
- [ ] Email templates tested completely
- [ ] Calendar event format verified
- [ ] Timeout values tuned
- [ ] Execution logs retention setup
- [ ] Backup and disaster recovery plan

---

## Version Migration

### Migrating from v1.1.0 to v2.0.0

**No data loss:** Both workflows are independent

**Steps:**
1. Setup Google Cloud credentials (see setup guide)
2. Import new workflow (candidate_acceptance_ai_agent.json)
3. Update backend to use new webhook endpoint
4. Test with sample candidate
5. Gradually transition in frontend buttons
6. Keep old workflow as fallback initially

**Rollback Plan:**
If v2.0.0 issues occur:
1. Update backend to point to v1.1.0 endpoint
2. v1.1.0 remains active and untouched
3. Investigate v2.0.0 issue
4. Re-deploy when fixed

---

## FAQ

**Q: Can I run both v1.1.0 and v2.0.0 simultaneously?**
A: Yes! They use different endpoints, so both can be active.

**Q: What if Gemini API is down?**
A: Fallback to v1.1.0 endpoint immediately. Implement retry logic.

**Q: How do I customize email content in v2.0.0?**
A: Edit the prompt in "Generate Email Prompt" node. Change wording, tone, structure.

**Q: Is there a cost difference?**
A: v2.0.0 costs ~$0.001/request (Gemini API), v1.1.0 is free.

**Q: How often should I rotate API keys?**
A: Every 90 days for security best practices.

**Q: Can I test workflows without sending emails?**
A: Yes - use "Test" mode in n8n, it won't execute send actions.

---

## Documentation

- **Setup Guide:** [CANDIDATE_ACCEPTANCE_AI_GUIDE.md](CANDIDATE_ACCEPTANCE_AI_GUIDE.md) (v2.0.0)
- **Integration Guide:** [N8N_INTEGRATION_GUIDE.md](N8N_INTEGRATION_GUIDE.md)
- **API Reference:** [API_REFERENCE.md](API_REFERENCE.md)
- **Webhook Guide:** [WEBHOOK_GUIDE.json](WEBHOOK_GUIDE.json)

---

**Last Updated:** April 2026
**Latest Version:** 2.0.0 (AI Agent)
