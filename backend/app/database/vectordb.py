import sys
import os
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

class VectorDatabase:
    store = None

vector_db_instance = VectorDatabase()

from ..core.config import settings

def init_vector_db():
    """Initializes the Chroma vector store on startup."""
    sys.stderr.write("Initialize Vector Database connection...\n")
    try:
        api_key = settings.get_key_for_agent(12)
        if not api_key:
            sys.stderr.write("VectorDB init skipped: Invalid GOOGLE_API_KEY.\n")
            return

        embeddings = GoogleGenerativeAIEmbeddings(api_key=api_key, model="models/gemini-embedding-001")
        
        # Use centralized path
        chroma_path = settings.CHROMA_PATH
        os.makedirs(chroma_path, exist_ok=True)
        
        vector_db_instance.store = Chroma(
            collection_name="candidates",
            embedding_function=embeddings,
            persist_directory=chroma_path
        )
        sys.stderr.write(f"Successfully initialized Vector Database at {chroma_path}\n")
    except Exception as e:
        sys.stderr.write(f"Failed to initialize Vector DB: {e}\n")

def get_vector_db():
    """Dependency hook to retrieve the current Vector DB store."""
    return vector_db_instance.store

def shutdown_vector_db():
    """Gracefully shuts down resources if needed (Chroma mostly handles this natively)."""
    sys.stderr.write("Vector Database connection closed.\n")
