# Implementation - Trigger n8n Workflows from Frontend

Quick guide for integrating n8n workflow triggers into your React frontend.

## Overview

Send candidate acceptance/rejection notifications directly from frontend buttons using n8n webhooks.

---

## 1. Create API Service Module

**File: `src/api/n8n.js`**

```javascript
/**
 * Service to trigger n8n workflows
 */

const N8N_BASE_URL = process.env.REACT_APP_N8N_URL || 'http://localhost:5678';

const WORKFLOWS = {
  ACCEPTANCE: '/webhook/candidate-acceptance',
  REJECTION: '/webhook/candidate-rejection',
  INTERVIEW: '/webhook/interview-scheduler',
};

/**
 * Send candidate acceptance notification
 * @param {string} candidateName - Full name
 * @param {string} candidateEmail - Email address
 * @param {object} options - Optional: position, company, interviewDate, interviewTime, timezone
 */
export const sendAcceptance = async (candidateName, candidateEmail, options = {}) => {
  const payload = {
    candidateName,
    candidateEmail,
    position: options.position || 'Software Engineer',
    company: options.company || 'Our Company',
    interviewDate: options.interviewDate || new Date().toISOString().split('T')[0],
    interviewTime: options.interviewTime || '10:00 AM',
    timezone: options.timezone || 'EST',
    hrEmail: options.hrEmail || 'hr@company.com',
  };

  try {
    const response = await fetch(`${N8N_BASE_URL}${WORKFLOWS.ACCEPTANCE}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to send acceptance:', error);
    throw error;
  }
};

/**
 * Send candidate rejection notification
 * @param {string} candidateName - Full name
 * @param {string} candidateEmail - Email address
 * @param {string} position - Position applied for
 * @param {string} feedback - Rejection feedback
 * @param {boolean} inviteReapply - Allow reapplication
 */
