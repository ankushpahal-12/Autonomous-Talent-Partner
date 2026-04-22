# API Documentation

Complete REST API reference for the Talent Partner system. All endpoints require proper authentication and return JSON responses.

## Base URL

```
http://127.0.0.1:8000/api/v1
```

For production:
```
https://your-deployment-domain.com/api/v1
```

---

## Authentication

All endpoints require a valid session. Authentication is handled through:
- Session cookies (automatically managed by frontend)
- Request headers may include authorization tokens if configured

---

## Job Management Endpoints

### 1. Create a New Job

**Endpoint:** `POST /jobs`

**Description:** Creates a new job posting in DRAFT status.

**Request:**
```json
{
  "company": "Tech Company Inc",
  "job_title": "Senior Backend Developer",
  "job_description": "Looking for experienced backend developer with Python expertise. 5+ years required.",
  "requirements": [
    "Python 3.9+",
    "FastAPI experience",
    "MongoDB knowledge",
    "REST API design",
    "3+ years backend development"
  ],
  "skills": [
    "Python",
    "AsyncIO",
    "FastAPI",
    "MongoDB",
    "Docker"
  ],
  "experience_level": "Senior",
  "location": "New York, NY",
  "salary_min": 140000,
  "salary_max": 180000,
  "employment_type": "Full-time",
  "remote": true
}
```

**Response:** `201 Created`
```json
{
  "status": "success",
  "job_id": "65d4a2c8f1e2a3b4c5d6e7f8",
  "message": "Job created successfully",
  "job": {
    "id": "65d4a2c8f1e2a3b4c5d6e7f8",
    "company": "Tech Company Inc",
    "job_title": "Senior Backend Developer",
    "status": "DRAFT",
    "created_at": "2024-04-15T10:30:00Z",
    "updated_at": "2024-04-15T10:30:00Z"
  }
}
```

**Error Response:** `400 Bad Request`
```json
{
  "status": "error",
  "message": "Missing required field: job_title"
}
```

---

### 2. Get All Jobs

**Endpoint:** `GET /jobs`

**Description:** Retrieves all jobs with optional filtering and pagination.

**Query Parameters:**
- `skip` (integer): Number of records to skip (default: 0)
- `limit` (integer): Number of records to return (default: 10, max: 100)
- `status` (string): Filter by status (DRAFT, REVIEWING, FINALIZED, PUBLISHED, ARCHIVED)
- `company` (string): Filter by company name (partial match)
- `search` (string): Search in title and description

**Request:**
```
GET /jobs?skip=0&limit=20&status=PUBLISHED
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "data": [
    {
      "id": "65d4a2c8f1e2a3b4c5d6e7f8",
      "company": "Tech Company Inc",
      "job_title": "Senior Backend Developer",
      "status": "PUBLISHED",
      "created_at": "2024-04-15T10:30:00Z",
      "location": "New York, NY",
      "salary_min": 140000,
      "salary_max": 180000
    }
  ],
  "pagination": {
    "total": 45,
    "skip": 0,
    "limit": 20,
    "pages": 3
  }
}
```

---

### 3. Get Single Job Details

**Endpoint:** `GET /jobs/{job_id}`

**Description:** Retrieves complete details of a specific job.

**Path Parameters:**
- `job_id` (string, required): MongoDB ObjectId of the job

**Request:**
```
GET /jobs/65d4a2c8f1e2a3b4c5d6e7f8
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "data": {
    "id": "65d4a2c8f1e2a3b4c5d6e7f8",
    "company": "Tech Company Inc",
    "job_title": "Senior Backend Developer",
    "job_description": "Looking for experienced backend developer...",
    "requirements": [
      "Python 3.9+",
      "FastAPI experience",
      "MongoDB knowledge"
    ],
    "skills": [
      "Python",
      "FastAPI",
      "MongoDB"
    ],
    "status": "PUBLISHED",
    "experience_level": "Senior",
    "location": "New York, NY",
    "salary_min": 140000,
    "salary_max": 180000,
    "employment_type": "Full-time",
    "remote": true,
    "created_at": "2024-04-15T10:30:00Z",
    "updated_at": "2024-04-15T10:30:00Z",
    "published_at": "2024-04-15T11:00:00Z",
    "ai_suggestions": null,
    "matched_candidates": [],
    "candidate_count": 0
  }
}
```

**Error Response:** `404 Not Found`
```json
{
  "status": "error",
  "message": "Job not found"
}
```

---

### 4. Update Job (Edit)

**Endpoint:** `PUT /jobs/edit/{job_id}`

**Description:** Updates job details in DRAFT or REVIEWING status only.

**Path Parameters:**
- `job_id` (string, required): MongoDB ObjectId of the job

