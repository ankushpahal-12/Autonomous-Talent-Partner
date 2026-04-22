"""
LLM Service for Job Description Generation and AI Analysis
Uses Google Gemini via LangChain for intelligent job description generation and analysis
"""

import logging
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import json

logger = logging.getLogger(__name__)

# Try to import LangChain dependencies, but don't fail if they're not available
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import PydanticOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LangChain dependencies not available: {e}. LLM features will be disabled.")
    LANGCHAIN_AVAILABLE = False

from app.core.config import settings


class JobDescription(BaseModel):
    """Generated job description structure"""
    title: str = Field(description="Job title")
    description: str = Field(description="Full job description")
    skills: List[str] = Field(description="Required technical skills")
    experience_level: str = Field(description="Required experience level (Junior/Mid/Senior/Lead)")
    education: str = Field(description="Educational requirements")
    salary_range: str = Field(description="Estimated salary range")
    benefits: List[str] = Field(description="Key benefits offered")


class JobSuggestion(BaseModel):
    """AI-generated suggestion for job improvement"""
    category: str = Field(description="Category of suggestion (clarity, completeness, competitiveness, etc.)")
    suggestion: str = Field(description="The specific suggestion")
    reason: str = Field(description="Why this improvement matters")
    impact: str = Field(description="Expected impact (High/Medium/Low)")