export const sendRejection = async (
  candidateName,
  candidateEmail,
  position,
  feedback,
  inviteReapply = true
) => {
  const payload = {
    candidateName,
    candidateEmail,
    position,
    feedback,
    inviteReapply,
    reapplyEligibilityMonths: 6,
  };

  try {
    const response = await fetch(`${N8N_BASE_URL}${WORKFLOWS.REJECTION}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to send rejection:', error);
    throw error;
  }
};

/**
 * Schedule interview and send confirmation
 */
export const scheduleInterview = async (
  candidateId,
  candidateName,
  candidateEmail,
  position,
  interviewDate,
  interviewTime,
  interviewerName,
  timezone = 'EST'
) => {
  const payload = {
    candidateId,
    candidateName,
    candidateEmail,
    position,
    interviewDate,
    interviewTime,
    interviewerName,
    timezone,
  };

  try {
    const response = await fetch(`${N8N_BASE_URL}${WORKFLOWS.INTERVIEW}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to schedule interview:', error);
    throw error;
  }
};
```

---

## 2. Update Candidate Detail Component

**File: `src/components/EnhancedCandidateDetail.jsx`**

```javascript
import React, { useState } from 'react';
import { sendAcceptance, sendRejection, scheduleInterview } from '../api/n8n';

export const EnhancedCandidateDetail = ({ candidate, onUpdate }) => {
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);
  const [showAcceptanceModal, setShowAcceptanceModal] = useState(false);
  const [interviewDetails, setInterviewDetails] = useState({
    date: '',
    time: '10:00 AM',
    timezone: 'EST',
  });

  // Show notification message
  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000);
  };

  // Handle candidate acceptance
  const handleAcceptance = async () => {
    setLoading(true);
    try {
      const response = await sendAcceptance(
        candidate.parsed_data.name,
        candidate.parsed_data.email,
        {
          position: candidate.position,
          company: candidate.company || 'Our Company',
          interviewDate: interviewDetails.date,
          interviewTime: interviewDetails.time,
          timezone: interviewDetails.timezone,
        }
      );

      // Update local state
      onUpdate({
        ...candidate,
        status: 'ACCEPTED',
        interview_details: interviewDetails,
      });

      showNotification(
        `Acceptance notification sent to ${candidate.parsed_data.email}`,
        'success'
      );
      setShowAcceptanceModal(false);
    } catch (error) {
      showNotification(
        `Failed to send acceptance: ${error.message}`,
        'error'
      );
    } finally {
      setLoading(false);
    }
  };

  // Handle candidate rejection
  const handleRejection = async () => {
    const feedback = prompt(
      'Enter feedback for rejection (optional):',
      'Thank you for your interest. We will keep your profile for future opportunities.'
    );

    if (feedback !== null) {
      setLoading(true);
      try {
        const response = await sendRejection(
          candidate.parsed_data.name,
          candidate.parsed_data.email,
          candidate.position,
          feedback,
          true // Allow reapplication
        );

        // Update local state
        onUpdate({
          ...candidate,
          status: 'REJECTED',
          rejection_feedback: feedback,
        });

        showNotification(
          `Rejection notification sent to ${candidate.parsed_data.email}`,
          'success'
        );
      } catch (error) {
        showNotification(
          `Failed to send rejection: ${error.message}`,
          'error'
        );
      } finally {
        setLoading(false);
      }
    }
  };

  // Render acceptance modal
  const AcceptanceModal = () => (
    <div className="modal">
      <div className="modal-content">
        <h3>Schedule Interview</h3>
        
        <div className="form-group">
          <label>Interview Date:</label>
          <input
            type="date"
            value={interviewDetails.date}
            onChange={(e) =>
              setInterviewDetails({ ...interviewDetails, date: e.target.value })
            }
            required
          />
        </div>

        <div className="form-group">
          <label>Interview Time:</label>
          <input
            type="time"
            value={interviewDetails.time}
            onChange={(e) =>
              setInterviewDetails({ ...interviewDetails, time: e.target.value })
            }
          />
        </div>

        <div className="form-group">
          <label>Timezone:</label>
          <select
            value={interviewDetails.timezone}
            onChange={(e) =>
              setInterviewDetails({ ...interviewDetails, timezone: e.target.value })
            }
          >
            <option value="EST">EST (Eastern)</option>
            <option value="CST">CST (Central)</option>
            <option value="MST">MST (Mountain)</option>
            <option value="PST">PST (Pacific)</option>
            <option value="UTC">UTC</option>
          </select>
        </div>

        <div className="modal-actions">
          <button
            onClick={handleAcceptance}
            disabled={!interviewDetails.date || loading}
            className="btn-primary"
          >
            {loading ? 'Sending...' : 'Send Acceptance & Schedule'}
          </button>
          <button
            onClick={() => setShowAcceptanceModal(false)}
            className="btn-secondary"
            disabled={loading}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="candidate-detail">
      {/* Notification */}
      {notification && (
        <div className={`notification notification-${notification.type}`}>
          {notification.message}
        </div>
      )}

      {/* Candidate Info */}
      <div className="candidate-info">
        <h2>{candidate.parsed_data.name}</h2>
        <p>Email: {candidate.parsed_data.email}</p>
        <p>Position: {candidate.position}</p>
        <p>Status: {candidate.status}</p>
      </div>

      {/* Action Buttons */}
      <div className="candidate-actions">
        {candidate.status === 'SCREENING' && (
          <>
            <button
              onClick={() => setShowAcceptanceModal(true)}
              className="btn btn-accept"
              disabled={loading}
            >
              ✓ Accept & Schedule Interview
            </button>
            <button
              onClick={handleRejection}
              className="btn btn-reject"
              disabled={loading}
            >
              ✕ Reject
            </button>
          </>
        )}
      </div>

      {/* Modals */}
      {showAcceptanceModal && <AcceptanceModal />}

      {/* Interview Details (if scheduled) */}
      {candidate.interview_details && (
        <div className="interview-details">
          <h4>Interview Scheduled</h4>
          <p>Date: {candidate.interview_details.date}</p>
          <p>Time: {candidate.interview_details.time}</p>
          <p>Timezone: {candidate.interview_details.timezone}</p>
        </div>
      )}
    </div>
  );
};

export default EnhancedCandidateDetail;
```

---

## 3. CSS Styling

**File: `src/components/EnhancedCandidateDetail.css`**

```css
.notification {
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
  font-weight: 500;
  animation: slideDown 0.3s ease-in-out;
}

.notification-success {
  background-color: #d1fae5;
  color: #065f46;
  border-left: 4px solid #10b981;
}

.notification-error {
  background-color: #fee2e2;
  color: #7f1d1d;
  border-left: 4px solid #ef4444;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.modal-content h3 {
  margin-bottom: 20px;
  color: #333;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #0ea5e9;
  box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.1);
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-top: 30px;
}

