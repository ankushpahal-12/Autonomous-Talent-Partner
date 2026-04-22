"""
scraper_agent.py — External Data Enrichment Agent with Advanced Scoring
========================================================================
Extracts LinkedIn and GitHub profile URLs from parsed resume data, then
fetches publicly available information from those sources to build a
360-degree candidate profile with comprehensive scoring.

FEATURES:
- GitHub: Deep profile analysis with contribution metrics
- Project Quality: Analyzes specific repositories with star/fork ratios
- Contribution Patterns: Analyzes project diversity and impact
- Experience Scoring: LinkedIn experience evaluation
- Final Score: Generates 0-100 score for decision making

The enriched data is stored under `candidate.external_intel` in MongoDB.
"""

import re
import json
import httpx
from typing import Optional, List, Dict
from datetime import datetime
from app.core.config import settings
from utils.mcp_client import mcp_client_manager
from pydantic import BaseModel, Field

async def mcp_safe_httpx_get(url: str, params: dict = None, headers: dict = None):
    res_str = await mcp_client_manager.invoke_tool(
        agent_id="scraper_agent",
        tool_name="tool_http_get",
        arguments={
            "url": url,
            "params_json": json.dumps(params or {}),
            "headers_json": json.dumps(headers or {})
        }
    )
    if not res_str: return None
    data = json.loads(res_str)
    if "error" in data: return None
    
    class DummyRes:
        def __init__(self, c, t):
            self.status_code = c
            self.text = t
        def json(self): return json.loads(self.text)
        def raise_for_status(self):
            if self.status_code >= 400: raise Exception(f"HTTP {self.status_code}")
    return DummyRes(data["status_code"], data.get("text", ""))

safe_httpx_get = mcp_safe_httpx_get


GITHUB_API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "AutonomousTalentPartner/1.0",
}


def _extract_github_username(text: str) -> Optional[str]:
    """Extracts a GitHub username from a URL or @-handle in raw text."""
    # Match full URLs: github.com/username or http(s)://github.com/username
    url_match = re.search(
        r'(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,37}[a-zA-Z0-9])?)',
        text, re.IGNORECASE
    )
    if url_match:
        return url_match.group(1)
    return None


def _extract_linkedin_url(text: str) -> Optional[str]:
    """Extracts a LinkedIn profile URL from raw text."""
    url_match = re.search(
        r'(?:https?://)?(?:www\.)?linkedin\.com/in/([a-zA-Z0-9\-_%]+)',
        text, re.IGNORECASE
    )
    if url_match:
        return f"https://www.linkedin.com/in/{url_match.group(1)}"
    return None


async def fetch_github_contributions(username: str) -> dict:
    """
    Fetches contribution counts using a community proxy to avoid PAT requirements.
    Endpoint: https://github-contributions-api.jogruber.de/v4/{username}
    """
    try:
        res = await safe_httpx_get(f"https://github-contributions-api.jogruber.de/v4/{username}")
        if res and res.status_code == 200:
            data = res.json()
            return {
                "total": data.get("total", {}).get("2024", 0) + data.get("total", {}).get("2023", 0), # Simplified for "recent"
                "all_time": sum(data.get("total", {}).values()),
                "years": data.get("total", {})
            }
    except Exception as e:
        print(f"Failed to fetch contributions for {username}: {e}")
    return {"total": 0, "all_time": 0, "years": {}}


