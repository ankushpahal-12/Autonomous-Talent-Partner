import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from typing import List

# Load .env from backend folder (or from .env in root, or parent directories)
# First try backend/.env, then .env in current dir, then parent dirs
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    # Fallback to standard search (current dir and parents)
    load_dotenv()

class Settings(BaseSettings):
    """
    Centralized configuration for the FastAPI application with enhanced security and flexibility.
    """
    # Application
    PROJECT_NAME: str = "Autonomous Talent Partner"
    PROJECT_VERSION: str = "1.0.0"
    ENV: str = os.getenv("ENV", "development")  # development, staging, production
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Security
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    API_KEY_ROTATION_ENABLED: bool = os.getenv("API_KEY_ROTATION_ENABLED", "false").lower() == "true"
    ALLOWED_FILE_TYPES: List[str] = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "25"))
    
    # Database Configuration
    MONGO_URI: str = os.getenv("MONGO_URI", "")
    DATABASE_NAME: str = os.getenv("MONGO_DB_NAME", "talent_partner_db")
    MONGO_CONNECTION_TIMEOUT_MS: int = int(os.getenv("MONGO_CONNECTION_TIMEOUT_MS", "5000"))
    MONGO_POOL_SIZE: int = int(os.getenv("MONGO_POOL_SIZE", "10"))
    
    # AI Keys - Dynamic List (more scalable than hardcoded variables)
    GOOGLE_API_KEYS: List[str] = []
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")  # Backward compatibility
    GOOGLE_API_KEY_1: str = os.getenv("GOOGLE_API_KEY_1", "")
    GOOGLE_API_KEY_2: str = os.getenv("GOOGLE_API_KEY_2", "")
    GOOGLE_API_KEY_3: str = os.getenv("GOOGLE_API_KEY_3", "")
    GOOGLE_API_KEY_4: str = os.getenv("GOOGLE_API_KEY_4", "")
    GOOGLE_API_KEY_5: str = os.getenv("GOOGLE_API_KEY_5", "")
    GOOGLE_API_KEY_6: str = os.getenv("GOOGLE_API_KEY_6", "")
    GOOGLE_API_KEY_7: str = os.getenv("GOOGLE_API_KEY_7", "")
    GOOGLE_API_KEY_8: str = os.getenv("GOOGLE_API_KEY_8", "")
    GOOGLE_API_KEY_9: str = os.getenv("GOOGLE_API_KEY_9", "")
    GOOGLE_API_KEY_10: str = os.getenv("GOOGLE_API_KEY_10", "")
    GOOGLE_API_KEY_11: str = os.getenv("GOOGLE_API_KEY_11", "")
    GOOGLE_API_KEY_12: str = os.getenv("GOOGLE_API_KEY_12", "")
    GOOGLE_API_KEY_13: str = os.getenv("GOOGLE_API_KEY_13", "")
    GOOGLE_API_KEY_14: str = os.getenv("GOOGLE_API_KEY_14", "")
    GOOGLE_API_KEY_15: str = os.getenv("GOOGLE_API_KEY_15", "")
    GOOGLE_API_KEY_16: str = os.getenv("GOOGLE_API_KEY_16","")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Vector DB
    CHROMA_PATH: str = os.getenv("CHROMA_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "chroma"))
    VECTOR_DB_COLLECTION_NAME: str = os.getenv("VECTOR_DB_COLLECTION_NAME", "candidates")
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "")
    
    # Neo4j Knowledge Graph
    NEO4J_URI: str = os.getenv("NEO4J_URI", "")
    NEO4J_USERNAME: str = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "")
    AURA_INSTANCEID: str = os.getenv("AURA_INSTANCEID", "")
    AURA_INSTANCENAME: str = os.getenv("AURA_INSTANCENAME", "")
    NEO4J_ENABLED: bool = NEO4J_URI and NEO4J_PASSWORD and "your-neo4j" not in NEO4J_URI
    
    # LinkedIn
    LINKEDIN_API_KEY: str = os.getenv("LINKEDIN_API_KEY", "")
    
    # n8n Automation
    N8N_WEBHOOK_URL_SELECTED: str = os.getenv("N8N_WEBHOOK_URL_SELECTED", "")
    N8N_WEBHOOK_URL_REJECTED: str = os.getenv("N8N_WEBHOOK_URL_REJECTED", "")
    N8N_ENABLED: bool = bool(N8N_WEBHOOK_URL_SELECTED and N8N_WEBHOOK_URL_REJECTED)
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
    MAX_PAGE_SIZE: int = int(os.getenv("MAX_PAGE_SIZE", "100"))
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    REQUESTS_PER_MINUTE: int = int(os.getenv("REQUESTS_PER_MINUTE", "60"))
    
    def __init__(self, **data):
        super().__init__(**data)
        # Load API keys from environment - supports comma-separated or numbered pattern
        keys_string = os.getenv("GOOGLE_API_KEYS", "")
        if keys_string:
            self.GOOGLE_API_KEYS = [key.strip().strip('"').strip("'") for key in keys_string.split(",") if key.strip()]
        
        # Fallback to individual numbered keys if comma-separated not found
        if not self.GOOGLE_API_KEYS:
            for i in range(1, 14):
                key = os.getenv(f"GOOGLE_API_KEY_{i}", "")
                if key and "your_google_ai_key_here" not in key:
                    self.GOOGLE_API_KEYS.append(key.strip().strip('"').strip("'"))
        
        # Add legacy single key as fallback
        if not self.GOOGLE_API_KEYS and self.GOOGLE_API_KEY:
            self.GOOGLE_API_KEYS = [self.GOOGLE_API_KEY]

    def get_key_for_agent(self, index: int = 0) -> str:
        """
        Retrieves an API key by index with automatic rotation support.
        Falls back to the first key if index is out of range.
        
        Args:
            index (int): Zero-based index for key selection
            
        Returns:
            str: Sanitized API key or empty string if none available
        """
        if not self.GOOGLE_API_KEYS:
            return ""
        
        # Use modulo for automatic rotation if rotation is enabled
        actual_index = (index % len(self.GOOGLE_API_KEYS)) if self.API_KEY_ROTATION_ENABLED else min(index, len(self.GOOGLE_API_KEYS) - 1)
        return self.GOOGLE_API_KEYS[actual_index] if actual_index < len(self.GOOGLE_API_KEYS) else ""
    
    def get_random_key(self) -> str:
        """Returns a random API key for load balancing."""
        if not self.GOOGLE_API_KEYS:
            return ""
        import random
        return random.choice(self.GOOGLE_API_KEYS)
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # Ignore extra env vars not defined in model

settings = Settings()
