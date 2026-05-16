import os
import uuid
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import UPLOAD_DIR
from app.database import SessionLocal
from app.models import Document
from app.schemas.document import DocumentOut

router = APIRouter(prefix="/api", tags=["upload"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload", response_model=DocumentOut)
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Nhận tập tin PDF, lưu vào thư mục uploads và tạo bản ghi Document."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận tập tin PDF.")

    file_id = str(uuid.uuid4())
    save_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc = Document(
        file_name=file.filename,
        file_path_url=save_path,
        status="Pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc
