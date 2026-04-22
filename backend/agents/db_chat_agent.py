import os
import json
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
from app.core.config import settings

# Database Services via MCP
from utils.mcp_client import mcp_client_manager

load_dotenv()

@tool
async def search_candidates_in_mongo(query_text: str) -> str:
    """
    Searches MongoDB for candidates based on a text string (matches name, email, or skills).
    Returns a brief summary of matched candidates including their ID, name, skills, and match score.
    """
    try:
        res = await mcp_client_manager.invoke_tool(
            agent_id="db_chat_agent",
            tool_name="tool_search_candidates_in_mongo",
            arguments={"query_text": query_text}
        )
        return res if res else f"No candidates found matching: {query_text}"
    except Exception as e:
        return f"Error querying candidates via MCP: {str(e)}"

@tool
async def get_related_skills_from_neo4j(skill_name: str) -> str:
    """
    Queries the Neo4j Knowledge Graph to find related skills or child technologies 
    for a given skill (e.g. asking for 'React' returns 'JavaScript', 'Next.js', etc.).
    """
    try:
        res = await mcp_client_manager.invoke_tool(
            agent_id="db_chat_agent",
            tool_name="tool_get_related_skills",
            arguments={"skill_name": skill_name}
        )
        return res if res else f"No relations found in the Knowledge Graph for '{skill_name}'."
    except Exception as e:
        return f"Error querying Knowledge Graph via MCP: {str(e)}"


# Define agent prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant for the Autonomous Talent Partner HR platform. You have tools to query MongoDB for candidate profiles and Neo4j for skill relations. Answer questions directly and concisely without hallucinating. If real data is not found, state that it cannot be found."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", 
api_key=settings.get_key_for_agent(8), 
temperature=0,
max_retries=5,
timeout=60
)

# Bind tools
tools = [search_candidates_in_mongo, get_related_skills_from_neo4j]
agent = create_tool_calling_agent(llm, tools, prompt)

# Create AgentExecutor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

async def ask_database(user_query: str) -> str:
    """
    Main entry point function to interact with the database chatbot agent.
    """
    try:
        response = await agent_executor.ainvoke({"input": user_query})
        return response.get("output", "No response generated.")
    except Exception as e:
        return f"Error executing chat agent: {str(e)}"

if __name__ == "__main__":
    import asyncio
    # Simple CLI manual test
    async def run_test():
        query = "Find candidates that have experience with Machine Learning"
        print(f"Querying: {query}")
        result = await ask_database(query)
        print("Response:\n", result)
    
    asyncio.run(run_test())