**Request:**
```json
{
  "job_title": "Senior Backend Engineer",
  "salary_min": 150000,
  "salary_max": 190000,
  "requirements": [
    "Python 3.10+",
    "FastAPI experience",
    "MongoDB knowledge",
    "REST API design",
    "4+ years backend development"
  ]
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Job updated successfully",
  "data": {
    "id": "65d4a2c8f1e2a3b4c5d6e7f8",
    "job_title": "Senior Backend Engineer",
    "salary_min": 150000,
    "salary_max": 190000,
    "updated_at": "2024-04-15T10:45:00Z"
  }
}
```

**Error Response:** `400 Bad Request`
```json
{
  "status": "error",
  "message": "Job cannot be edited in PUBLISHED status"
}
```

---

### 5. Generate AI Suggestions

**Endpoint:** `POST /jobs/suggestions/{job_id}`

**Description:** Generates AI-powered suggestions for job requirements and description using Google Gemini.

**Path Parameters:**
- `job_id` (string, required): MongoDB ObjectId of the job

**Query Parameters:**
- `use_gemini` (boolean): Use Google Gemini AI (default: true)

**Response:** `200 OK` (streaming)
```json
{
  "status": "success",
  "message": "Processing suggestions...",
  "suggestions": {
    "enhanced_description": "Looking for a skilled Senior Backend Developer with strong foundation in async Python development...",
    "suggested_requirements": [
      "Mastery of Python async/await patterns and asyncio framework",
      "5+ years professional backend development experience",
      "Proven expertise with FastAPI framework and RESTful API design",
      "Advanced MongoDB data modeling and query optimization",
      "Docker containerization and Kubernetes orchestration experience",
      "Understanding of microservices architecture",
      "Experience with CI/CD pipelines"
    ],
    "suggested_skills": [
      "Python",
      "AsyncIO",
      "FastAPI",
      "MongoDB",
      "Docker",
      "Kubernetes",
      "PostgreSQL",
      "REST APIs"
    ],
    "missing_fields": [
      "salary_range",
      "benefits_description"
    ],
    "improvement_score": 0.92
  }
}
```

**Error Response:** `503 Service Unavailable`
```json
{
  "status": "error",
  "message": "AI service temporarily unavailable"
}
```

---

### 6. Apply AI Suggestions

**Endpoint:** `POST /jobs/apply-suggestions`

**Description:** Applies selected AI suggestions to a job.

**Request:**
```json
{
  "job_id": "65d4a2c8f1e2a3b4c5d6e7f8",
  "suggestions_to_apply": {
    "enhanced_description": true,
    "suggested_requirements": true,
    "suggested_skills": true
  }
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Suggestions applied successfully",
  "data": {
    "id": "65d4a2c8f1e2a3b4c5d6e7f8",
    "status": "REVIEWING",
    "updated_at": "2024-04-15T11:00:00Z",
    "applied_suggestions_count": 3
  }
}
```

---

### 7. Finalize Job (Complete Posting)

**Endpoint:** `POST /jobs/finalize/{job_id}`

**Description:** Finalizes job posting - generates vector embeddings for semantic matching.

**Path Parameters:**
- `job_id` (string, required): MongoDB ObjectId of the job

**Request:**
```json
{
  "confirm": true
}
```

**Response:** `200 OK` (webhook-based, WebSocket notification sent)
```json
{
  "status": "success",
  "message": "Job finalized successfully",
  "data": {
    "id": "65d4a2c8f1e2a3b4c5d6e7f8",
    "status": "FINALIZED",
    "embedding_generated": true,
    "ready_for_publish": true,
    "updated_at": "2024-04-15T11:05:00Z"
  }
}
```

**WebSocket Notification:**
```json
{
  "event": "job_finalized",
  "job_id": "65d4a2c8f1e2a3b4c5d6e7f8",
  "status": "FINALIZED",
  "timestamp": "2024-04-15T11:05:00Z"
}
```

---

### 8. Publish Job

**Endpoint:** `POST /jobs/publish/{job_id}`

**Description:** Publishes finalized job and triggers candidate matching.

**Path Parameters:**
- `job_id` (string, required): MongoDB ObjectId of the job

**Request:**
```json
{
  "confirm": true,
  "notify_candidates": true
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Job published successfully",
  "data": {
    "id": "65d4a2c8f1e2a3b4c5d6e7f8",
    "status": "PUBLISHED",
    "published_at": "2024-04-15T11:10:00Z",
    "candidate_match_initiated": true,
    "estimated_matches": 5
  }
}
```

**WebSocket Notification:**
```json
{
  "event": "job_published",
  "job_id": "65d4a2c8f1e2a3b4c5d6e7f8",
  "status": "PUBLISHED",
  "candidates_notified": true,
  "timestamp": "2024-04-15T11:10:00Z"
}
```

