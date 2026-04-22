"""
Centralized database connection management with connection pooling.
Eliminates the need for repeated connection checks in every service.
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorGridFSBucket
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Singleton database manager for MongoDB with connection pooling and graceful fallback.
    Ensures connections are reused and properly managed across the application.
    """
    
    _instance: Optional['DatabaseManager'] = None
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None
    _fs: Optional[AsyncIOMotorGridFSBucket] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._is_connected = False
    
    async def connect(self, mongo_uri: str, db_name: str, pool_size: int = 10, timeout_ms: int = 5000) -> bool:
        """
        Establishes MongoDB connection with pooling and proper URL configuration.
        Handles SSL/TLS issues on Windows systems.
        
        Args:
            mongo_uri (str): MongoDB connection string
            db_name (str): Database name
            pool_size (int): Connection pool size
            timeout_ms (int): Connection timeout in milliseconds
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        if self._is_connected:
            logger.warning("Database already connected, skipping reconnection")
            return True
        
        if not mongo_uri or "your_google_ai_key_here" in mongo_uri or "<password>" in mongo_uri:
            logger.warning("MongoDB connection skipped: Invalid or placeholder URI. Please update .env")
            return False
        
        try:
            logger.info("Connecting to MongoDB with connection pooling...")
            
            # Add retry writes and connection pool parameters to URI
            separator = "&" if "?" in mongo_uri else "?"
            uri_params = []
            
            if "retryWrites" not in mongo_uri:
                uri_params.append("retryWrites=true")
            if "w=" not in mongo_uri:
                uri_params.append("w=majority")
            
            # Add additional URI parameters for SSL handling
            if uri_params:
                mongo_uri += separator + "&".join(uri_params)
            
            # Create client with connection pooling and SSL configuration
            # PyMongo/Motor SSL parameters for Windows compatibility
            self._client = AsyncIOMotorClient(
                mongo_uri,
                tls=True,
                tlsInsecure=True,  # Disable hostname verification and cert validation for development
                serverSelectionTimeoutMS=timeout_ms,
                connectTimeoutMS=timeout_ms,
                socketTimeoutMS=timeout_ms,
                maxPoolSize=pool_size,
                minPoolSize=1,
                maxIdleTimeMS=60000,  # Close idle connections after 60s
                waitQueueTimeoutMS=10000,  # Wait up to 10s for available connection
            )
            
            # Test connection with timeout
            logger.info("Testing MongoDB connection...")
            await self._client.admin.command('ping')
            
            self._db = self._client[db_name]
            self._fs = AsyncIOMotorGridFSBucket(self._db)
            self._is_connected = True
            
            logger.info(f"Successfully connected to MongoDB database: {db_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            logger.error("Please verify your MongoDB URI in .env and check your network connection")
            self._is_connected = False
            return False
    
    async def disconnect(self) -> None:
        """Gracefully closes MongoDB connections."""
        if self._client is not None:
            try:
                self._client.close()
                self._is_connected = False
                logger.info("MongoDB connection gracefully closed")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {e}")
    
    def get_db(self) -> Optional[AsyncIOMotorDatabase]:
        """Returns the current database instance."""
        if not self._is_connected:
            logger.warning("Database not connected. Returning None.")
        return self._db
    
    def get_gridfs(self) -> Optional[AsyncIOMotorGridFSBucket]:
        """Returns the current GridFS instance."""
        if not self._is_connected:
            logger.warning("Database not connected. Returning None.")
        return self._fs
    
    def is_connected(self) -> bool:
        """Returns connection status."""
        return self._is_connected
    
    @asynccontextmanager
    async def get_collection(self, collection_name: str):
        """
        Context manager for safe collection access.
        
        Args:
            collection_name (str): Name of the collection
            
        Yields:
            AsyncIOMotorCollection: The requested collection or None if not connected
        """
        if not self._is_connected or self._db is None:
            logger.error(f"Cannot access collection '{collection_name}': Database not connected")
            yield None
        else:
            yield self._db[collection_name]

# Global instance
db_manager = DatabaseManager()

# Legacy compatibility functions
async def connect_to_mongo(mongo_uri: str, db_name: str, pool_size: int = 10, timeout_ms: int = 5000) -> bool:
    """Connect to MongoDB (legacy function)."""
    return await db_manager.connect(mongo_uri, db_name, pool_size, timeout_ms)

async def close_mongo_connection() -> None:
    """Close MongoDB connection (legacy function)."""
    await db_manager.disconnect()

def get_mongodb() -> Optional[AsyncIOMotorDatabase]:
    """Get database instance (legacy function)."""
    return db_manager.get_db()

def get_gridfs() -> Optional[AsyncIOMotorGridFSBucket]:
    """Get GridFS instance (legacy function)."""
    return db_manager.get_gridfs()

def is_db_connected() -> bool:
    """Check if database is connected."""
    return db_manager.is_connected()
