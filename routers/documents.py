"""
Documents Router
Handle file uploads and document management
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

from database import get_db
import models
import schemas
from routers.auth import get_current_user

router = APIRouter()

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.get("/", response_model=List[schemas.DocumentResponse])
async def get_documents(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all documents for the current user"""
    documents = db.query(models.Document).filter(models.Document.user_id == current_user.id).all()
    return documents

@router.post("/upload", response_model=schemas.DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("academic"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document
    """
    # Create valid filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    clean_filename = f"{current_user.id}_{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, clean_filename)
    
    # Save file locally
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Get file size
        file_size = os.path.getsize(file_path)
        size_str = f"{round(file_size / 1024, 1)} KB"
        if file_size > 1024 * 1024:
            size_str = f"{round(file_size / (1024 * 1024), 2)} MB"
            
        # Determine type
        import mimetypes
        file_type = mimetypes.guess_extension(file.content_type) or os.path.splitext(file.filename)[1]
        file_type = file_type.replace(".", "").upper()
            
        # Create DB record
        new_doc = models.Document(
            user_id=current_user.id,
            name=file.filename,
            type=file_type,
            size=size_str,
            category=category,
            status="pending",
            file_path=file_path
        )
        
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)
        
        return new_doc
        
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail="Could not save file")

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    doc = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.user_id == current_user.id
    ).first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Delete physical file
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass # Ignore if file already missing
            
    db.delete(doc)
    db.commit()
    
    return {"message": "Document deleted"}
