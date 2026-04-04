import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from dotenv import load_dotenv

load_dotenv()

class Database:
    client: AsyncIOMotorClient = None
    db = None
    fs = None

db_instance = Database()

def connect_to_mongo():
    """Initializes the connection to the MongoDB cluster."""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB_NAME", "talent_partner_db")
    
    # We will fallback to attempting a connection but avoid throwing an error
    # instantly if it's missing just so the app can start up if needed.
    
    try:
        if mongo_uri and "your_google_ai_key_here" not in mongo_uri and "<password>" not in mongo_uri:
            print("Connecting to MongoDB Cluster...")
            db_instance.client = AsyncIOMotorClient(mongo_uri)
            db_instance.db = db_instance.client[db_name]
            # Initialize GridFS bucket
            db_instance.fs = AsyncIOMotorGridFSBucket(db_instance.db)
            print("Successfully connected to MongoDB Cluster and GridFS.")
        else:
            print("MongoDB Connection skipped: Using default or placeholder URI. Please update .env")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")

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