---

### 9. Delete Job

**Endpoint:** `DELETE /jobs/{job_id}`

**Description:** Deletes a job (only in DRAFT status).

**Path Parameters:**
- `job_id` (string, required): MongoDB ObjectId of the job

**Request:**
```
DELETE /jobs/65d4a2c8f1e2a3b4c5d6e7f8
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Job deleted successfully"
}
```

**Error Response:** `400 Bad Request`
```json
{
  "status": "error",
  "message": "Can only delete jobs in DRAFT status"
}
```

---

### 10. Archive Job

**Endpoint:** `POST /jobs/archive/{job_id}`

**Description:** Archives a published job (stops showing in active listings).

**Path Parameters:**
- `job_id` (string, required): MongoDB ObjectId of the job

**Request:**
```json
{
  "archive_reason": "Position filled",
  "notify_candidates": true
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Job archived successfully",
  "data": {
    "id": "65d4a2c8f1e2a3b4c5d6e7f8",
    "status": "ARCHIVED",
    "archived_at": "2024-04-15T12:00:00Z",
    "candidates_notified": true
  }
}
```

---

## Candidate Management Endpoints

### 11. Upload Resume/Upload Candidate

**Endpoint:** `POST /candidates/upload`

**Description:** Uploads candidate resume and creates candidate profile.

**Headers:**
```
Content-Type: multipart/form-data
```

**Request Data:**
```
file: [PDF/DOCX file, max 10MB]
candidate_name: "John Doe"
candidate_email: "john@example.com"
candidate_phone: "+1-555-0123"
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Resume uploaded successfully",
  "candidate": {
    "id": "65d4a3d9f1e2a3b4c5d6e8f9",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "resume_stored": true,
    "resume_id": "65d4a3d9f1e2a3b4c5d6e9fa",
    "created_at": "2024-04-15T10:15:00Z",
    "embedding_generated": false
  }
}
```

**Error Response:** `413 Payload Too Large`
```json
{
  "status": "error",
  "message": "File size exceeds 10MB limit"
}
```

---

### 12. Get Candidate Details

**Endpoint:** `GET /candidates/{candidate_id}`

**Description:** Retrieves complete candidate profile and resume information.

**Path Parameters:**
- `candidate_id` (string, required): MongoDB ObjectId of the candidate

**Response:** `200 OK`
```json
{
  "status": "success",
  "data": {
    "id": "65d4a3d9f1e2a3b4c5d6e8f9",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "resume_stored": true,
    "resume_id": "65d4a3d9f1e2a3b4c5d6e9fa",
    "extracted_skills": [
      "Python",
      "FastAPI",
      "MongoDB",
      "Docker",
      "AWS"
    ],
    "experience_years": 6,
    "education": [
      {
        "degree": "B.S. Computer Science",
        "school": "State University",
        "graduation_year": 2018
      }
    ],
    "created_at": "2024-04-15T10:15:00Z",
    "updated_at": "2024-04-15T10:15:00Z",
    "matched_jobs": [
      {
        "job_id": "65d4a2c8f1e2a3b4c5d6e7f8",
        "job_title": "Senior Backend Developer",
        "match_score": 0.92
      }
    ]
  }
}
```

---

## Job Requirements Endpoints

### 13. Get Job Requirements

**Endpoint:** `GET /requirements`

**Description:** Retrieves all job requirements with optional filtering.

**Query Parameters:**
- `job_id` (string): Filter by specific job
- `skill` (string): Filter by skill name
- `experience_level` (string): Filter by level (Junior, Mid, Senior)

**Response:** `200 OK`
```json
{
  "status": "success",
  "data": [
    {
      "id": "65d4a4e0f1e2a3b4c5d6e10g",
      "job_id": "65d4a2c8f1e2a3b4c5d6e7f8",
      "requirement_text": "5+ years Python development experience",
      "requirement_type": "experience",
      "priority": "high",
      "matched_candidates": []
    }
  ],
  "total": 15
}
```

---

## Analytics Endpoints

### 14. Get Job Analytics

**Endpoint:** `GET /analytics/jobs/{job_id}`

**Description:** Retrieves analytics and statistics for a specific job.

**Path Parameters:**
- `job_id` (string, required): MongoDB ObjectId of the job

**Response:** `200 OK`
```json
{
  "status": "success",
  "data": {
    "job_id": "65d4a2c8f1e2a3b4c5d6e7f8",
    "job_title": "Senior Backend Developer",
    "status": "PUBLISHED",
    "views": 245,
    "clicks": 65,
    "applications": 12,
    "qualified_candidates": 8,
    "match_scores": {
      "average": 0.81,
      "highest": 0.98,
      "distribution": {
        "0.9-1.0": 3,
        "0.8-0.9": 5,
        "0.7-0.8": 4,
        "below_0.7": 0
      }
    },
    "timeline": {
      "created_at": "2024-04-15T10:30:00Z",
      "published_at": "2024-04-15T11:10:00Z",
      "time_to_publish_hours": 0.67,
      "days_published": 3
    }
  }
}
```

