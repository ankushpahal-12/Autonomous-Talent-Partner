import re
from typing import Dict, Any

class FairHiringProcessor:
    """
    Implements the Hybrid Bias Reduction Layer.
    Redacts personal identifiers (Name, Gender, Photo) for initial screening.
    """

    def __init__(self, mandatory: bool = True):
        self.mandatory = mandatory
        # Basic patterns for redaction (can be expanded with NER models)
        self.pii_patterns = {
            "name": r"(?i)\b(?:Name|Candidate|Full Name):\b\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*",
            "gender": r"(?i)\b(?:Gender|Sex):\b\s*(?:Male|Female|Non-binary|Transgender|Other)",
            "photo": r"(?i)\[IMAGE\]|\[PHOTO\]|\[RESUME_PHOTO\]"
        }

    def redact_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        Redacts PII from resume text and returns the redacted text 
        along with an audit log.
        """
        redacted_text = resume_text
        removed_fields = []

        # 1. Simple Regex Redaction
        for field, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, redacted_text)
            if matches:
                redacted_text = re.sub(pattern, f"[REDACTED_{field.upper()}]", redacted_text)
                removed_fields.append(field)

        # 2. PII Cleanup for Common Locations (Name usually at top)
        # We'll also remove the first 2-3 lines if they look like contact info
        lines = redacted_text.split("\n")
        if len(lines) > 2:
            contact_indicators = ["@", "Phone:", "Location:", "Address:"]
            if any(ind in lines[0] or ind in lines[1] for ind in contact_indicators):
                lines[0] = "[REDACTED_HEADER]"
                lines[1] = "[REDACTED_CONTACT_INFO]"
                if "header" not in removed_fields: removed_fields.append("header")

        return {
            "redacted_text": "\n".join(lines),
            "audit_log": {
                "bias_checked": True,
                "fields_removed": removed_fields,
                "mode": "Fair Hiring (Default ON)"
            }
        }

# Singleton
fair_hiring_service = FairHiringProcessor()