async def scrape_github_profile(username: str) -> dict:
    """
    Fetches public GitHub profile data for a given username.
    Returns: dict with repos, top languages, contributions estimate, bio.
    """
    intel = {
        "platform": "github",
        "username": username,
        "profile_url": f"https://github.com/{username}",
        "bio": None,
        "public_repos": 0,
        "followers": 0,
        "total_stars": 0,
        "total_forks": 0,
        "contributions": {"total": 0, "all_time": 0},
        "top_languages": [],
        "pinned_repos": [],
        "status": "ok",
    }

    try:
        # 1. Get user profile
        user_res = await safe_httpx_get(f"{GITHUB_API}/users/{username}", headers=HEADERS)
        if not user_res:
            intel["status"] = "upstream_error"
            return intel
            
        if user_res.status_code == 404:
            intel["status"] = "user_not_found"
            return intel
        if user_res.status_code == 403:
            intel["status"] = "rate_limited"
            return intel
        user_res.raise_for_status()
        user_data = user_res.json()

        intel["bio"] = user_data.get("bio")
        intel["public_repos"] = user_data.get("public_repos", 0)
        intel["followers"] = user_data.get("followers", 0)
        intel["company"] = user_data.get("company")
        intel["location"] = user_data.get("location")
        intel["avatar_url"] = user_data.get("avatar_url")

        # 2. Get repos for broad stats
        repos_res = await safe_httpx_get(
            f"{GITHUB_API}/users/{username}/repos",
            headers=HEADERS,
            params={"per_page": 50, "sort": "pushed", "type": "owner"}
        )
        if not repos_res:
            intel["status"] = "repos_fetch_error"
            return intel
            
        repos_res.raise_for_status()
        repos_data = repos_res.json()

        lang_count: dict = {}
        total_stars = 0
        total_forks = 0
        all_repos = []
        
        for repo in repos_data:
            lang = repo.get("language")
            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            
            total_stars += stars
            total_forks += forks
            
            if lang:
                lang_count[lang] = lang_count.get(lang, 0) + (1 + (stars // 10)) # Weight languages by stars
            
            all_repos.append({
                "name": repo.get("name"),
                "description": repo.get("description"),
                "stars": stars,
                "forks": forks,
                "language": lang,
                "url": repo.get("html_url"),
                "topics": repo.get("topics", [])
            })

        intel["total_stars"] = total_stars
        intel["total_forks"] = total_forks
        intel["top_languages"] = sorted(lang_count, key=lang_count.get, reverse=True)[:5]
        intel["all_topics"] = list(set([t for r in all_repos for t in r.get("topics", [])]))
        intel["pinned_repos"] = sorted(all_repos, key=lambda r: r["stars"], reverse=True)[:5]

        # 3. Get contributions from proxy
        intel["contributions"] = await fetch_github_contributions(username)

    except httpx.TimeoutException:
        intel["status"] = "timeout"
    except Exception as e:
        intel["status"] = f"error: {str(e)}"

    return intel


async def scrape_github_repo(repo_url: str) -> dict:
    """Fetches details for a specific repository (name, star, forks, readme)."""
    # Extract owner/repo from URL
    match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
    if not match:
        return {"status": "error", "message": "Invalid GitHub repo URL"}
    
    owner, repo = match.groups()
    repo_info = {
        "name": repo,
        "owner": owner,
        "url": repo_url,
        "stars": 0,
        "forks": 0,
        "readme": "",
        "status": "ok"
    }

    try:
        # 1. Get repo metadata
        res = await safe_httpx_get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=HEADERS)
        if res and res.status_code == 200:
            data = res.json()
            repo_info["stars"] = data.get("stargazers_count", 0)
            repo_info["forks"] = data.get("forks_count", 0)
            repo_info["description"] = data.get("description", "")
        
        # 2. Get README content (base64 encoded)
        readme_res = await safe_httpx_get(f"{GITHUB_API}/repos/{owner}/{repo}/readme", headers=HEADERS)
        if readme_res and readme_res.status_code == 200:
            import base64
            readme_data = readme_res.json()
            content = base64.b64decode(readme_data["content"]).decode("utf-8", errors="ignore")
            repo_info["readme"] = content[:2000] # Cap for context safety
        
        # 3. Get repository contents (main branch) to identifies source files
        contents_res = await safe_httpx_get(f"{GITHUB_API}/repos/{owner}/{repo}/contents", headers=HEADERS)
        if contents_res and contents_res.status_code == 200:
            files = contents_res.json()
            source_files = [f["name"] for f in files if f["type"] == "file" and f["name"].split(".")[-1] in ["py", "js", "ts", "go", "java"]]
            repo_info["source_files"] = source_files[:10] # Top 10 files
    except Exception as e:
        repo_info["status"] = f"error: {str(e)}"
    
    return repo_info


async def scrape_linkedin_profile(linkedin_url: str) -> dict:
    """
    Fetches enriched LinkedIn profile data using an external data provider (e.g. Proxycurl).
    Note: Requires settings.LINKEDIN_API_KEY to be set.
    """
    intel = {
        "platform": "linkedin",
        "url": linkedin_url,
        "summary": None,
        "experience": [],
        "headline": None,
        "status": "pending"
    }

    if not linkedin_url:
        return intel

    api_key = settings.LINKEDIN_API_KEY
    if api_key and api_key.lower() == "mock":
        # sandbox mode for testing without a work email
        intel.update({
            "status": "ok",
            "headline": "Senior Software Architect | Cloud Native Specialist",
            "summary": "Full-stack engineer with over 8 years of experience building scalable microservices and high-performance web applications. Passionate about system design and automated CI/CD pipelines.",
            "experience": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Amazon (Tier 1 Global Leader)",
                    "starts_at": {"month": 1, "year": 2021},
                    "ends_at": None,
                    "description": "Architected high-throughput services for AWS Lambda."
                },
                {
                    "title": "Software Intern",
                    "company": "Google (Tier 1 Global Leader)",
                    "starts_at": {"month": 5, "year": 2019},
                    "ends_at": {"month": 8, "year": 2019},
                    "description": "Improved search indexing efficiency by 15%."
                }
            ]
        })
        return intel

    if not api_key or "your_proxycurl" in api_key:
        intel["status"] = "missing_api_key"
        return intel

    try:
        # Extract profile ID from URL (e.g., https://www.linkedin.com/in/williamhgates)
        profile_id = linkedin_url.split("/in/")[-1].split("/")[0].split("?")[0]
        
        # Integrated with ScrapingDog LinkedIn Person Scraper
        # Endpoint: https://api.scrapingdog.com/profile/
        params = {
            "api_key": api_key,
            "type": "profile",
            "id": profile_id,
            "premium": "true"  # Required to bypass LinkedIn Captchas
        }
        
        res = await safe_httpx_get("https://api.scrapingdog.com/profile/", params=params)
        
        if res and res.status_code == 200:
            data = res.json()
            # ScrapingDog often returns a list or a nested 'fullName' object
            profile = data[0] if isinstance(data, list) and len(data) > 0 else data
            
            intel["summary"] = profile.get("about") or profile.get("summary")
            intel["headline"] = profile.get("headline") or profile.get("title")
            
            # Normalize Experience
            raw_exp = profile.get("experience", [])
            intel["experience"] = [
                {
                    "title": exp.get("title"),
                    "company": exp.get("company") or exp.get("companyName"),
                    "starts_at": exp.get("startDate") or exp.get("starts_at"),
                    "ends_at": exp.get("endDate") or exp.get("ends_at"),
                    "description": exp.get("description")
                } for exp in raw_exp
            ]
            intel["status"] = "ok"
        else:
            intel["status"] = f"api_error_{getattr(res, 'status_code', 'no_res')}"
    except Exception as e:
        intel["status"] = f"exception: {str(e)}"

    return intel


