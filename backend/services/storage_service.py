"""
Storage service for managing file operations with GridFS.
Now uses centralized connection management to eliminate redundant checks.
"""

import logging
from typing import Optional
from bson import ObjectId
from app.database.connection_manager import db_manager

logger = logging.getLogger(__name__)

async def save_file_to_gridfs(file_content: bytes, filename: str) -> str:
    """
    Saves a file's binary content to MongoDB GridFS with proper error handling.
    
    Args:
        file_content (bytes): Binary file content
        filename (str): Name of the file
        
    Returns:
        str: String ID of the saved file
        
    Raises:
        RuntimeError: If GridFS is not available
    """
    fs = db_manager.get_gridfs()
    if fs is None:
        error_msg = "GridFS is not available - database connection required"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    try:
        logger.info(f"Saving file to GridFS: {filename}")
        grid_in = fs.open_upload_stream(filename)
        await grid_in.write(file_content)
        await grid_in.close()
        
        file_id = str(grid_in._id)
        logger.info(f"File saved successfully with ID: {file_id}")
        return file_id
        
    except Exception as e:
        logger.error(f"Failed to save file to GridFS: {e}", exc_info=True)
        raise RuntimeError(f"Failed to save file: {str(e)}")

async def get_file_from_gridfs(file_id: str) -> Optional[bytes]:
    """
    Retrieves a file's binary content from MongoDB GridFS by its ID.
    
    Args:
        file_id (str): GridFS file ID
        
    Returns:
        bytes: File content or None if not found
        
    Raises:
        RuntimeError: If GridFS is not available or file not found
    """
    fs = db_manager.get_gridfs()
    if fs is None:
        error_msg = "GridFS is not available - database connection required"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    try:
        logger.info(f"Retrieving file from GridFS: {file_id}")
        object_id = ObjectId(file_id)
        grid_out = await fs.open_download_stream(object_id)
        content = await grid_out.read()
        
        logger.info(f"File retrieved successfully: {file_id}")
        return content
        
    except Exception as e:
        logger.error(f"Failed to retrieve file from GridFS: {e}", exc_info=True)
        raise RuntimeError(f"Failed to retrieve file: {str(e)}")

async def delete_file_from_gridfs(file_id: str) -> bool:
    """
    Deletes a file from MongoDB GridFS by its ID.
    
    Args:
        file_id (str): GridFS file ID
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    fs = db_manager.get_gridfs()
    if fs is None:
        logger.warning("GridFS is not available - cannot delete file")
        return False
    
    try:
        object_id = ObjectId(file_id)
        await fs.delete(object_id)
        logger.info(f"File deleted successfully: {file_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete file from GridFS: {e}")
        return False

async def file_exists_in_gridfs(file_id: str) -> bool:
    """
    Checks if a file exists in GridFS.
    
    Args:
        file_id (str): GridFS file ID
        
    Returns:
        bool: True if file exists, False otherwise
    """
    db = db_manager.get_db()
    if db is None:
        return False
    
    try:
        object_id = ObjectId(file_id)
        file_doc = await db.fs.files.find_one({"_id": object_id})
        return file_doc is not None
    except Exception as e:
        logger.error(f"Error checking file existence: {e}")
        return False

