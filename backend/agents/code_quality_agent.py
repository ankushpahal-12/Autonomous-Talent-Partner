"""
code_quality_agent.py — Deep Static Code Analysis Agent
=========================================================
Upgraded from basic LLM review to a hybrid analysis engine that:
1. Runs RULE-BASED security and maturity checks (no LLM, instant, free)
2. Runs an LLM analysis for qualitative depth assessment

Rule-Based Checks (Module 4):
- API Key Leak Detection: Scans README and filenames for known secret patterns
- Project Maturity Rating: Checks for tests/, requirements.txt, Dockerfile, README length
- Tutorial vs. Real Project detection: Based on star counts + description richness

The LLM then adds qualitative assessment on top.
"""

import re
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from .agent_thinking import (
    ThinkingMode,
    build_cot_prefix,
    build_adaptive_prompt_context,
    run_self_reflection,
    apply_reflection_adjustments,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Security Patterns (Rule-Based)
# ============================================================================

SECRET_PATTERNS = [
    r'api[_\-]?key\s*=\s*["\'][^"\']{8,}',
    r'secret[_\-]?key\s*=\s*["\'][^"\']{8,}',
    r'password\s*=\s*["\'][^"\']{4,}',
    r'token\s*=\s*["\'][^"\']{10,}',
    r'aws[_\-]access[_\-]key',
    r'aws[_\-]secret',
    r'private[_\-]key',
    r'AKIA[A-Z0-9]{16}',  # AWS Access Key ID pattern
    r'sk-[a-zA-Z0-9]{32,}',  # OpenAI-style secret key
    r'ghp_[a-zA-Z0-9]{36}',  # GitHub personal access token
]

INSECURE_FILES = [".env", "credentials.json", "secrets.yaml", "config.secret"]

MATURITY_SIGNALS_GOOD = [
    "tests", "test", "__tests__", "spec", "pytest", "unittest",
    "requirements.txt", "pyproject.toml", "package.json",
    "Dockerfile", "docker-compose", ".github",
    "ci", "cd", ".yml", ".yaml",
    "setup.py", "Makefile", "tox.ini"
]

TUTORIAL_SIGNALS = [
    "todo app", "to-do app", "hello world", "my first", "beginner",
    "learning", "practice", "tutorial", "following along", "course project"
]


# ============================================================================
# Pydantic Models
# ============================================================================

class CodeQualityReport(BaseModel):
    """Enhanced code quality analysis report."""
    # Original fields (preserved for backward compatibility)
    source_files_found: List[str] = Field(description="Source code artifacts analyzed")
    coding_style_note: str = Field(description="Observation on variable naming, structure, and consistency")
    security_awareness: str = Field(description="Detection of unsafe patterns or secrets, if visible")
    documentation_quality: str = Field(description="Effectiveness of comments and README documentation")
    code_quality_score: int = Field(description="1-10 overall score for code quality based on artifacts")

    # NEW: Rule-based deep analysis fields (Module 4)
    security_flags: List[str] = Field(
        default_factory=list,
        description="Specific security issues found: exposed secrets, insecure files, etc."
    )
    project_maturity: str = Field(
        default="unknown",
        description="Project maturity classification: 'production-grade', 'solid', 'basic', or 'tutorial'"
    )
    maturity_evidence: List[str] = Field(
        default_factory=list,
        description="Evidence that led to the maturity classification (e.g. 'Has test/ folder', 'No README')"
    )
    is_tutorial_project: bool = Field(
        default=False,
        description="True if projects appear to be simple tutorial reproductions, not original work"
    )
    reasoning_trace: str = Field(
        default="",
        description="Brief internal reasoning trace summarising how rule-based and LLM analysis was combined."
    )


# ============================================================================
# Rule-Based Analyzers (Module 4 — instant, free, deterministic)
# ============================================================================

def _scan_for_secrets(readme_text: str, filenames: List[str]) -> List[str]:
    """Scan README and filenames for potential secret leaks."""
    flags = []
    combined_text = readme_text.lower()

    for pattern in SECRET_PATTERNS:
        if re.search(pattern, combined_text, re.IGNORECASE):
            flags.append(f"SECURITY: Potential secret pattern detected in README: '{pattern[:40]}...'")

    for fname in filenames:
        fname_lower = fname.lower()
        for insecure in INSECURE_FILES:
            if insecure in fname_lower:
                flags.append(f"SECURITY: Sensitive file found in repository: '{fname}'")

    return flags


def _assess_project_maturity(
    readme_text: str,
    filenames: List[str],
    stars: int,
    description: str
) -> tuple:
    """
    Assess whether a project is production-grade, solid, basic, or a tutorial.
    Returns: (maturity_level: str, evidence: List[str], is_tutorial: bool)
    """
    evidence = []
    maturity_points = 0
    is_tutorial = False

    # Check for README quality
    if len(readme_text) > 1000:
        maturity_points += 2
        evidence.append("Detailed README (> 1000 chars)")
    elif len(readme_text) > 300:
        maturity_points += 1
        evidence.append("Adequate README (> 300 chars)")
    elif len(readme_text) < 50:
        evidence.append("Missing or empty README")

    # Check for good engineering signals in filenames
    for signal in MATURITY_SIGNALS_GOOD:
        for fname in filenames:
            if signal.lower() in fname.lower():
                maturity_points += 1
                evidence.append(f"Found '{fname}' (engineering best practice)")
                break

    # Stars are a proxy for real-world adoption
    if stars >= 50:
        maturity_points += 3
        evidence.append(f"High community adoption: {stars} stars")
    elif stars >= 10:
        maturity_points += 1
        evidence.append(f"Some community interest: {stars} stars")

    # Check for tutorial signals in description
    desc_lower = (description or "").lower()
    readme_lower = readme_text.lower()
    for signal in TUTORIAL_SIGNALS:
        if signal in desc_lower or signal in readme_lower:
            is_tutorial = True
            evidence.append(f"Tutorial signal detected: '{signal}'")
            maturity_points -= 2
            break

    # Classify maturity
    if maturity_points >= 6:
        maturity_level = "production-grade"
    elif maturity_points >= 3:
        maturity_level = "solid"
    elif maturity_points >= 1:
        maturity_level = "basic"
    else:
        maturity_level = "tutorial"
        is_tutorial = True

    return maturity_level, evidence, is_tutorial


# ============================================================================
# Main Agent Function
# ============================================================================

async def run_code_quality_agent(
    external_projects: Optional[list],
    mode: ThinkingMode = ThinkingMode.BALANCED,
    seniority_level: str = "mid",
    past_feedback_summary: Optional[str] = None,
    enable_self_reflection: bool = True,
) -> CodeQualityReport:
    """
    Analyzes project artifacts for code quality, security, and maturity.
    Combines rule-based scanning with LLM qualitative assessment.
    Thinking Mode aware — STRICT mode penalises tutorial/insecure projects;
    POTENTIAL mode rewards ambition and novelty.
    """
    key = settings.get_key_for_agent(1)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=key,
        transport="rest",
        temperature=0.2,
        max_retries=5,
        timeout=60
    )
    structured_llm = llm.with_structured_output(CodeQualityReport)

    if not external_projects:
        return CodeQualityReport(
            source_files_found=[],
            coding_style_note="No code artifacts found.",
            security_awareness="Unknown — no public repositories were provided.",
            documentation_quality="Unknown.",
            code_quality_score=1,
            security_flags=[],
            project_maturity="unknown",
            maturity_evidence=["No project data available for assessment"],
            is_tutorial_project=False
        )

    # --- STAGE 1: Rule-Based Security & Maturity Analysis ---
    all_security_flags = []
    all_maturity_evidence = []
    maturity_levels = []
    tutorials_found = 0

    for project in external_projects:
        readme = project.get("readme", "")
        filenames = project.get("source_files", [])
        stars = project.get("stars", 0)
        description = project.get("description", "")

        # Security scan
        flags = _scan_for_secrets(readme, filenames)
        all_security_flags.extend(flags)

        # Maturity assessment
        maturity, evidence, is_tutorial = _assess_project_maturity(readme, filenames, stars, description)
        maturity_levels.append(maturity)
        all_maturity_evidence.extend([f"[{project.get('name', 'Unknown')}] {e}" for e in evidence])
        if is_tutorial:
            tutorials_found += 1

    # Aggregate maturity level (take the best project's assessment)
    maturity_priority = ["production-grade", "solid", "basic", "tutorial", "unknown"]
    overall_maturity = "unknown"
    for level in maturity_priority:
        if level in maturity_levels:
            overall_maturity = level
            break

    is_mostly_tutorials = tutorials_found >= len(external_projects) and len(external_projects) > 0

    # --- STAGE 2: LLM Qualitative Assessment ---
    context = "\n\n".join([
        f"Project: {p['name']}\nStars: {p['stars']}\nFiles: {', '.join(p.get('source_files', []))}\nREADME Summary: {p.get('readme', '')[:1000]}"
        for p in external_projects
    ])

    rule_based_summary = (
        f"\n[Rule-Based Pre-Analysis Results]\n"
        f"Security Flags Found: {len(all_security_flags)}\n"
        f"Detected Project Maturity: {overall_maturity}\n"
        f"Tutorial Projects: {tutorials_found}/{len(external_projects)}\n"
        f"Maturity Evidence: {'; '.join(all_maturity_evidence[:5])}\n"
    )

    cot      = build_cot_prefix(mode)
    adaptive = build_adaptive_prompt_context(seniority_level, past_feedback_summary)

    mode_note = {
        ThinkingMode.STRICT: (
            "STRICT MODE: Penalise any tutorial projects or security flags heavily. "
            "Only production-grade or solid projects count toward a high score."
        ),
        ThinkingMode.BALANCED: (
            "BALANCED MODE: Weigh project quality proportionally. "
            "Security flags reduce score; solid structure improves it."
        ),
        ThinkingMode.POTENTIAL: (
            "POTENTIAL MODE: Focus on engineering ambition and novelty. "
            "Reward candidates who build original, non-trivial projects even if "
            "they don't yet have full CI/CD pipelines."
        ),
    }[mode]

    prompt = f"""{cot}
{adaptive}
{mode_note}

You are an AI Senior Code Reviewer.
The rule-based security scanner has already processed this candidate's repositories.
Your job is to provide the QUALITATIVE assessment — focus on engineering judgment, not just metrics.

{rule_based_summary}

PROJECTS DATA:
{context}

Evaluate the candidate's COMMITMENT TO QUALITY based on:
1. README Quality: Detailed setup instructions vs. "Hello World" clones.
2. File Structure: Logical separation of concerns vs. flat folder dumps.
3. Technical Depth: Complexity of the project scope, not just language variety.
4. Real-World Relevance: Does this look like something a professional would ship?

Be specific. Reference project names and actual evidence.
"""

    try:
        result = await structured_llm.ainvoke(prompt)

        # Inject our rule-based findings into the LLM result
        result.security_flags = all_security_flags
        result.project_maturity = overall_maturity
        result.maturity_evidence = all_maturity_evidence[:10]  # Cap for readability
        result.is_tutorial_project = is_mostly_tutorials

        # Adjust the final score downward if security issues are found
        if all_security_flags:
            result.code_quality_score = max(1, result.code_quality_score - 2)
            result.security_awareness = f"CRITICAL: {len(all_security_flags)} security issue(s) detected by automated scan. " + result.security_awareness
        if is_mostly_tutorials:
            result.code_quality_score = max(1, result.code_quality_score - 1)

        # ── Self-Reflection Pass ──────────────────────────────────────────────────
        if enable_self_reflection:
            review = await run_self_reflection(
                llm_instance=llm,
                initial_output=result,
                resume_text=context[:4000],
                job_requirement="Code quality assessment for candidate projects.",
                mode=mode,
            )
            result = apply_reflection_adjustments(result, review)

        return result

    except Exception as e:
        logger.error(f"CodeQualityAgent LLM failed: {e}. Returning rule-based result only.")
        return CodeQualityReport(
            source_files_found=[p.get("name", "") for p in external_projects],
            coding_style_note="LLM analysis unavailable. Rule-based scan completed.",
            security_awareness=f"{len(all_security_flags)} flags found." if all_security_flags else "No obvious issues detected.",
            documentation_quality="Not assessed (LLM unavailable).",
            code_quality_score=5,
            security_flags=all_security_flags,
            project_maturity=overall_maturity,
            maturity_evidence=all_maturity_evidence,
            is_tutorial_project=is_mostly_tutorials
        )
