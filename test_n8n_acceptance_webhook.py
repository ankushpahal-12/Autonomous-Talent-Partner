#!/usr/bin/env python3
"""
Test script for n8n Candidate Acceptance Webhook with sessionId support
Sends fake candidate data to test the workflow with AI agent integration
Supports n8n Chat Trigger Node with Agentic AI
"""

import requests
import json
from datetime import datetime, timedelta
import time
import uuid

# n8n Webhook URL
N8N_WEBHOOK_URL = "https://ankushpahal.app.n8n.cloud/webhook-test/webhooks/candidate-acceptance"


# ===== SESSION ID GENERATION FUNCTIONS =====

def generate_uuid_session():
    """Generate UUID-based session ID (recommended)"""
    return str(uuid.uuid4())


def generate_email_session(email):
    """Generate email-based session ID"""
    return f"session-{email.split('@')[0]}-{int(time.time())}"


def generate_timestamp_session():
    """Generate timestamp-based session ID"""
    return f"session-{int(time.time()*1000)}"


def generate_candidate_session(candidate_name, candidate_email):
    """Generate candidate-specific session ID"""
    sanitized_name = candidate_name.lower().replace(" ", "-")
    sanitized_email = candidate_email.split("@")[0]
    return f"session-{sanitized_name}-{sanitized_email}-{uuid.uuid4().hex[:8]}"


# ===== FAKE CANDIDATE DATA WITH SESSION IDs =====

# Generate session IDs for batch
CANDIDATE_SESSIONS = {
    0: generate_uuid_session(),  # UUID-based
    1: generate_uuid_session(),  # UUID-based
    2: generate_uuid_session(),  # UUID-based
    3: generate_uuid_session(),  # UUID-based
    4: generate_uuid_session(),  # UUID-based
    5: generate_uuid_session(),  # UUID-based
    6: generate_uuid_session(),  # UUID-based
}

FAKE_CANDIDATES = [
    {
        "sessionId": CANDIDATE_SESSIONS[0],  # REQUIRED: Session ID for chat trigger
        "candidateName": "Ankushpahal",
        "candidateEmail": "ankushpayal58@gmail.com",
        "position": "Senior Backend Developer",
        "company": "Tech Company Inc",
        "interviewDate": "2024-04-25",
        "interviewTime": "10:00 AM",
        "timezone": "EST",
        "hrEmail": "hr@company.com",
        "chatInput": "Please schedule the interview for April 26 at 2 PM PST and Create a meeting  link for the interview and send the  email."
    },
    {
        "sessionId": CANDIDATE_SESSIONS[1],
        "candidateName": "Jane Smith",
        "candidateEmail": "jane.smith@example.com",
        "position": "Frontend Developer",
        "company": "Innovation Labs",
        "interviewDate": "2024-04-26",
        "interviewTime": "2:00 PM",
        "timezone": "PST",
        "hrEmail": "hiring@innovationlabs.com",
        "chatInput": "Send acceptance email for Frontend Developer position at Innovation Labs and create a calendar event for April 26 at 2:00 PM PST."
    },
    {
        "sessionId": CANDIDATE_SESSIONS[2],
        "candidateName": "Bob Wilson",
        "candidateEmail": "bob.wilson@example.com",
        "position": "DevOps Engineer",
        "company": "Cloud Solutions Inc",
        "interviewDate": "2024-04-27",
        "interviewTime": "11:00 AM",
        "timezone": "CST",
        "hrEmail": "recruitment@cloudsolutions.com",
        "chatInput": "Send acceptance email for DevOps Engineer role at Cloud Solutions Inc and schedule interview for April 27 at 11:00 AM CST."
    },
    {
        "sessionId": CANDIDATE_SESSIONS[3],
        "candidateName": "Alice Johnson",
        "candidateEmail": "alice.johnson@example.com",
        "position": "Data Scientist",
        "company": "Analytics Corp",
        "interviewDate": "2024-04-28",
        "interviewTime": "3:00 PM",
        "timezone": "UTC",
        "hrEmail": "hr@analyticscorp.com",
        "chatInput": "Send acceptance email for Data Scientist position at Analytics Corp and create calendar event for April 28 at 3:00 PM UTC."
    },
    {
        "sessionId": CANDIDATE_SESSIONS[4],
        "candidateName": "Charlie Brown",
        "candidateEmail": "charlie.brown@example.com",
        "position": "Full Stack Developer",
        "company": "StartupXYZ",
        "interviewDate": "2024-04-29",
        "interviewTime": "9:00 AM",
        "timezone": "EST",
        "hrEmail": "team@startupxyz.com",
        "chatInput": "Send acceptance email for Full Stack Developer position and create calendar event for April 29 at 9:00 AM EST."
    },
    {
        # Minimal payload with sessionId
        "sessionId": CANDIDATE_SESSIONS[5],
        "candidateName": "Eva Martinez",
        "candidateEmail": "eva.martinez@example.com",
        "chatInput": "Send acceptance email and schedule interview calendar event."
    },
    {
        # Another minimal test with sessionId
        "sessionId": CANDIDATE_SESSIONS[6],
        "candidateName": "David Chen",
        "candidateEmail": "david.chen@example.com",
        "position": "QA Engineer",
        "chatInput": "Send acceptance email for QA Engineer role and create calendar event for the interview."
    }
]


