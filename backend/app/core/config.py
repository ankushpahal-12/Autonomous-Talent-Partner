import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """
    Centralized configuration for the FastAPI application.
    """
    PROJECT_NAME: str = "Autonomous Talent Partner"
    PROJECT_VERSION: str = "1.0.0"
    
    # Database
    MONGO_URI: str = os.getenv("MONGO_URI", "")
    DATABASE_NAME: str = os.getenv("MONGO_DB_NAME", "talent_partner_db")
    
    # AI Keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Vector DB
    CHROMA_PATH: str = os.getenv("CHROMA_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "chroma"))
    
    # Neo4j Knowledge Graph
    NEO4J_URI: str = os.getenv("NEO4J_URI", "")
    NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")
    
    # n8n Automation
    N8N_WEBHOOK_URL_SELECTED: str = os.getenv("N8N_WEBHOOK_URL_SELECTED", "")
    N8N_WEBHOOK_URL_REJECTED: str = os.getenv("N8N_WEBHOOK_URL_REJECTED", "")
    
    class Config:
        case_sensitive = True

settings = Settings()
