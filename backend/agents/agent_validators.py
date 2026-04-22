"""
Input validation and preprocessing for agent functions.
Ensures data quality and prevents token limit overflows.
"""

import logging
import re
from typing import Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Conservative token estimates: 1 token ≈ 4 characters
TOKEN_RATIO = 4
MAX_TOKENS_PER_REQUEST = 30000  # Keep buffer for output
MAX_RESUME_TOKENS = 20000
MAX_JOB_REQUIREMENT_TOKENS = 5000

@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    error_message: Optional[str] = None
    cleaned_text: Optional[str] = None
    token_count: int = 0

def estimate_tokens(text: str) -> int:
    """
    Estimate token count from text length.
    Conservative estimate: 1 token ≈ 4 characters
    
    Args:
        text: Text to estimate tokens for
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    return len(text) // TOKEN_RATIO

def validate_resume_text(resume_text: str, max_tokens: int = MAX_RESUME_TOKENS) -> ValidationResult:
    """
    Validate resume text for agent processing.
    
    Checks:
    - Not empty
    - Not excessively long
    - Contains reasonable content
    
    Args:
        resume_text: Raw resume text
        max_tokens: Maximum permitted tokens
        
    Returns:
        ValidationResult with cleaned text if valid
    """
    # Check if empty
    if not resume_text or not resume_text.strip():
        return ValidationResult(
            is_valid=False,
            error_message="Resume text is empty"
        )
    
    # Clean whitespace
    cleaned = resume_text.strip()
    
    # Estimate tokens
    token_count = estimate_tokens(cleaned)
    
    # Check token limit
    if token_count > max_tokens:
        return ValidationResult(
            is_valid=False,
            error_message=f"Resume exceeds token limit ({token_count} > {max_tokens}). "
                          f"Please provide a shorter resume or summary.",
            token_count=token_count
        )
    
    # Minimum length check (200 characters minimum)
    if len(cleaned) < 200:
        logger.warning(f"Resume is very short ({len(cleaned)} chars). May produce poor results.")
    
    logger.info(f"Resume validated: {len(cleaned)} chars, ~{token_count} tokens")
    
    return ValidationResult(
        is_valid=True,
        cleaned_text=cleaned,
        token_count=token_count
    )

def validate_job_requirement(job_text: str, max_tokens: int = MAX_JOB_REQUIREMENT_TOKENS) -> ValidationResult:
    """
    Validate job requirement text.
    
    Args:
        job_text: Raw job requirement text
        max_tokens: Maximum permitted tokens
        
    Returns:
        ValidationResult with cleaned text if valid
    """
    if not job_text or not job_text.strip():
        return ValidationResult(
            is_valid=False,
            error_message="Job requirement text is empty"
        )
    
    cleaned = job_text.strip()
    token_count = estimate_tokens(cleaned)
    
    if token_count > max_tokens:
        return ValidationResult(
            is_valid=False,
            error_message=f"Job requirement exceeds token limit ({token_count} > {max_tokens})",
            token_count=token_count
        )
    
    logger.info(f"Job requirement validated: {len(cleaned)} chars, ~{token_count} tokens")
    
    return ValidationResult(
        is_valid=True,
        cleaned_text=cleaned,
        token_count=token_count
    )

def validate_candidate_id(candidate_id: str) -> ValidationResult:
    """
    Validate candidate ID format.
    
    Args:
        candidate_id: Candidate identifier
        
    Returns:
        ValidationResult
    """
    if not candidate_id or not candidate_id.strip():
        return ValidationResult(
            is_valid=False,
            error_message="Candidate ID is empty"
        )
    
    # Check format: allow alphanumeric, dash, underscore
    if not re.match(r'^[a-zA-Z0-9_-]+$', candidate_id):
        return ValidationResult(
            is_valid=False,
            error_message=f"Invalid candidate ID format: {candidate_id}. "
                          f"Use only alphanumeric characters, dashes, and underscores."
        )
    
    return ValidationResult(
        is_valid=True,
        cleaned_text=candidate_id.strip()
    )

def sanitize_text(text: str) -> str:
    """
    Sanitize text by removing problematic characters.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text
    """
    if not text:
        return text
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    # Remove control characters except newlines and tabs
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    return text

def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """
    Truncate text to maximum token count while preserving readability.
    
    Args:
        text: Text to truncate
        max_tokens: Maximum token count
        
    Returns:
        Truncated text
    """
    max_chars = max_tokens * TOKEN_RATIO
    
    if len(text) <= max_chars:
        return text
    
    # Truncate and add ellipsis
    truncated = text[:max_chars-3].rsplit(' ', 1)[0]  # Break on word boundary
    return truncated + "..."

def validate_inputs_for_agent(
    resume_text: str,
    job_requirement: str,
    candidate_id: Optional[str] = None
) -> Tuple[ValidationResult, ValidationResult, ValidationResult]:
    """
    Validate all inputs for an agent in one call.
    
    Args:
        resume_text: Candidate resume
        job_requirement: Job requirement
        candidate_id: Optional candidate identifier
        
    Returns:
        Tuple of (resume_validation, job_validation, id_validation)
    """
    resume_result = validate_resume_text(resume_text)
    job_result = validate_job_requirement(job_requirement)
    id_result = validate_candidate_id(candidate_id) if candidate_id else ValidationResult(is_valid=True)
    
    return resume_result, job_result, id_result

def check_combined_token_limit(
    resume_tokens: int,
    job_tokens: int,
    additional_tokens: int = 1000,
    max_total: int = MAX_TOKENS_PER_REQUEST
) -> ValidationResult:
    """
    Check if combined input fits within token limits.
    
    Args:
        resume_tokens: Tokens in resume
        job_tokens: Tokens in job requirement
        additional_tokens: Extra tokens for prompts and output
        max_total: Maximum total tokens
        
    Returns:
        ValidationResult
    """
    total = resume_tokens + job_tokens + additional_tokens
    
    if total > max_total:
        return ValidationResult(
            is_valid=False,
            error_message=f"Combined token count exceeds limit "
                          f"({total} > {max_total}). "
                          f"Resume: {resume_tokens}, Job: {job_tokens}, "
                          f"Overhead: {additional_tokens}",
            token_count=total
        )
    
    return ValidationResult(
        is_valid=True,
        token_count=total
    )

def suggest_resume_truncation(text: str, max_chars_per_section: int = 2000) -> dict:
    """
    Suggest which sections can be truncated if resume is too long.
    
    Args:
        text: Resume text
        max_chars_per_section: Characters to keep per section
        
    Returns:
        Dictionary with truncation suggestions
    """
    sections = {
        "Summary": text[200:].find("Experience") if "Experience" in text else -1,
        "Experience": text.find("Education") if "Education" in text else -1,
        "Projects": text.find("Skills") if "Skills" in text else -1,
        "About": text.find("More") if "More" in text else -1,
    }
    
    suggestions = []
    for section, start_idx in sections.items():
        if start_idx > max_chars_per_section:
            suggestions.append(f"Truncate {section} section (currently {start_idx} chars)")
    
    return {
        "total_chars": len(text),
        "estimated_tokens": estimate_tokens(text),
        "suggestions": suggestions
    }