async def run_scraper_agent(candidate_id: str, parsed_data: dict) -> dict:
    """
    Main entry point for the Scraper Agent.
    Extracted social URLs and specific project links are enriched.
    """
    print(f"[ScraperAgent] Starting enrichment for: {candidate_id}")

    links = parsed_data.get("links", [])
    resume_text = " ".join([str(v) for v in parsed_data.values()])

    external_intel = {
        "candidate_id": candidate_id,
        "github": None,
        "project_analysis": [],
        "linkedin_url": None,
        "enrichment_status": "pending",
    }

    # --- GitHub Profile ---
    github_username = _extract_github_username(resume_text)
    if github_username:
        print(f"[ScraperAgent] Found GitHub Profile: @{github_username}")
        external_intel["github"] = await scrape_github_profile(github_username)

    # --- Specific Project Analysis (GitHub Repos) ---
    repo_links = [l for l in links if "github.com" in l and "/" in l.split("github.com/")[1] and "tree" not in l]
    for repo_url in repo_links[:3]: # Analyze up to 3 specific repos
        print(f"[ScraperAgent] Analyzing specific repo: {repo_url}")
        repo_data = await scrape_github_repo(repo_url)
        if repo_data["status"] == "ok":
            external_intel["project_analysis"].append(repo_data)

    # --- LinkedIn ---
    linkedin_url = _extract_linkedin_url(resume_text)
    external_intel["linkedin_url"] = linkedin_url
    if linkedin_url:
        print(f"[ScraperAgent] Found LinkedIn Profile: {linkedin_url}")
        external_intel["linkedin"] = await scrape_linkedin_profile(linkedin_url)
    
    external_intel["enrichment_status"] = "complete"
    return external_intel