.btn-primary,
.btn-secondary {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 4px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background-color: #0ea5e9;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0284c7;
}

.btn-primary:disabled {
  background-color: #cbd5e1;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #e5e7eb;
  color: #333;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #d1d5db;
}

.candidate-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.btn-accept {
  background-color: #10b981;
  color: white;
}

.btn-accept:hover:not(:disabled) {
  background-color: #059669;
}

.btn-reject {
  background-color: #ef4444;
  color: white;
}

.btn-reject:hover:not(:disabled) {
  background-color: #dc2626;
}

.interview-details {
  background-color: #f9fafb;
  padding: 20px;
  border-radius: 6px;
  margin-top: 20px;
  border-left: 4px solid #0ea5e9;
}

.interview-details h4 {
  margin-top: 0;
  color: #0ea5e9;
}

.interview-details p {
  margin: 10px 0;
  color: #333;
}
```

---

## 4. Environment Configuration

**File: `.env`**

```env
# n8n Configuration
REACT_APP_N8N_URL=http://localhost:5678
REACT_APP_N8N_CANDIDATE_ACCEPTANCE_WEBHOOK=/webhook/candidate-acceptance
REACT_APP_N8N_CANDIDATE_REJECTION_WEBHOOK=/webhook/candidate-rejection
REACT_APP_N8N_INTERVIEW_SCHEDULER_WEBHOOK=/webhook/interview-scheduler
```

---

## 5. Testing

### Test Acceptance Workflow

```javascript
// In your test or console
import { sendAcceptance } from './api/n8n';

await sendAcceptance('John Doe', 'john@example.com', {
  position: 'Senior Developer',
  company: 'Tech Corp',
  interviewDate: '2024-04-25',
  interviewTime: '2:00 PM',
  timezone: 'EST',
});
```

### With cURL

```bash
curl -X POST http://localhost:5678/webhook/candidate-acceptance \
  -H "Content-Type: application/json" \
  -d '{
    "candidateName": "Jane Smith",
    "candidateEmail": "jane@example.com",
    "position": "Frontend Developer",
    "company": "Startup Inc",
    "interviewDate": "2024-04-22",
    "interviewTime": "11:00 AM",
    "timezone": "PST"
  }'
```

---

## 6. Error Handling

Comprehensive error handling pattern:

```javascript
export const sendAcceptance = async (candidateName, candidateEmail, options = {}) => {
  const payload = { candidateName, candidateEmail, ...options };

  try {
    const response = await fetch(`${N8N_BASE_URL}${WORKFLOWS.ACCEPTANCE}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      timeout: 30000, // 30 second timeout
    });

    // Handle HTTP errors
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.message || `HTTP ${response.status}: ${response.statusText}`
      );
    }

    return await response.json();
  } catch (error) {
    // Log to monitoring service
    console.error('n8n workflow error:', { error, payload });
    
    // Re-throw with user-friendly message
    throw {
      message: 'Failed to send acceptance notification',
      originalError: error.message,
      canRetry: error.code !== 'ERR_INVALID_PAYLOAD',
    };
  }
};
```

---

## 7. Advanced Usage

### Batch Send Acceptances

```javascript
export const sendBulkAcceptances = async (candidates) => {
  const results = await Promise.allSettled(
    candidates.map((c) =>
      sendAcceptance(c.name, c.email, {
        position: c.position,
        interviewDate: c.interview_date,
        interviewTime: c.interview_time,
      })
    )
  );

  return {
    successful: results.filter((r) => r.status === 'fulfilled').length,
    failed: results.filter((r) => r.status === 'rejected').length,
    failures: results.filter((r) => r.status === 'rejected').map((r) => r.reason),
  };
};
```

### Retry Logic

```javascript
export const sendAcceptanceWithRetry = async (
  candidateName,
  candidateEmail,
  options,
  maxRetries = 3
) => {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await sendAcceptance(candidateName, candidateEmail, options);
    } catch (error) {
      if (attempt === maxRetries) throw error;
      
      // Exponential backoff
      const delay = Math.pow(2, attempt) * 1000;
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }
};
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| CORS error | Check n8n CORS settings and webhook URL |
| Timeout | Increase fetch timeout or reduce API latency |
| 404 Not Found | Verify n8n webhook path is correct |
| 500 Server Error | Check n8n workflow execution logs |
| Email not received | Verify Gmail credentials are valid |

---

**Last Updated:** April 2026
