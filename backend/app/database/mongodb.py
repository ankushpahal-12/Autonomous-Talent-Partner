"""
MongoDB connection module - now delegates to connection_manager for pooling and reuse.
This module is kept for backward compatibility.
"""

import logging
from .connection_manager import db_manager

logger = logging.getLogger(__name__)

# Legacy class for backward compatibility
class Database:
    client = None
    db = None
    fs = None

db_instance = Database()

async def connect_to_mongo():
    """
    Initializes the connection to the MongoDB cluster using the connection manager.
    Now supports connection pooling and proper resource management.
    """
    from ..core.config import settings
    
    success = await db_manager.connect(
        mongo_uri=settings.MONGO_URI,
        db_name=settings.DATABASE_NAME,
        pool_size=settings.MONGO_POOL_SIZE,
        timeout_ms=settings.MONGO_CONNECTION_TIMEOUT_MS
    )
    
    # Update legacy class for backward compatibility
    if success:
        db_instance.client = db_manager._client
        db_instance.db = db_manager.get_db()
        db_instance.fs = db_manager.get_gridfs()

def get_mongodb():
    """
    Dependency hook to retrieve the database instance.
    Returns the connection-pooled database from the connection manager.
    """
    return db_manager.get_db()

def get_gridfs():
    """
    Dependency hook to retrieve the GridFS instance.
    Returns the GridFS bucket from the connection manager.
    """
    return db_manager.get_gridfs()

async def close_mongo_connection():
    """Closes the active MongoDB connection through the connection manager."""
    await db_manager.disconnect()

