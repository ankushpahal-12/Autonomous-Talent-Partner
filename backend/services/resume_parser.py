import io
import json
from pypdf import PdfReader
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from typing import List, Optional
from services.storage_service import get_file_from_gridfs

# Load environment variables
load_dotenv()

# Define Pydantic schema for structured output extraction
class ComponentMetrics(BaseModel):
    name: str = Field(description="Name of the candidate")
    email: str = Field(description="Email address of the candidate")
    phone: Optional[str] = Field(description="Phone number or contact number of the candidate")
    skills: List[str] = Field(description="List of skills the candidate has. Extract individual skills.")
    projects: List[str] = Field(description="List of projects mentioned in the resume")
    experience_years: Optional[float] = Field(description="Total years of experience, if explicitly stated or easily calculable")

class CandidateProfile(BaseModel):
    candidate_id: str = Field(description="A unique ID for the candidate")
    name: str = Field(description="Name of the candidate")
    email: str = Field(description="Email address of the candidate")
    phone: Optional[str] = Field(description="Phone number or contact number of the candidate")
    skills: List[str] = Field(description="List of skills the candidate has")
    projects: List[str] = Field(description="Brief descriptions of projects")
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
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0.0
    )
    
    structured_llm = llm.with_structured_output(CandidateProfile)
    
    # Create a LangChain PromptTemplate
    from langchain_core.prompts import PromptTemplate
    
    prompt_template = PromptTemplate.from_template(
        """You are an expert HR resume parser. I am providing you with the raw text extracted from a resume PDF.
        Please extract the relevant candidate information into the provided JSON schema.
        
        Make sure to identify:
        - Name and Email
        - Phone/Contact number
        - Professional skills
        - Key projects
        
        Assign the candidate ID as: {candidate_id}
        Always set the status to: 'pending_review'
        
        Resume Text:
        {resume_text}"""
    )
    
    # 3. Create LCEL Chain (Prompt -> LLM with Structured Output)
    parsing_chain = prompt_template | structured_llm
    
    # 4. Invoke the chain
    result: CandidateProfile = await parsing_chain.ainvoke({
        "candidate_id": candidate_id,
        "resume_text": resume_text
    })
    
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
