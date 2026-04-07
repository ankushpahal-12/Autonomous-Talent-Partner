from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List, Literal
from app.core.config import settings

class CultureReport(BaseModel):
    communication_style: Literal["clear", "concise", "detailed", "verbose"] = Field(description="Dominant communication style")
    leadership_potential: bool = Field(description="Evidence of leadership or ownership")
    collaborative_tone: int = Field(description="1-10 score for collaborative work")
    summary: str = Field(description="Analysis of soft skills and culture fit")
    culture_fit_score: int = Field(description="1-10 overall culture fit")

async def run_culture_agent(resume_text: str, job_requirement: str) -> CultureReport:
    """
    Evaluates soft skills and culture fit based on the resume content.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=settings.GOOGLE_API_KEY, temperature=0.5)
    structured_llm = llm.with_structured_output(CultureReport)
    
    prompt = f"""
    You are a Culture Fit and Soft Skills Reviewer Agent. 
    Analyze the candidate's professional style based on their resume.

    JOB REQUIREMENT:
    {job_requirement}

    CANDIDATE RESUME:
    {resume_text}

    Evaluate:
    1. Communication style in project descriptions.
    2. Leadership examples (mentoring, leading teams, ownership).
    3. Collaborative nature (teamwork, cross-functional projects).

    Provide a structured culture analysis.
    """
    
    return await structured_llm.ainvoke(prompt)
