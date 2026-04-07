import certifi
import sys
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from dotenv import load_dotenv

load_dotenv()

class Database:
    client: AsyncIOMotorClient = None
    db = None
    fs = None

db_instance = Database()

from ..core.config import settings

def connect_to_mongo():
    """Initializes the connection to the MongoDB cluster."""
    mongo_uri = settings.MONGO_URI
    db_name = settings.DATABASE_NAME
    
    # We will fallback to attempting a connection but avoid throwing an error
    # instantly if it's missing just so the app can start up if needed.
    
    try:
        if mongo_uri and "your_google_ai_key_here" not in mongo_uri and "<password>" not in mongo_uri:
            sys.stderr.write("Connecting to MongoDB Cluster...\n")
            
            # Standard Atlas Tuning
            if "retryWrites" not in mongo_uri:
                separator = "&" if "?" in mongo_uri else "?"
                mongo_uri += f"{separator}retryWrites=true&w=majority"

            db_instance.client = AsyncIOMotorClient(
                mongo_uri, 
                tls=True,
                serverSelectionTimeoutMS=5000, # Fail faster if connection times out
                tlsAllowInvalidCertificates=True # Development fallback for SSL alerts
            )
            db_instance.db = db_instance.client[db_name]
            # Initialize GridFS bucket
            db_instance.fs = AsyncIOMotorGridFSBucket(db_instance.db)
            sys.stderr.write("Successfully connected to MongoDB Cluster and GridFS.\n")
        else:
            sys.stderr.write("MongoDB Connection skipped: Using default or placeholder URI. Please update .env\n")
    except Exception as e:
        sys.stderr.write(f"Failed to connect to MongoDB: {e}\n")

def get_mongodb():
    """Dependency hook to retrieve the database instance."""
    return db_instance.db

def get_gridfs():
    """Dependency hook to retrieve the GridFS instance."""
    return db_instance.fs

def close_mongo_connection():
    """Closes the active MongoDB connection."""
    if db_instance.client is not None:
        db_instance.client.close()
        print("MongoDB connection gracefully closed.")
