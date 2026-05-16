import logging
import os
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import UPLOAD_DIR
from app.database import SessionLocal
from app.models import Document, FormulaEntry
from app.schemas.formula import FormulaOut, ProcessResult
from app.services.ocr import run_ocr
from app.services.pdf_parser import extract_formula_images, image_bytes_to_base64

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["process"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _do_process(document_id: UUID) -> None:
    """Xử lý tài liệu trong background: trích xuất ảnh, OCR, lưu kết quả."""
    logger.info("[BG] Bắt đầu xử lý document %s", document_id)
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.warning("[BG] Không tìm thấy document %s", document_id)
            return

        # Xóa các công thức cũ nếu xử lý lại
        db.query(FormulaEntry).filter(FormulaEntry.document_id == doc.id).delete()
        doc.status = "Processing"
        db.commit()
        logger.info("[BG] Status → Processing")

        # Thư mục lưu ảnh công thức của tài liệu này
        img_dir = os.path.join(UPLOAD_DIR, str(document_id))
        os.makedirs(img_dir, exist_ok=True)

        logger.info("[BG] Trích xuất công thức từ PDF…")
        images = extract_formula_images(doc.file_path_url)
        total = len(images)
        logger.info("[BG] Tìm thấy %d công thức, bắt đầu OCR…", total)

        for order_index, image_bytes in images:
            # Lưu ảnh ra đĩa (dùng raw_image_path)
            img_path = os.path.join(img_dir, f"{order_index}.png")
            with open(img_path, "wb") as f:
                f.write(image_bytes)

            logger.info("[BG] OCR công thức %d/%d…", order_index + 1, total)
            latex = run_ocr(image_bytes)
            logger.info("[BG] OCR xong %d/%d: %s", order_index + 1, total, repr((latex or "")[:60]))

            entry = FormulaEntry(
                document_id=doc.id,
                latex_content=latex or "",
                order_index=order_index,
                raw_image_path=img_path,
            )
            db.add(entry)
            db.commit()  # commit ngay từng công thức — kết quả hiện dần

        doc.status = "Processed"
        db.commit()
        logger.info("[BG] Hoàn thành! Status → Processed (%d công thức)", total)

    except Exception as exc:
        logger.exception("[BG] Lỗi khi xử lý document %s: %s", document_id, exc)
        try:
            doc.status = "Error"
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.post("/process/{document_id}", status_code=202)
def process_document(
    document_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Bắt đầu xử lý tài liệu trong background, trả về ngay lập tức."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")

    background_tasks.add_task(_do_process, document_id)
    return {"status": "Processing", "document_id": str(document_id)}


@router.get("/process/{document_id}/status", response_model=ProcessResult)
def get_process_status(document_id: UUID, db: Session = Depends(get_db)):
    """Kiểm tra trạng thái xử lý và lấy kết quả khi hoàn thành."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")

    if doc.status == "Error":
        raise HTTPException(status_code=500, detail="Xử lý tài liệu thất bại.")

    if doc.status != "Processed":
        # Đang xử lý — trả về trạng thái hiện tại, chưa có công thức
        return ProcessResult(
            document_id=doc.id,
            status=doc.status,
            formulas=[],
        )

    entries = (
        db.query(FormulaEntry)
        .filter(FormulaEntry.document_id == doc.id)
        .order_by(FormulaEntry.order_index)
        .all()
    )

    formulas = []
    for entry in entries:
        image_b64 = None
        if entry.raw_image_path and os.path.exists(entry.raw_image_path):
            with open(entry.raw_image_path, "rb") as f:
                image_b64 = image_bytes_to_base64(f.read())
        formulas.append(
            FormulaOut(
                id=entry.id,
                order_index=entry.order_index,
                latex_content=entry.latex_content,
                image_base64=image_b64,
                created_at=entry.created_at,
                updated_at=entry.updated_at,
            )
        )

    return ProcessResult(document_id=doc.id, status="Processed", formulas=formulas)