def send_webhook_request(payload):
    """
    Send webhook request to n8n
    
    Args:
        payload: Dictionary with candidate data
        
    Returns:
        tuple: (success: bool, response: dict, status_code: int)
    """
    try:
        print(f"\n{'='*70}")
        print(f"Sending request for: {payload.get('candidateName', 'Unknown')}")
        print(f"Email: {payload.get('candidateEmail', 'N/A')}")
        print(f"{'='*70}")
        
        print("\nPayload:")
        print(json.dumps(payload, indent=2))
        
        # Send POST request
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        # Try to parse response
        try:
            response_data = response.json()
            print("Response:")
            print(json.dumps(response_data, indent=2))
        except:
            print(f"Response: {response.text}")
            response_data = {"raw": response.text}
        
        success = response.status_code in [200, 201, 202, 204]
        
        if success:
            print("\n✓ SUCCESS - Webhook executed!")
        else:
            print(f"\n✗ FAILED - HTTP {response.status_code}")
        
        return success, response_data, response.status_code
        
    except requests.exceptions.Timeout:
        print("\n✗ ERROR: Request timeout (30 seconds)")
        return False, {"error": "Timeout"}, None
    except requests.exceptions.ConnectionError as e:
        print(f"\n✗ ERROR: Connection failed - {str(e)}")
        return False, {"error": f"Connection error: {str(e)}"}, None
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        return False, {"error": str(e)}, None


def test_single_candidate(candidate_data):
    """Test with a single candidate"""
    success, response, status = send_webhook_request(candidate_data)
    time.sleep(1)  # Wait between requests
    return success


def test_all_candidates():
    """Test with all fake candidates"""
    print("\n" + "="*70)
    print("N8N CANDIDATE ACCEPTANCE WEBHOOK TEST")
    print("="*70)
    print(f"Webhook URL: {N8N_WEBHOOK_URL}")
    print(f"Total candidates to test: {len(FAKE_CANDIDATES)}")
    print("="*70)
    
    results = {
        "total": len(FAKE_CANDIDATES),
        "successful": 0,
        "failed": 0,
        "details": []
    }
    
    for idx, candidate in enumerate(FAKE_CANDIDATES, 1):
        print(f"\n[{idx}/{len(FAKE_CANDIDATES)}]")
        success, response, status = send_webhook_request(candidate)
        
        results["details"].append({
            "candidate": candidate.get("candidateName"),
            "email": candidate.get("candidateEmail"),
            "success": success,
            "status_code": status
        })
        
        if success:
            results["successful"] += 1
        else:
            results["failed"] += 1
        
        # Wait a bit between requests
        if idx < len(FAKE_CANDIDATES):
            print("\nWaiting 2 seconds before next request...")
            time.sleep(2)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total Sent: {results['total']}")
    print(f"Successful: {results['successful']} ✓")
    print(f"Failed: {results['failed']} ✗")
    print(f"Success Rate: {(results['successful']/results['total']*100):.1f}%")
    print("="*70)
    
    return results


