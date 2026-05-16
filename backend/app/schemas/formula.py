from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class FormulaOut(BaseModel):
    id: UUID
    order_index: int
    latex_content: Optional[str]
    image_base64: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FormulaUpdate(BaseModel):
    latex_content: str


class ProcessResult(BaseModel):
    document_id: UUID
    status: str = "Processed"
    formulas: list[FormulaOut]