class GitHubScore(BaseModel):
    """GitHub profile evaluation score"""
    profile_score: int = Field(0, description="Overall profile quality (0-100)")
    contribution_score: int = Field(0, description="Contribution activity (0-100)")
    project_quality_score: int = Field(0, description="Project quality (0-100)")
    influence_score: int = Field(0, description="Community influence (0-100)")
    language_diversity: int = Field(0, description="Technology diversity (0-100)")
    details: Dict = Field(default_factory=dict)


class ExperienceScore(BaseModel):
    """LinkedIn experience evaluation"""
    seniority_score: int = Field(0, description="Seniority level (0-100)")
    company_prestige: int = Field(0, description="Company tier (0-100)")
    role_relevance: int = Field(0, description="Relevance to target role (0-100)")
    experience_duration: int = Field(0, description="Years in field (0-100)")
    details: Dict = Field(default_factory=dict)


class ExternalIntelligenceScore(BaseModel):
    """Complete external intelligence evaluation"""
    github_score: int = Field(0, description="GitHub presence score (0-100)")
    linkedin_score: int = Field(0, description="LinkedIn experience score (0-100)")
    project_quality: int = Field(0, description="Project analysis score (0-100)")
    overall_external_score: int = Field(0, description="Final external score (0-100)")
    recommendation: str = Field("neutral", description="'strong', 'good', 'neutral', 'weak'")
    evidence: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


