import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List
from app.core.config import settings

class SkillFrequency(BaseModel):
    skill: str = Field(description="Name of the technical skill")
    implementation_count: int = Field(description="Total number of discrete projects, modules, or distinct roles where this skill was actively implemented or utilized by the candidate.")

class SkillCounterReport(BaseModel):
    skills: List[SkillFrequency] = Field(description="List of top 10 core technical skills and their exact real-world implementation counts from the resume.")

async def run_skill_counter_agent(resume_text: str) -> SkillCounterReport:
    """
    Scans the candidate's entire resume to mathematically quantify their experience 
    by counting exactly how many times a skill was tangibly implemented across different projects.
    """
    logging.info("Running Skill Counter Analytics Agent...")
    key = settings.get_key_for_agent(7)
    if not key:
        logging.warning("Skill Counter Agent started without a valid API key.")

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            api_key=key, 
            transport="rest",
            temperature=0.0
        )
        structured_llm = llm.with_structured_output(SkillCounterReport)
        
        prompt = f"""
        You are a highly analytical HR Technical Data Extraction Agent.
        Your goal is to parse the provided text and provide REAL data points.
        
        CANDIDATE RESUME:
        {resume_text}
        
        INSTRUCTIONS:
        1. Identify the core technical languages, frameworks, or tools the candidate knows (e.g. React, Python, AWS, NLP, etc).
        2. Read through the candidate's work experience and project history.
        3. COUNT EXACTLY how many *distinct projects* or *distinct job roles* explicitly required the candidate to use each skill.
        4. Do NOT use fake numbers. If they used Python at 3 companies and 1 personal project, the implementation_count is 4.
        5. Return the top 10 most used skills based on their extracted frequency counts.
        """
        
        report = await structured_llm.ainvoke(prompt)
        # Sort skills by implementation_count descending to ensure primary skills are prioritized in UI
        report.skills = sorted(report.skills, key=lambda x: x.implementation_count, reverse=True)
        return report
    except Exception as e:
        logging.error(f"Error in skill counter agent: {str(e)}")
        # Provide a safe fallback if generation fails
        return SkillCounterReport(skills=[])
