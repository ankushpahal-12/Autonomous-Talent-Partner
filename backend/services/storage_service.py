import io
from app.database.mongodb import get_gridfs, connect_to_mongo

async def save_file_to_gridfs(file_content: bytes, filename: str) -> str:
    """
    Saves a file's binary content to MongoDB GridFS.
    Returns the string ID of the saved file.
    """
    fs = get_gridfs()
    if fs is None:
        connect_to_mongo()
        fs = get_gridfs()
        
    if fs is None:
        raise Exception("Failed to connect to GridFS bucket.")
        
    grid_in = fs.open_upload_stream(filename)
    await grid_in.write(file_content)
    await grid_in.close()
    
    return str(grid_in._id)

async def get_file_from_gridfs(file_id: str) -> bytes:
    """
    Retrieves a file's binary content from MongoDB GridFS by its ID.
    """
    from bson import ObjectId
    fs = get_gridfs()
    if fs is None:
        connect_to_mongo()
        fs = get_gridfs()
        
    if fs is None:
        raise Exception("Failed to connect to GridFS bucket.")
        
    grid_out = await fs.open_download_stream(ObjectId(file_id))
    return await grid_out.read()

async def delete_file_from_gridfs(file_id: str):
    """
    Deletes a file from MongoDB GridFS by its ID.
    """
    from bson import ObjectId
    fs = get_gridfs()
    if fs is None:
        connect_to_mongo()
        fs = get_gridfs()
        
    if fs is None:
        return
        
    await fs.delete(ObjectId(file_id))
