import os
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

class VectorDatabase:
    store = None

vector_db_instance = VectorDatabase()

def init_vector_db():
    """Initializes the Chroma vector store on startup."""
    print("Initialize Vector Database connection...")
    try:
        if not os.getenv("GOOGLE_API_KEY") or "your_google_ai_key_here" in os.getenv("GOOGLE_API_KEY"):
            print("VectorDB init skipped: Invalid GOOGLE_API_KEY.")
            return

        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        # Define directory relative to the backend base folder
        chroma_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "chroma")
        os.makedirs(chroma_path, exist_ok=True)
        
        vector_db_instance.store = Chroma(
            collection_name="candidates",
            embedding_function=embeddings,
            persist_directory=chroma_path
        )
        print(f"Successfully initialized Vector Database at {chroma_path}")
    except Exception as e:
        print(f"Failed to initialize Vector DB: {e}")

def get_vector_db():
    """Dependency hook to retrieve the current Vector DB store."""
    return vector_db_instance.store

def shutdown_vector_db():
    """Gracefully shuts down resources if needed (Chroma mostly handles this natively)."""
    print("Vector Database connection closed.")