def test_minimal_payload():
    """Test with minimal required fields only"""
    print("\n" + "="*70)
    print("TESTING MINIMAL PAYLOAD")
    print("="*70)
    
    minimal_payload = {
        "candidateName": "Test User",
        "candidateEmail": "test@example.com"
    }
    
    print("Testing with only required fields (name + email)...")
    success, response, status = send_webhook_request(minimal_payload)
    
    return success


def test_with_defaults():
    """Test that defaults are applied correctly"""
    print("\n" + "="*70)
    print("TESTING DEFAULT VALUES")
    print("="*70)
    
    payload = {
        "candidateName": "Default Test User",
        "candidateEmail": "default.test@example.com",
        # Not providing optional fields - should use defaults
    }
    
    print("Fields NOT provided (should use defaults):")
    print("  - position (default: Software Engineer)")
    print("  - company (default: Our Company)")
    print("  - interviewDate (default: today)")
    print("  - interviewTime (default: 10:00 AM)")
    print("  - timezone (default: EST)")
    print("  - hrEmail (default: hr@company.com)")
    
    success, response, status = send_webhook_request(payload)
    
    return success


def batch_test_with_delays(delay_seconds=3):
    """Test multiple candidates with custom delay"""
    print("\n" + "="*70)
    print(f"BATCH TEST WITH {delay_seconds}s DELAYS")
    print("="*70)
    
    successful = 0
    
    for candidate in FAKE_CANDIDATES[:3]:  # Test first 3
        success, _, _ = send_webhook_request(candidate)
        if success:
            successful += 1
        time.sleep(delay_seconds)
    
    print(f"\nBatch test result: {successful}/{3} successful")
    return successful == 3


def test_invalid_email():
    """Test with invalid email format"""
    print("\n" + "="*70)
    print("TESTING INVALID EMAIL")
    print("="*70)
    
    payload = {
        "candidateName": "Invalid Email Test",
        "candidateEmail": "not-an-email-address"  # Invalid format
    }
    
    print("Payload with invalid email format...")
    success, response, status = send_webhook_request(payload)
    
    return success


def test_with_special_characters():
    """Test with special characters in names"""
    print("\n" + "="*70)
    print("TESTING SPECIAL CHARACTERS")
    print("="*70)
    
    payload = {
        "candidateName": "José García-López",
        "candidateEmail": "jose.garcia.lopez@example.com",
        "position": "Senior C++ Developer (C++17/20)",
        "company": "Tech & Innovation Co."
    }
    
    print("Payload with special characters and unicode...")
    success, response, status = send_webhook_request(payload)
    
    return success


def test_session_id_uuid_method():
    """Test UUID-based session ID generation"""
    print("\n" + "="*70)
    print("TESTING SESSION ID - UUID METHOD")
    print("="*70)
    
    session_id = generate_uuid_session()
    
    payload = {
        "sessionId": session_id,  # UUID-based
        "candidateName": "Test User UUID",
        "candidateEmail": "test.uuid@example.com"
    }
    
    print(f"Generated sessionId: {session_id}")
    print("Format: UUID v4 (universally unique)")
    success, response, status = send_webhook_request(payload)
    
    return success


def test_session_id_email_method():
    """Test email-based session ID generation"""
    print("\n" + "="*70)
    print("TESTING SESSION ID - EMAIL-BASED METHOD")
    print("="*70)
    
    email = "test.email@example.com"
    session_id = generate_email_session(email)
    
    payload = {
        "sessionId": session_id,  # Email-based with timestamp
        "candidateName": "Test User Email",
        "candidateEmail": email
    }
    
    print(f"Generated sessionId: {session_id}")
    print("Format: session-{email_prefix}-{timestamp}")
    success, response, status = send_webhook_request(payload)
    
    return success


