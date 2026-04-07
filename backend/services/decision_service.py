from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

class FinalDecision(BaseModel):
    final_score: int = Field(description="Final candidate score from 1 to 100")
    decision: str = Field(description="Must be 'hire', 'reject', or 'further_interview'")
    explanation: str = Field(description="Detailed explanation of the decision based on agent reports")

class RejectionFeedback(BaseModel):
    missing_skills: list[str] = Field(description="Critical skills the candidate lacks")
    experience_gap: str = Field(description="Any gaps in experience duration or quality")
    suggestions: str = Field(description="Constructive suggestions for the candidate to improve")

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)

async def run_decision_chain(screener_report: str, tech_report: str, culture_report: str, requirements_context: str) -> dict:
    """
    Takes all multi-agent outputs and generates the final score, decision, and explanation.
    """
    decision_parser = JsonOutputParser(pydantic_object=FinalDecision)
    
    prompt = PromptTemplate(
        template="""You are the Final Decision Maker (Lead Agent) for the Hiring Pipeline.
        Based on the provided agent reports and job requirements, generate the final decision.
        
        Job Requirements Context:
        {requirements}
        
        Screener Report:
        {screener}
        
        Technical Report:
        {tech}
        
        Culture Run/Report:
        {culture}
        
        Output the decision exactly as requested by the format instructions.
        \n{format_instructions}""",
        input_variables=["requirements", "screener", "tech", "culture"],
        partial_variables={"format_instructions": decision_parser.get_format_instructions()},
    )
    
    chain = prompt | llm | decision_parser
    
    return await chain.ainvoke({
        "requirements": requirements_context,
        "screener": screener_report,
        "tech": tech_report,
        "culture": culture_report
    })

async def run_rejection_chain(decision_explanation: str, resume_details: str) -> dict:
    """
    Dedicated chain to generate constructive feedback if a candidate is rejected.
    """
    feedback_parser = JsonOutputParser(pydantic_object=RejectionFeedback)
    
    prompt = PromptTemplate(
        template="""You are an empathetic HR feedback generator.
        The candidate was rejected based on the following evaluation context.
        Generate structured, constructive feedback highlighting missing skills and experience gaps, along with actionable suggestions.
        
        Decision Explanation:
        {explanation}
        
        Candidate Details/Resume Overview:
        {resume}
        
        \n{format_instructions}""",
        input_variables=["explanation", "resume"],
        partial_variables={"format_instructions": feedback_parser.get_format_instructions()},
    )
    
    chain = prompt | llm | feedback_parser
    
    return await chain.ainvoke({
        "explanation": decision_explanation,
        "resume": resume_details
    })
