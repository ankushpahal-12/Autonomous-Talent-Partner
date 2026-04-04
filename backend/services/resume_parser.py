import os
import json
from pypdf import PdfReader
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List, Optional

# Load environment variables
load_dotenv()

# Define Pydantic schema for structured output extraction
class ComponentMetrics(BaseModel):
    name: str = Field(description="Name of the candidate")
    email: str = Field(description="Email address of the candidate")
    skills: List[str] = Field(description="List of skills the candidate has. Extract individual skills.")
    projects: List[str] = Field(description="List of projects mentioned in the resume")
    experience_years: Optional[float] = Field(description="Total years of experience, if explicitly stated or easily calculable")

class CandidateProfile(BaseModel):
    candidate_id: str = Field(description="A unique ID for the candidate")
    name: str = Field(description="Name of the candidate")
    email: str = Field(description="Email address of the candidate")
    skills: List[str] = Field(description="List of skills the candidate has")
    projects: List[str] = Field(description="Brief descriptions of projects")
    status: str = Field(description="Always 'pending_review'")

def extract_text_from_pdf(pdf_path: str) -> str:
    """Read a PDF file and extract its text."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at {pdf_path}")
    
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def parse_resume(pdf_path: str, candidate_id: str) -> dict:
    """
    Complete flow to parse resume from PDF using an LLM to extract structured JSON.
    Returns the parsed CandidateProfile as a dictionary.
    """
    # 1. Extract Raw Text
    resume_text = extract_text_from_pdf(pdf_path)
    if not resume_text.strip():
        raise ValueError("Could not extract any text from the PDF.")

    # 2. Extract structured data using LLM
    # Use Gemini model for extraction, assuming GOOGLE_API_KEY is in .env
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",  # Update to latest model available in environment
        temperature=0.0
    )
    
    structured_llm = llm.with_structured_output(CandidateProfile)
    
    prompt = f"""
    You are an expert HR resume parser. I am providing you with the raw text extracted from a resume PDF.
    Please extract the relevant candidate information into the provided JSON schema.
    
    Assign the candidate ID as: {candidate_id}
    Always set the status to: 'pending_review'
    
    Resume Text:
    {resume_text}
    """
    
    # 3. Get the structured output
    result: CandidateProfile = structured_llm.invoke(prompt)
    
    # Return as dict
    return result.model_dump()

if __name__ == "__main__":
    # Small local test block if run directly
    import sys
    if len(sys.argv) > 1:
        test_pdf = sys.argv[1]
        try:
            print("Parsing PDF...", test_pdf)
            output = parse_resume(test_pdf, "test_candidate_001")
            print(json.dumps(output, indent=2))
        except Exception as e:
            print(f"Error parsing resume: {e}")
