import io
import json
import os
from pypdf import PdfReader
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List, Optional
from services.storage_service import get_file_from_gridfs

# Load environment variables
load_dotenv()

# Define Pydantic schema for structured output extraction
class EducationEntry(BaseModel):
    degree: str = Field(description="Degree or certificate name (e.g. B.Tech, M.Sc)")
    institution: str = Field(description="Name of the university or school")
    percentage_or_gpa: Optional[str] = Field(description="Final marks, GPA, or percentage obtained")
    year: Optional[str] = Field(description="Year of graduation")

class CandidateProfile(BaseModel):
    candidate_id: str = Field(description="A unique ID for the candidate")
    is_resume: bool = Field(description="True if the extracted text appears to be a legitimate resume or CV, False if it is another type of document")
    name: str = Field(description="Name of the candidate, if available")
    email: str = Field(description="Email address of the candidate, if available")
    phone: Optional[str] = Field(description="Phone number or contact number of the candidate")
    skills: List[str] = Field(description="List of technical/hard skills")
    soft_skills: List[str] = Field(description="List of soft skills (e.g. Teamwork, Leadership). If none, leave empty.", default=[])
    education: List[EducationEntry] = Field(description="Academic background including marks/GPA", default=[])
    certifications: List[str] = Field(description="Professional certifications and licenses", default=[])
    projects: List[str] = Field(description="Brief descriptions of specific projects")
    extracurricular_activities: List[str] = Field(description="Non-technical activities, volunteering, clubs, and sports", default=[])
    hackathons: List[str] = Field(description="List of hackathons and competitions with outcomes if available (e.g. Winner, Top 10, Participant)", default=[])
    experience_years: Optional[int] = Field(description="Total years of professional experience claimed in the resume", default=0)
    links: List[str] = Field(description="URLs found in the resume (GitHub, LinkedIn, Portfolio, etc.)", default=[])
    status: str = Field(description="Always 'pending_review'")

def extract_text_from_pdf(pdf_stream: io.BytesIO) -> str:
    """Read a PDF from a byte stream and extract its text."""
    reader = PdfReader(pdf_stream)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

async def parse_resume_from_gridfs(gridfs_id: str, candidate_id: str) -> dict:
    """
    Fetches resume from GridFS and parses it in-memory using an LLM.
    Returns the parsed CandidateProfile as a dictionary.
    """
    # 1. Fetch from GridFS
    file_bytes = await get_file_from_gridfs(gridfs_id)
    pdf_stream = io.BytesIO(file_bytes)
    
    # 2. Extract Raw Text
    resume_text = extract_text_from_pdf(pdf_stream)
    if not resume_text.strip():
        raise ValueError("Could not extract any text from the PDF.")

    # 2. Extract structured data using LangChain Chain
    # Use Gemini model for extraction
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set. Get it from https://aistudio.google.com/app/apikey")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.0,
        api_key=api_key
    )
    
    structured_llm = llm.with_structured_output(CandidateProfile)
    
    # Create a LangChain PromptTemplate
    from langchain_core.prompts import PromptTemplate
    
    prompt_template = PromptTemplate.from_template(
        """You are an expert HR resume parser. I am providing you with the raw text extracted from a PDF.
        First, carefully analyze the text and determine if it is actually a resume/CV. 
        If it's a resume, extract the relevant candidate information into the provided JSON schema.
        
        SPECIFIC INSTRUCTIONS:
        1. EDUCATION: Extract degree, university, and critically, any marks, GPA, or percentage mentioned.
        2. CERTIFICATIONS: List any professional certifications (e.g. AWS, PMP, Oracle).
        3. LINKS: Extract all URLs, especially GitHub, LinkedIn, and Portfolio sites.
        4. SOFT SKILLS: Identify soft skills like "Leadership", "Teamwork", or "Communication". If none are found, return an empty list.
        5. EXTRACURRICULAR: Identify non-technical activities, volunteering, club memberships, and sports achievements.
        6. HACKATHONS: List any hackathons or technical competitions. Explicitly note outcomes like "Winner", "Finalist", or "1st Place".
        7. EXPERIENCE: Extract the total number of professional experience years mentioned.
        
        Assign the candidate ID as: {candidate_id}
        Always set the status to: 'pending_review'
        
        Extracted Text:
        {resume_text}"""
    )
    
    # 3. Create LCEL Chain (Prompt -> LLM with Structured Output)
    parsing_chain = prompt_template | structured_llm
    
    # 4. Invoke the chain
    result: CandidateProfile = await parsing_chain.ainvoke({
        "candidate_id": candidate_id,
        "resume_text": resume_text
    })
    
    # Enhance with metadata
    from datetime import datetime
    profile_dict = result.model_dump()
    profile_dict["parse_timestamp"] = datetime.utcnow().isoformat()
    profile_dict["parsing_version"] = "2.0"
    
    # Return as dict
    return profile_dict

async def save_parsed_resume_to_db(candidate_id: str, parsed_data: dict) -> bool:
    """Saves parsed resume data to MongoDB with full history."""
    from app.database.mongodb import get_mongodb, connect_to_mongo
    from datetime import datetime
    
    db = get_mongodb()
    if db is None:
        connect_to_mongo()
        db = get_mongodb()
    
    if db is None:
        return False
    
    try:
        collection = db["candidates"]
        update_doc = {
            "parsed_resume": parsed_data,
            "resume_parse_timestamp": datetime.utcnow().isoformat(),
            "resume_status": "parsed",
            "skills_count": len(parsed_data.get("skills", [])),
            "projects_count": len(parsed_data.get("projects", [])),
            "certifications_count": len(parsed_data.get("certifications", []))
        }
        
        await collection.update_one(
            {"_id": candidate_id},
            {"$set": update_doc},
            upsert=True
        )
        return True
    except Exception as e:
        import logging
        logging.error(f"Failed to save parsed resume: {e}")
        return False

# This block is for manual testing
# Usage: python resume_parser.py <path_to_pdf>
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_pdf = sys.argv[1]
        # Note: This requires a running MongoDB/GridFS or a mock for get_file_from_gridfs
        print(f"To test, use the API or MCP tool: process_and_embed_resume")
