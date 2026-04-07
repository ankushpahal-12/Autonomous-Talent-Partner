from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from pydantic import BaseModel, Field
from typing import List, Literal
from app.core.config import settings

class ScreenerReport(BaseModel):
    visa_status: Literal["eligible", "ineligible", "unknown"] = Field(description="Eligibility based on visa info")
    location_match: Literal["match", "mismatch", "remote_only"] = Field(description="Does candidate location match job location")
    experience_level: Literal["junior", "mid", "senior", "lead"] = Field(description="Estimated seniority level")
    summary: str = Field(description="1-2 sentence summary of hard requirement check")
    passed: bool = Field(description="True if basic criteria are met")

async def run_screener_agent(resume_text: str, job_requirement: str) -> ScreenerReport:
    """
    Evaluates hard requirements like visas, location, and seniority.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=settings.GOOGLE_API_KEY, temperature=0)
    structured_llm = llm.with_structured_output(ScreenerReport)
    
    prompt = f"""
    You are a Recruitment Screener Agent. Your job is to check if a candidate meets the hard requirements 
    of a job description.

    JOB REQUIREMENT:
    {job_requirement}

    CANDIDATE RESUME:
    {resume_text}

    Analyze the resume for:
    1. Visa status or work authorization (if mentioned).
    2. Current location vs required location.
    3. Years of experience vs required seniority.

    Provide a structured report based on your findings.
    """
    
    return await structured_llm.ainvoke(prompt)