class LLMJobService:
    """Service for LLM-based job description generation and analysis"""
    
    def __init__(self, api_key_index: int = 11):
        """Initialize LLM client with API key rotation
        
        Args:
            api_key_index: Index for API key rotation (default: 11 for job service)
        """
        try:
            api_key = settings.get_key_for_agent(api_key_index)
            if not api_key:
                logger.warning(f"No API key available at index {api_key_index}. LLM features will be disabled.")
                self.llm = None
                return
                
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-pro",
                api_key=api_key,
                temperature=0.7,
                top_p=0.9,
                top_k=40
            )
            logger.info(f"LLM Service initialized with Google Gemini (key index: {api_key_index})")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self.llm = None
    
    async def generate_job_description(self, requirements: str) -> Dict[str, Any]:
        """
        Generate a professional job description from user requirements.
        
        Args:
            requirements: User's requirements as text
            
        Returns:
            Dictionary with generated job description
        """
        if not self.llm:
            logger.warning("LLM not available, returning requirements as-is")
            return {
                "title": "Professional Position",
                "description": requirements,
                "skills": [],
                "experience_level": "Mid",
                "education": "Bachelor's Degree",
                "salary_range": "Competitive",
                "benefits": []
            }
        
        try:
            prompt_template = PromptTemplate(
                input_variables=["requirements"],
                template="""You are an expert HR professional and job description writer.

Based on the following user requirements, generate a comprehensive, professional job description.

User Requirements:
{requirements}

Create a detailed job description with proper structure, professional tone, and competitive positioning.
Include specific technical requirements, soft skills, and clear expectations."""
            )
            
            parser = PydanticOutputParser(pydantic_object=JobDescription)
            
            # Format instructions into prompt
            format_instructions = parser.get_format_instructions()
            full_prompt = prompt_template.format_prompt(requirements=requirements)
            
            # Call LLM
            response = await self.llm.apredict(f"{full_prompt.to_string()}\n\n{format_instructions}")
            
            # Parse response
            parsed_job = parser.parse(response)
            
            logger.info(f"Successfully generated job description for: {parsed_job.title}")
            
            return {
                "title": parsed_job.title,
                "description": parsed_job.description,
                "skills": parsed_job.skills,
                "experience_level": parsed_job.experience_level,
                "education": parsed_job.education,
                "salary_range": parsed_job.salary_range,
                "benefits": parsed_job.benefits
            }
            
        except Exception as e:
            logger.error(f"Error generating job description: {e}")
            # Fallback: return structured version of requirements
            return {
                "title": "Professional Position",
                "description": requirements,
                "skills": [],
                "experience_level": "Mid",
                "education": "Not specified",
                "salary_range": "Competitive",
                "benefits": []
            }
    
    async def generate_job_suggestions(self, job_title: str, job_description: str) -> List[Dict[str, str]]:
        """
        Analyze job description and generate improvement suggestions.
        
        Args:
            job_title: The job title
            job_description: The full job description
            
        Returns:
            List of suggestions for improvement
        """
        if not self.llm:
            logger.warning("LLM not available, returning empty suggestions")
            return []
        
        try:
            prompt = f"""You are an expert HR consultant analyzing a job description for completeness and competitiveness.

Job Title: {job_title}

Current Job Description:
{job_description}

Analyze this job description and provide 3-5 specific, actionable suggestions to make it more:
1. Complete (missing important details)
2. Competitive (to attract top talent)
3. Clear (easier to understand for candidates)
4. Specific (measurable and well-defined)

For each suggestion, provide:
- What specific text is missing or should be improved
- Why this improvement matters
- The expected impact on candidate quality"""
            
            response = await self.llm.apredict(prompt)
            
            # Parse suggestions from response
            suggestions = self._parse_suggestions(response)
            logger.info(f"Generated {len(suggestions)} suggestions for job: {job_title}")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return []
    
    async def merge_suggestion_into_description(
        self, 
        original_description: str,
        suggestion: str,
        job_title: str
    ) -> str:
        """
        Intelligently merge a suggestion into the job description.
        
        Args:
            original_description: Current job description
            suggestion: The suggestion to merge
            job_title: The job title (for context)
            
        Returns:
            Updated job description with suggestion merged
        """
        if not self.llm:
            logger.warning("LLM not available, returning original description")
            return original_description
        
        try:
            prompt = f"""You are an expert job description editor.

Job Title: {job_title}

Current Description:
{original_description}

Improvement Suggestion:
{suggestion}

Seamlessly integrate this suggestion into the job description. 
The merged description should:
1. Flow naturally without repetition
2. Maintain the original tone and structure
3. Clearly incorporate the suggested improvement
4. Keep the same length or slightly longer if needed

Return ONLY the improved job description, nothing else."""
            
            merged_description = await self.llm.apredict(prompt)
            logger.info(f"Successfully merged suggestion for job: {job_title}")
            
            return merged_description
            
        except Exception as e:
            logger.error(f"Error merging suggestion: {e}")
            return original_description
    
    def _parse_suggestions(self, response: str) -> List[Dict[str, str]]:
        """
        Parse LLM suggestions response into structured list.
        
        Args:
            response: Raw LLM response
            
        Returns:
            List of structured suggestions
        """
        try:
            # Try to parse as JSON first
            suggestions = json.loads(response)
            if isinstance(suggestions, list):
                return suggestions
        except:
            pass
        
        # Fallback: parse text response
        suggestions = []
        lines = response.split('\n')
        current_suggestion = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_suggestion:
                    suggestions.append(current_suggestion)
                    current_suggestion = {}
                continue
            
            if any(prefix in line.lower() for prefix in ['suggestion:', 'improvement:', 'what:']):
                if current_suggestion and 'suggested_text' not in current_suggestion:
                    current_suggestion['suggested_text'] = line.split(':', 1)[-1].strip()
            elif any(prefix in line.lower() for prefix in ['reason:', 'why:', 'impact:']):
                if current_suggestion and 'reason' not in current_suggestion:
                    current_suggestion['reason'] = line.split(':', 1)[-1].strip()
            elif current_suggestion:
                # Continue previous field if no prefix
                if 'reason' in current_suggestion and 'suggested_text' in current_suggestion:
                    current_suggestion['reason'] += ' ' + line
                elif 'suggested_text' in current_suggestion:
                    current_suggestion['suggested_text'] += ' ' + line
        
        if current_suggestion:
            suggestions.append(current_suggestion)
        
        # Ensure proper structure
        structured = []
        for s in suggestions:
            if 'suggested_text' in s or 'reason' in s:
                structured.append({
                    'suggested_text': s.get('suggested_text', ''),
                    'reason': s.get('reason', ''),
                    'status': 'pending'
                })
        
        return structured if structured else []


# Singleton instance
_llm_service = None


def get_llm_service() -> LLMJobService:
    """Get or create LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMJobService()
    return _llm_service