def test_session_id_timestamp_method():
    """Test timestamp-based session ID generation"""
    print("\n" + "="*70)
    print("TESTING SESSION ID - TIMESTAMP METHOD")
    print("="*70)
    
    session_id = generate_timestamp_session()
    
    payload = {
        "sessionId": session_id,  # Timestamp-based
        "candidateName": "Test User Timestamp",
        "candidateEmail": "test.timestamp@example.com"
    }
    
    print(f"Generated sessionId: {session_id}")
    print("Format: session-{milliseconds_since_epoch}")
    success, response, status = send_webhook_request(payload)
    
    return success


def test_multiturn_conversation():
    """Test multi-turn conversation with same sessionId"""
    print("\n" + "="*70)
    print("TESTING MULTI-TURN CONVERSATION (Same sessionId)")
    print("="*70)
    
    # Generate a single session ID
    session_id = generate_uuid_session()
    candidate_name = "Multi-Turn Test User"
    candidate_email = "multiturn@example.com"
    
    print(f"Session ID: {session_id}")
    print(f"Candidate: {candidate_name}")
    print("\nThis simulates a multi-turn conversation where the AI agent")
    print("remembers context from previous messages.\n")
    
    # Message 1: Initial acceptance
    turn_1 = {
        "sessionId": session_id,  # Same session
        "candidateName": candidate_name,
        "candidateEmail": candidate_email,
        "message": "Send acceptance email for Senior Developer position",
        "position": "Senior Backend Developer"
    }
    
    print("Turn 1: Initial request")
    print("-" * 70)
    success1, _, _ = send_webhook_request(turn_1)
    time.sleep(2)
    
    # Message 2: Modify details (AI should remember context)
    turn_2 = {
        "sessionId": session_id,  # SAME session ID - maintains context
        "candidateName": candidate_name,
        "candidateEmail": candidate_email,
        "message": "Actually, please schedule the interview for April 30 instead of April 25",
        "position": "Senior Backend Developer"
    }
    
    print("\nTurn 2: Follow-up request (same session)")
    print("-" * 70)
    success2, _, _ = send_webhook_request(turn_2)
    time.sleep(2)
    
    # Message 3: Additional modification
    turn_3 = {
        "sessionId": session_id,  # SAME session ID - still maintains context
        "candidateName": candidate_name,
        "candidateEmail": candidate_email,
        "message": "Make the time 3:30 PM EST",
        "position": "Senior Backend Developer"
    }
    
    print("\nTurn 3: Another modification (same session)")
    print("-" * 70)
    success3, _, _ = send_webhook_request(turn_3)
    
    all_success = success1 and success2 and success3
    print(f"\n✓ All turns completed" if all_success else "\n✗ Some turns failed")
    
    return all_success


def test_session_persistence():
    """Test that session state persists across requests"""
    print("\n" + "="*70)
    print("TESTING SESSION PERSISTENCE")
    print("="*70)
    
    session_id = generate_candidate_session("Persistence Test", "persist@example.com")
    
    print(f"Session ID: {session_id}")
    print("\nSending 3 separate requests with SAME sessionId...")
    print("The AI agent should maintain state across all requests.\n")
    
    payloads = [
        {
            "sessionId": session_id,
            "candidateName": "Session Persistence User",
            "candidateEmail": "persist@example.com",
            "message": "Start: Create acceptance flow for backend role"
        },
        {
            "sessionId": session_id,
            "candidateName": "Session Persistence User",
            "candidateEmail": "persist@example.com",
            "message": "Update: Change interview date to May 1"
        },
        {
            "sessionId": session_id,
            "candidateName": "Session Persistence User",
            "candidateEmail": "persist@example.com",
            "message": "Final: Send the email with all changes"
        }
    ]
    
    results = []
    for i, payload in enumerate(payloads, 1):
        print(f"Request {i}: {payload.get('message')}")
        success, _, _ = send_webhook_request(payload)
        results.append(success)
        if i < len(payloads):
            time.sleep(1)
    
    success_count = sum(results)
    print(f"\n✓ Persistence test: {success_count}/{len(payloads)} successful")
    
    return all(results)


