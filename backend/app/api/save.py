from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import FormulaEntry
from app.schemas.formula import FormulaOut, FormulaUpdate

router = APIRouter(prefix="/api", tags=["save"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.put("/save/{formula_id}", response_model=FormulaOut)
def save_formula(formula_id: UUID, payload: FormulaUpdate, db: Session = Depends(get_db)):
    """Lưu nội dung LaTeX đã chỉnh sửa vào database (FR3)."""
    entry = db.query(FormulaEntry).filter(FormulaEntry.id == formula_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Công thức không tồn tại.")

    entry.latex_content = payload.latex_content
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/documents/{document_id}/formulas", response_model=list[FormulaOut])
def get_formulas(document_id: UUID, db: Session = Depends(get_db)):
    """Lấy danh sách công thức của một tài liệu theo thứ tự."""
    return (
        db.query(FormulaEntry)
        .filter(FormulaEntry.document_id == document_id)
        .order_by(FormulaEntry.order_index)
        .all()
    )
