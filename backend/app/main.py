from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
from .api.v1 import system 
from .database.mongodb import connect_to_mongo, close_mongo_connection
from .database.vectordb import init_vector_db, shutdown_vector_db
from .core.config import settings
from .api.v1 import candidates, requirements

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    connect_to_mongo()
    init_vector_db()
    yield
    # Shutdown actions
    close_mongo_connection()
    shutdown_vector_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(candidates.router, prefix="/api/candidates", tags=["Candidates"])
app.include_router(requirements.router, prefix="/api/requirements", tags=["Requirements"])
app.include_router(system.router, prefix="/api/system", tags=["System Activity"])

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "status": "Online"
    }
