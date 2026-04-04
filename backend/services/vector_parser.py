import os
import json
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# We will store Chroma DB locally in the backend/data directory
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma")

def get_vector_store():
    """Initializes and returns the Chroma vector store instance."""
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    # Create the directory if it doesn't exist
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    
    vector_store = Chroma(
        collection_name="candidates",
        embedding_function=embeddings,
        persist_directory=CHROMA_PERSIST_DIR
    )
    return vector_store

def embed_candidate_data(candidate_data: dict) -> bool:
    """
    Takes parsed candidate JSON data, creates a combined textual representation
    for semantic search, generates an embedding, and stores it in Chroma.
    
    Returns True if successfully embedded.
    """
    vector_store = get_vector_store()
    
    # 1. Prepare text to embed
    candidate_id = candidate_data.get("candidate_id", "unknown_id")
    name = candidate_data.get("name", "Unknown Candidate")
    skills = ", ".join(candidate_data.get("skills", []))
    projects = " | ".join(candidate_data.get("projects", []))
    
    # The text representation should be rich so standard RAG works well on it
    page_content = f"Candidate Name: {name}\n"
    page_content += f"Skills: {skills}\n"
    page_content += f"Projects: {projects}\n"
    
    # 2. Add metadata
    metadata = {
        "candidate_id": candidate_id,
        "name": name,
        "status": candidate_data.get("status", "pending_review")
    }
    
    doc = Document(page_content=page_content, metadata=metadata)
    
    # 3. Add to Chroma
    vector_store.add_documents([doc])
    
    return True

def search_candidates_by_job_description(job_description: str, k: int = 3) -> list:
    """
    Search for top k candidates that match a given job description.
    """
    vector_store = get_vector_store()
    results = vector_store.similarity_search_with_score(job_description, k=k)
    
    formatted_results = []
    for doc, score in results:
        formatted_results.append({
            "candidate_id": doc.metadata.get("candidate_id"),
            "name": doc.metadata.get("name"),
            "content": doc.page_content,
            "score": score
        })
    
    return formatted_results

if __name__ == "__main__":
    # Local test
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        dummy_data = {
            "candidate_id": "test_123",
            "name": "Jane Doe",
            "email": "jane@example.com",
            "skills": ["Python", "Machine Learning", "FastAPI", "React"],
            "projects": ["Built an AI Resume Parser using LangChain", "Developed a React Dashboard"],
            "status": "pending_review"
        }
        print("Embedding test data...", dummy_data["candidate_id"])
        embed_candidate_data(dummy_data)
        print("Done. Now searching for 'Python API expert'...")
        res = search_candidates_by_job_description("Python API expert", k=1)
        print("Results:")
        print(json.dumps(res, indent=2))