def calculate_github_score(github_data: dict) -> GitHubScore:
    """
    Calculates comprehensive GitHub profile score (0-100).
    
    Factors:
    - Public repositories count
    - Total stars and forks (community recognition)
    - Contributions (activity level)
    - Language diversity (versatility)
    - Followers (influence)
    """
    if not github_data or github_data.get("status") != "ok":
        return GitHubScore(details={"error": f"GitHub data unavailable: {github_data.get('status', 'unknown')}"})
    
    score_details = {}
    
    # 1. PROFILE QUALITY SCORE (based on basic metrics)
    public_repos = github_data.get("public_repos", 0)
    followers = github_data.get("followers", 0)
    
    # Repos: 0-20 repos = 10 pts, 20-50 = 50 pts, 50+ = 100 pts
    repos_score = min(100, (public_repos // 5) * 10) if public_repos > 0 else 0
    
    # Followers: 0-50 = 10 pts, 50-500 = 50 pts, 500+ = 100 pts
    followers_score = min(100, (followers // 5)) if followers > 0 else 0
    
    profile_score = int((repos_score + followers_score) / 2)
    score_details["repos_score"] = repos_score
    score_details["followers_score"] = followers_score
    
    # 2. CONTRIBUTION SCORE (consistency and activity)
    contributions = github_data.get("contributions", {})
    total_contributions = contributions.get("total", 0)
    
    # Total contributions: 0-100 = 10pts, 100-1000 = 50pts, 1000+ = 100pts
    contrib_score = min(100, max(0, (total_contributions - 100) / 10))
    score_details["total_contributions"] = total_contributions
    
    # 3. PROJECT QUALITY SCORE (stars and forks)
    total_stars = github_data.get("total_stars", 0)
    total_forks = github_data.get("total_forks", 0)
    
    # Stars: 0-10 = 10pts, 10-100 = 50pts, 100+ = 100pts
    stars_score = min(100, max(0, (total_stars - 10) / 0.9))
    
    # Forks: 0-5 = 10pts, 5-50 = 50pts, 50+ = 100pts
    forks_score = min(100, max(0, (total_forks - 5) / 0.45))
    
    project_quality_score = int((stars_score + forks_score) / 2)
    score_details["total_stars"] = total_stars
    score_details["total_forks"] = total_forks
    
    # 4. INFLUENCE SCORE (stars to repos ratio - quality indicator)
    if public_repos > 0:
        stars_per_repo = total_stars / public_repos
        influence_score = min(100, (stars_per_repo / 5) * 100)  # 5+ stars/repo = excellent
    else:
        influence_score = 0
    
    score_details["stars_per_repo"] = stars_per_repo if public_repos > 0 else 0
    
    # 5. LANGUAGE DIVERSITY (versatility)
    top_languages = github_data.get("top_languages", [])
    language_count = len(top_languages)
    
    # 1-2 langs = 30pts, 3-4 = 70pts, 5+ = 100pts
    if language_count >= 5:
        language_diversity = 100
    elif language_count >= 3:
        language_diversity = 70
    elif language_count > 0:
        language_diversity = 30
    else:
        language_diversity = 0
    
    score_details["languages"] = top_languages
    score_details["language_count"] = language_count
    
    # Calculate weighted overall scores
    github_score = GitHubScore(
        profile_score=profile_score,
        contribution_score=int(contrib_score),
        project_quality_score=project_quality_score,
        influence_score=int(influence_score),
        language_diversity=language_diversity,
        details=score_details
    )
    
    return github_score


def calculate_experience_score(linkedin_data: dict) -> ExperienceScore:
    """
    Calculates LinkedIn experience score (0-100).
    
    Factors:
    - Current title and company prestige
    - Total years of experience
    - Company tier (FAANG, Tier 1, etc.)
    - Role relevance
    """
    if not linkedin_data or linkedin_data.get("status") != "ok":
        return ExperienceScore(details={"error": f"LinkedIn data unavailable: {linkedin_data.get('status', 'unknown')}"})
    
    score_details = {}
    
    # 1. COMPANY PRESTIGE (current role)
    experience_list = linkedin_data.get("experience", [])
    company_prestige = 0
    
    if experience_list:
        current_role = experience_list[0]  # Most recent role
        company = current_role.get("company", "").upper()
        score_details["current_company"] = company
        
        # FAANG tier
        faang = ["GOOGLE", "AMAZON", "FACEBOOK", "META", "APPLE", "MICROSOFT", "NETFLIX"]
        tier1 = ["IBM", "INTEL", "CISCO", "ORACLE", "SALESFORCE", "PAYPAL", "ADOBE", "UBER"]
        tier2 = ["STRIPE", "DATABRICKS", "FIGMA", "AIRBNB", "DROPBOX", "SLACK", "PINTEREST", "SQUARE"]
        
        if any(f in company for f in faang):
            company_prestige = 100
            score_details["company_tier"] = "FAANG"
        elif any(t in company for t in tier1):
            company_prestige = 80
            score_details["company_tier"] = "Tier 1"
        elif any(t in company for t in tier2):
            company_prestige = 70
            score_details["company_tier"] = "Tier 2 (High Growth)"
        else:
            company_prestige = 50
            score_details["company_tier"] = "Other"
    
    # 2. EXPERIENCE DURATION
    total_years = 0
    for exp in experience_list:
        starts = exp.get("starts_at")
        ends = exp.get("ends_at")
        
        try:
            if isinstance(starts, dict):
                start_year = starts.get("year", 2024)
            else:
                start_year = int(str(starts).split("-")[0]) if starts else 2024
            
            if ends:
                if isinstance(ends, dict):
                    end_year = ends.get("year", 2024)
                else:
                    end_year = int(str(ends).split("-")[0]) if ends else 2024
            else:
                end_year = 2024  # Current year
            
            total_years += max(0, end_year - start_year)
        except:
            pass
    
    # 0-2 years = 20pts, 2-5 = 50pts, 5-10 = 80pts, 10+ = 100pts
    if total_years >= 10:
        duration_score = 100
    elif total_years >= 5:
        duration_score = 80
    elif total_years >= 2:
        duration_score = 50
    elif total_years > 0:
        duration_score = 20
    else:
        duration_score = 0
    
    score_details["total_years"] = total_years
    
    # 3. SENIORITY SCORE (based on titles)
    seniority_score = 0
    titles_held = [exp.get("title", "") for exp in experience_list]
    score_details["titles"] = titles_held[:5]  # Top 5 roles
    
    for title in titles_held:
        title_upper = title.upper()
        
        # Executive/Leadership
        if any(x in title_upper for x in ["DIRECTOR", "VP", "CHIEF", "MANAGER", "LEAD", "PRINCIPAL"]):
            seniority_score = max(seniority_score, 100)
        # Senior level
        elif any(x in title_upper for x in ["SENIOR", "STAFF"]):
            seniority_score = max(seniority_score, 80)
        # Mid level
        elif any(x in title_upper for x in ["ENGINEER", "ARCHITECT", "SPECIALIST"]):
            seniority_score = max(seniority_score, 60)
        # Junior level
        elif any(x in title_upper for x in ["JUNIOR", "INTERN", "ASSOCIATE"]):
            seniority_score = max(seniority_score, 30)
        else:
            seniority_score = max(seniority_score, 40)
    
    # 4. ROLE RELEVANCE (simplified - assumes backend/full-stack roles)
    role_relevance = 50  # Default neutral
    
    relevant_keywords = ["ENGINEER", "ARCHITECT", "DEVELOPER", "SENIOR", "STAFF", "TECH LEAD"]
    for title in titles_held[:3]:
        for keyword in relevant_keywords:
            if keyword in title.upper():
                role_relevance = 100
                break
    
    score_details["role_relevance_keywords"] = relevant_keywords
    
    experience_score = ExperienceScore(
        seniority_score=seniority_score,
        company_prestige=company_prestige,
        role_relevance=role_relevance,
        experience_duration=duration_score,
        details=score_details
    )
    
    return experience_score


def calculate_project_quality_score(project_analysis: List[dict]) -> int:
    """
    Analyzes specific projects/repos for quality metrics.
    Returns 0-100 score based on stars, forks, and documentation.
    """
    if not project_analysis:
        return 0  # No projects analyzed
    
    scores = []
    
    for project in project_analysis:
        if project.get("status") != "ok":
            continue
        
        stars = project.get("stars", 0)
        forks = project.get("forks", 0)
        readme_length = len(project.get("readme", ""))
        has_description = len(project.get("description", "")) > 20
        
        # Stars indicate community adoption
        stars_score = min(100, (stars / 10) * 100)
        
        # Forks indicate reusability
        forks_score = min(100, (forks / 5) * 100)
        
        # Documentation (README) indicates quality
        readme_score = 100 if readme_length > 500 else 50 if readme_length > 100 else 0
        
        # Full project evaluation
        project_score = int((stars_score * 0.4 + forks_score * 0.4 + readme_score * 0.2))
        scores.append(project_score)
    
    # Average of all analyzed projects
    return int(sum(scores) / len(scores)) if scores else 0


async def calculate_external_intelligence_score(external_intel: dict) -> ExternalIntelligenceScore:
    """
    Comprehensive scoring of external intelligence.
    Combines GitHub, LinkedIn, and project analysis into final score.
    
    Returns a score from 0-100 and recommendation.
    """
    evidence = []
    warnings = []
    
    # ===== GitHub Score =====
    github_score = 0
    github_data = external_intel.get("github")
    
    if github_data and github_data.get("status") == "ok":
        github_eval = calculate_github_score(github_data)
        
        # Weighted GitHub score
        github_score = int(
            github_eval.profile_score * 0.2 +
            github_eval.contribution_score * 0.25 +
            github_eval.project_quality_score * 0.3 +
            github_eval.influence_score * 0.15 +
            github_eval.language_diversity * 0.1
        )
        
        if github_score >= 80:
            evidence.append(f"Exceptional GitHub presence: {github_score}/100 with significant community contributions")
        elif github_score >= 60:
            evidence.append(f"Good GitHub portfolio: {github_score}/100 with active development")
        elif github_score >= 40:
            evidence.append(f"Basic GitHub presence: {github_score}/100")
        else:
            warnings.append(f"Limited GitHub presence: {github_score}/100")
    else:
        warnings.append("No GitHub profile found")
    
    # ===== LinkedIn Score =====
    linkedin_score = 0
    linkedin_data = external_intel.get("linkedin")
    
    if linkedin_data and linkedin_data.get("status") == "ok":
        linkedin_eval = calculate_experience_score(linkedin_data)
        
        # Weighted LinkedIn score
        linkedin_score = int(
            linkedin_eval.seniority_score * 0.25 +
            linkedin_eval.company_prestige * 0.35 +
            linkedin_eval.experience_duration * 0.25 +
            linkedin_eval.role_relevance * 0.15
        )
        
        years = linkedin_eval.details.get("total_years", 0)
        company = linkedin_eval.details.get("current_company", "Unknown")
        
        if linkedin_score >= 80:
            evidence.append(f"Strong professional background: {linkedin_score}/100 ({years}+ years at {company})")
        elif linkedin_score >= 60:
            evidence.append(f"Solid experience: {linkedin_score}/100 ({years}+ years)")
        else:
            warnings.append(f"Limited professional background: {linkedin_score}/100")
    else:
        warnings.append("No LinkedIn profile found")
    
    # ===== Project Quality Score =====
    project_analysis = external_intel.get("project_analysis", [])
    project_quality = calculate_project_quality_score(project_analysis)
    
    if project_analysis:
        if project_quality >= 70:
            evidence.append(f"Excellent project portfolio: {project_quality}/100 with high-quality repositories")
        elif project_quality >= 50:
            evidence.append(f"Good projects: {project_quality}/100")
        else:
            evidence.append(f"Basic project portfolio: {project_quality}/100")
    
    # ===== FINAL OVERALL SCORE =====
    scores = [s for s in [github_score, linkedin_score] if s > 0]
    
    if scores:
        # Weight: GitHub 40%, LinkedIn 40%, Projects 20%
        weights_sum = 0
        weighted_total = 0
        
        if github_score > 0:
            weighted_total += github_score * 0.4
            weights_sum += 0.4
        
        if linkedin_score > 0:
            weighted_total += linkedin_score * 0.4
            weights_sum += 0.4
        
        if project_quality > 0:
            weighted_total += project_quality * 0.2
            weights_sum += 0.2
        
        overall_score = int(weighted_total / weights_sum) if weights_sum > 0 else 0
    else:
        overall_score = 0
    
    # Determine recommendation
    if overall_score >= 85:
        recommendation = "strong"
        evidence.append("★★★ STRONG EXTERNAL VERIFICATION: Candidate demonstrates exceptional external presence")
    elif overall_score >= 70:
        recommendation = "good"
        evidence.append("★★ GOOD EXTERNAL PROFILE: Candidate has solid external credentials")
    elif overall_score >= 50:
        recommendation = "neutral"
        evidence.append("★ LIMITED EXTERNAL DATA: Insufficient information to verify claims")
    else:
        recommendation = "weak"
        warnings.append("⚠ WEAK EXTERNAL PRESENCE: Limited verified professional presence")
    
    return ExternalIntelligenceScore(
        github_score=github_score,
        linkedin_score=linkedin_score,
        project_quality=project_quality,
        overall_external_score=overall_score,
        recommendation=recommendation,
        evidence=evidence,
        warnings=warnings
    )


async def save_external_evaluation_to_db(candidate_id: str, external_eval: ExternalIntelligenceScore) -> bool:
    """
    Saves external intelligence evaluation via MCP.
    """
    try:
        eval_dict = external_eval.model_dump() if hasattr(external_eval, "model_dump") else external_eval
        res_str = await mcp_client_manager.invoke_tool(
            agent_id="scraper_agent",
            tool_name="tool_db_save_external_eval",
            arguments={
                "candidate_id": candidate_id,
                "external_eval_json": json.dumps(eval_dict)
            }
        )
        data = json.loads(res_str)
        return "status" in data and data["status"] == "success"
    except Exception as e:
        print(f"Failed to route save evaluation to mcp: {e}")
        return False
    except Exception as e:
        print(f"Failed to save external evaluation: {e}")
        return False