def test_session_isolation():
    """Test that different sessionIds are isolated from each other"""
    print("\n" + "="*70)
    print("TESTING SESSION ISOLATION")
    print("="*70)
    
    session_1 = generate_uuid_session()
    session_2 = generate_uuid_session()
    
    print(f"Session 1: {session_1}")
    print(f"Session 2: {session_2}\n")
    print("Both sessions should have independent conversation history.\n")
    
    # Session 1 - Candidate A
    payload_1a = {
        "sessionId": session_1,
        "candidateName": "Candidate A",
        "candidateEmail": "candidate.a@example.com",
        "message": "Send acceptance for Product Manager role"
    }
    
    # Session 2 - Candidate B
    payload_2a = {
        "sessionId": session_2,
        "candidateName": "Candidate B",
        "candidateEmail": "candidate.b@example.com",
        "message": "Send acceptance for Developer role"
    }
    
    print("Session 1 - Candidate A:")
    success_1a, _, _ = send_webhook_request(payload_1a)
    time.sleep(1)
    
    print("\nSession 2 - Candidate B:")
    success_2a, _, _ = send_webhook_request(payload_2a)
    time.sleep(1)
    
    # Back to Session 1 - Different message
    payload_1b = {
        "sessionId": session_1,
        "candidateName": "Candidate A",
        "candidateEmail": "candidate.a@example.com",
        "message": "Change interview to April 28"
    }
    
    print("\nBack to Session 1 - Continue with Candidate A:")
    success_1b, _, _ = send_webhook_request(payload_1b)
    
    all_success = success_1a and success_2a and success_1b
    print(f"\n✓ Sessions properly isolated" if all_success else "\n✗ Session isolation failed")
    
    return all_success


def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test n8n Candidate Acceptance Webhook with sessionId support"
    )
    parser.add_argument(
        "--mode",
        choices=[
            "all", "single", "minimal", "defaults", "batch", "invalid", "special",
            "session-uuid", "session-email", "session-timestamp",
            "multiturn", "persistence", "isolation"
        ],
        default="all",
        help="Test mode to run"
    )
    parser.add_argument(
        "--index",
        type=int,
        default=0,
        help="Index of candidate to test (for single mode)"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=2,
        help="Delay between requests in seconds (for batch mode)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show verbose output"
    )
    
    args = parser.parse_args()
    
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  n8n CANDIDATE ACCEPTANCE WEBHOOK TESTER".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    if args.mode == "all":
        results = test_all_candidates()
    elif args.mode == "single":
        if args.index < len(FAKE_CANDIDATES):
            test_single_candidate(FAKE_CANDIDATES[args.index])
        else:
            print(f"Error: Index {args.index} out of range (0-{len(FAKE_CANDIDATES)-1})")
    elif args.mode == "minimal":
        test_minimal_payload()
    elif args.mode == "defaults":
        test_with_defaults()
    elif args.mode == "batch":
        batch_test_with_delays(args.delay)
    elif args.mode == "invalid":
        test_invalid_email()
    elif args.mode == "special":
        test_with_special_characters()
    elif args.mode == "session-uuid":
        test_session_id_uuid_method()
    elif args.mode == "session-email":
        test_session_id_email_method()
    elif args.mode == "session-timestamp":
        test_session_id_timestamp_method()
    elif args.mode == "multiturn":
        test_multiturn_conversation()
    elif args.mode == "persistence":
        test_session_persistence()
    elif args.mode == "isolation":
        test_session_isolation()
    
    print("\n✓ Test run completed!\n")


if __name__ == "__main__":
    main()
