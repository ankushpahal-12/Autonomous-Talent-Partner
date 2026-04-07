import os
import json
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.core.config import settings

def get_vector_store(collection_name="candidates"):
    """Initializes and returns the Chroma vector store instance using centralized settings."""
    api_key = settings.GOOGLE_API_KEY
    embeddings = GoogleGenerativeAIEmbeddings(api_key=api_key, model="models/gemini-embedding-001")
    
    # Use centralized path from core config
    chroma_path = settings.CHROMA_PATH
    os.makedirs(chroma_path, exist_ok=True)
    
    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=chroma_path
    )
    return vector_store

def embed_candidate_data(candidate_data: dict) -> bool:
    """
    Takes parsed candidate JSON data, creates a combined textual representation
    for semantic search, generates an embedding, and stores it in Chroma.
    
    Returns True if successfully embedded.
    """
    vector_store = get_vector_store(collection_name="candidates")
    
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

def embed_job_requirement(req_id: str, title: str, text: str) -> bool:
    """
    Embeds a job requirement document into a separate Chroma collection.
    """
    vector_store = get_vector_store(collection_name="job_requirements")
    
    metadata = {
        "req_id": req_id,
        "title": title
    }
    
    doc = Document(page_content=text, metadata=metadata)
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

async def evaluate_candidate_with_rag(candidate_text: str, requirement_id: str) -> str:
    """
    Retrieves the job requirement context and reasons over the candidate using a LangChain RAG chain.
    """
    from langchain_core.prompts import PromptTemplate
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    req_vector_store = get_vector_store(collection_name="job_requirements")
    retriever = req_vector_store.as_retriever(
        search_kwargs={'filter': {'req_id': requirement_id}, 'k': 2}
    )
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)
    
    template = """You are an expert technical AI recruiter.
    Evaluate the candidate's profile based strictly on the retrieved Job Requirement context.
    
    Job Requirement Context:
    {context}
    
    Candidate Profile:
    {candidate}
    
    Provide a detailed reasoning of whether this candidate is a good match for the job requirements.
    Highlight matched skills and missing critical skills.
    
    Reasoning:"""
    
    prompt = PromptTemplate.from_template(template)
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    rag_chain = (
        {"context": retriever | format_docs, "candidate": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return await rag_chain.ainvoke(candidate_text)

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
