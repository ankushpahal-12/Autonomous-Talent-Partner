from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

from .database.mongodb import connect_to_mongo, close_mongo_connection
from .database.vectordb import init_vector_db, shutdown_vector_db
from mcp_server import process_and_embed_resume

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    connect_to_mongo()
    init_vector_db()
    
    # Ensure resumes upload dir exists
    os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "resumes"), exist_ok=True)
    yield
    
    # Shutdown actions
    close_mongo_connection()
    shutdown_vector_db()

# Initialize the main FastAPI application with our custom lifespan setup
app = FastAPI(
    title="Autonomous Talent Partner API",
    description="Backend API for the autonomous hiring and multi-agent AI system.",
    version="1.0.0",
    lifespan=lifespan
)

# Securely bind CORSMiddleware to allow frontend (Vite mapping)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Autonomous Talent Partner API",
        "status": "Online and running successfully!"
    }

from services.db_service import initial_save_candidate, update_candidate_parsed, get_all_candidates, get_candidate_by_id, update_candidate_decision

@app.get("/api/candidates")
async def list_candidates():
    candidates = await get_all_candidates()
    return candidates

@app.get("/api/candidates/{candidate_id}")
async def fetch_candidate(candidate_id: str):
    candidate = await get_candidate_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

@app.patch("/api/candidates/{candidate_id}/decision")
async def update_decision(candidate_id: str, payload: dict):
    decision = payload.get("decision") # "selected" or "rejected"
    reason = payload.get("reason", "")
    
    success = await update_candidate_decision(candidate_id, decision, reason)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update recruitment decision.")
    
    return {"status": "success", "message": f"Candidate marked as {decision}"}

import tempfile
from services.storage_service import save_file_to_gridfs

@app.post("/api/upload-resume")
async def upload_resume_endpoint(file: UploadFile = File(...)):
    """
    Receives PDF from frontend, saves it permanently to MongoDB GridFS,
    creates a transient local temp file for processing, and triggers the MCP tool.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")
        
    try:
        content = await file.read()
        
        # 1. Save to MongoDB GridFS (Permanent Storage)
        gridfs_id = await save_file_to_gridfs(content, file.filename)
        
        # 2. Use a temporary file for the processing pipeline
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
            
        try:
            # We can dynamically generate an ID from filename or randomly
            candidate_id = file.filename.replace(".pdf", "").replace(" ", "_").lower()
            
            # 3. Trigger the advanced MCP process pipeline (passing the temp path)
            result_json_str = await process_and_embed_resume(tmp_path, candidate_id, gridfs_id)
            
            return {
                "status": "success",
                "message": "Resume uploaded to MongoDB and processing completed.",
                "gridfs_id": gridfs_id,
                "data": result_json_str
            }
        finally:
            # 4. Ensure cleanup of the temporary file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GridFS upload/processing failed: {str(e)}")

