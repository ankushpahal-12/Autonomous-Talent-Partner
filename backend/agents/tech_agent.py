from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List, Literal
from app.core.config import settings

class TechReport(BaseModel):
    tech_stack_match: Literal["high", "medium", "low"] = Field(description="Match between candidate tech stack and requirement")
    project_complexity_score: int = Field(description="1-10 score for overall project scope and complexity")
    key_technologies: List[str] = Field(description="Top 3 technologies the candidate excels in")
    summary: str = Field(description="Technical summary of projects and tech expertise")
    technical_fit_score: int = Field(description="1-10 overall technical suitability")

async def run_tech_agent(resume_text: str, job_requirement: str) -> TechReport:
    """
    Evaluates the depth and complexity of technical projects mentioned in the resume.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=settings.GOOGLE_API_KEY, temperature=0.2)
    structured_llm = llm.with_structured_output(TechReport)
    
    prompt = f"""
    You are a Senior Technical Architect and Technical Reviewer Agent. 
    Analyze the candidate's resume against the technical requirements of the job.

    JOB REQUIREMENT:
    {job_requirement}

    CANDIDATE RESUME:
    {resume_text}

    Evaluate:
    1. The core technologies used by the candidate.
    2. The complexity and scale of their projects.
    3. The depth of their technical understanding.

    Provide a structured technical analysis.
    """
    
    return await structured_llm.ainvoke(prompt)
