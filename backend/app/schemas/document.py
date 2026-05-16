from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class DocumentOut(BaseModel):
    id: UUID
    file_name: str
    status: str
    upload_date: datetime

    model_config = {"from_attributes": True}
