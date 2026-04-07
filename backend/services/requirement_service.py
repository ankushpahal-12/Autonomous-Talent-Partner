import io
import docx
from pypdf import PdfReader
from app.database.mongodb import get_mongodb, connect_to_mongo
from services.storage_service import get_file_from_gridfs

async def _get_requirements_collection():
    """Helper to ensure DB connection is active and returns the job_requirements collection."""
    db = get_mongodb()
    if db is None:
        connect_to_mongo()
        db = get_mongodb()
    if db is None:
        return None
    return db["job_requirements"]

def extract_text_from_pdf(pdf_stream: io.BytesIO) -> str:
    """Read a PDF from a byte stream and extract its text."""
    reader = PdfReader(pdf_stream)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def extract_text_from_docx(docx_stream: io.BytesIO) -> str:
    """Read a DOCX from a byte stream and extract its text."""
    doc = docx.Document(docx_stream)
    text = []
    for para in doc.paragraphs:
        text.append(para.text)
    return "\n".join(text)

def extract_text_from_txt(txt_stream: io.BytesIO) -> str:
    """Read a TXT from a byte stream and extract its text."""
    return txt_stream.read().decode('utf-8', errors='ignore')

async def extract_text_from_gridfs(gridfs_id: str, filename: str) -> str:
    """Fetches requirement from GridFS and extracts text in-memory."""
    file_bytes = await get_file_from_gridfs(gridfs_id)
    stream = io.BytesIO(file_bytes)
    
    if filename.lower().endswith(".pdf"):
        return extract_text_from_pdf(stream)
    elif filename.lower().endswith(".docx"):
        return extract_text_from_docx(stream)
    else:
        return extract_text_from_txt(stream)

async def save_requirement_metadata(req_id: str, filename: str, gridfs_id: str, title: str, extracted_text: str = "") -> bool:
    """Save requirement metadata including full extracted description to MongoDB."""
    collection = await _get_requirements_collection()
    if collection is None:
        return False
        
    document = {
        "_id": req_id,
        "title": title,
        "filename": filename,
        "gridfs_id": gridfs_id,
        "extracted_text": extracted_text,
        "status": "active"
    }
    
    try:
        await collection.update_one(
            {"_id": req_id},
            {"$set": document},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Failed to save requirement metadata: {e}")
        return False

async def get_all_requirements():
    """Retrieve all job requirements from MongoDB."""
    collection = await _get_requirements_collection()
    if collection is None:
        return []
    
    requirements = []
    async for doc in collection.find({}):
        requirements.append(doc)
    return requirements

async def delete_requirement(requirement_id: str) -> bool:
    """Removes a job requirement from MongoDB by its ID."""
    collection = await _get_requirements_collection()
    if collection is None:
        return False
        
    try:
        result = await collection.delete_one({"_id": requirement_id})
        return result.deleted_count > 0
    except Exception as e:
        import sys
        sys.stderr.write(f"Failed to delete requirement: {e}\n")
        return False