---

### 15. Get Platform Analytics

**Endpoint:** `GET /analytics/platform`

**Description:** Retrieves overall platform statistics.

**Query Parameters:**
- `period` (string): Time period (day, week, month, all)

**Response:** `200 OK`
```json
{
  "status": "success",
  "data": {
    "period": "month",
    "jobs": {
      "total": 45,
      "published": 32,
      "drafts": 8,
      "archived": 5,
      "created_this_period": 12
    },
    "candidates": {
      "total": 187,
      "registered_this_period": 34,
      "with_matching_jobs": 156,
      "average_match_score": 0.79
    },
    "matches": {
      "total_matches": 234,
      "high_quality_matches": 187,
      "average_match_score": 0.82
    },
    "activity": {
      "jobs_published": 12,
      "candidates_added": 34,
      "matches_generated": 89,
      "interviews_scheduled": 23
    }
  }
}
```

---

## WebSocket Events

### Real-Time Job Status Updates

**Connection URL:**
```
ws://127.0.0.1:8000/ws/jobs/{job_id}
```

**Events:**

1. **Job Status Change:**
```json
{
  "event": "job_status_changed",
  "job_id": "65d4a2c8f1e2a3b4c5d6e7f8",
  "old_status": "DRAFT",
  "new_status": "REVIEWING",
  "timestamp": "2024-04-15T10:45:00Z"
}
```

2. **AI Processing Progress:**
```json
{
  "event": "ai_processing",
  "job_id": "65d4a2c8f1e2a3b4c5d6e7f8",
  "progress": 75,
  "status": "Generating suggestions...",
  "timestamp": "2024-04-15T10:50:00Z"
}
```

3. **Candidate Match Found:**
```json
{
  "event": "candidate_matched",
  "job_id": "65d4a2c8f1e2a3b4c5d6e7f8",
  "candidate_id": "65d4a3d9f1e2a3b4c5d6e8f9",
  "candidate_name": "John Doe",
  "match_score": 0.92,
  "timestamp": "2024-04-15T11:15:00Z"
}
```

4. **Error Notification:**
```json
{
  "event": "error",
  "job_id": "65d4a2c8f1e2a3b4c5d6e7f8",
  "error_message": "Vector embedding generation failed",
  "timestamp": "2024-04-15T11:20:00Z"
}
```

---

## Error Responses

### Standard Error Format

All error responses follow this format:

```json
{
  "status": "error",
  "message": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "details": {
    "field": "Additional error information"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Job retrieved successfully |
| 201 | Created | Job created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Session expired or invalid |
| 403 | Forbidden | Cannot access this resource |
| 404 | Not Found | Job not found |
| 409 | Conflict | Operation conflicts with current state |
| 413 | Payload Too Large | File too large for upload |
| 422 | Unprocessable Entity | Validation error in request |
| 500 | Server Error | Internal server error |
| 503 | Service Unavailable | Service temporarily down |

---

## Rate Limiting

Current rate limits (may change):
- 100 requests per minute per IP
- 50 requests per minute for upload endpoints
- WebSocket connections: 10 concurrent per user

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1713180000
```

---

## Request/Response Examples

### Complete Job Creation Workflow

1. Create job:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Tech Company",
    "job_title": "Backend Developer",
    "job_description": "We need a backend developer...",
    "requirements": ["Python", "FastAPI"],
    "skills": ["Python", "FastAPI"],
    "experience_level": "Senior",
    "location": "New York, NY"
  }'
```

2. Get suggestions:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/jobs/[JOB_ID]/suggestions
```

3. Apply suggestions:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/jobs/apply-suggestions \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "[JOB_ID]",
    "suggestions_to_apply": {
      "suggested_requirements": true
    }
  }'
```

4. Finalize and publish:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/jobs/[JOB_ID]/finalize \
  -H "Content-Type: application/json" \
  -d '{"confirm": true}'

curl -X POST http://127.0.0.1:8000/api/v1/jobs/[JOB_ID]/publish \
  -H "Content-Type: application/json" \
  -d '{"confirm": true}'
```

---

## API Development Notes

- All timestamps are in ISO 8601 format (UTC)
- All monetary values in USD
- All IDs are MongoDB ObjectIds (24-character hex strings)
- Pagination defaults: skip=0, limit=10
- Maximum limit: 100 records per request

---

Last Updated: April 2026
