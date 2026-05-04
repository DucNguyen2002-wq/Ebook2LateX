import uuid

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Text, Numeric

from sqlalchemy.dialects.postgresql import UUID, JSONB

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy.sql import func


# Khởi tạo lớp Base để các Model kế thừa

Base = declarative_base()


class User(Base):

    __tablename__ = 'users'

    

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    username_email = Column(String(255), unique=True, nullable=False)

    password_hash = Column(Text, nullable=False)

    full_name = Column(String(100))

    role = Column(String(20), default='Editor') # Admin, Editor, Viewer

    last_login = Column(DateTime(timezone=True))

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


    # Quan hệ: Một người dùng có thể tải lên nhiều tài liệu

    documents = relationship("Document", back_populates="owner")


class Document(Base):

    __tablename__ = 'documents'

    

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='SET NULL'))

    file_name = Column(Text, nullable=False)

    file_path_url = Column(Text, nullable=False)

    upload_date = Column(DateTime(timezone=True), server_default=func.now())

    status = Column(String(50), default='Pending') # Pending, Processed, Error


    # Quan hệ ngược lại với User

    owner = relationship("User", back_populates="documents")

    # Quan hệ: Một tài liệu có nhiều mục công thức

    formulas = relationship("FormulaEntry", back_populates="document", cascade="all, delete-orphan")


class FormulaEntry(Base):

    __tablename__ = 'formula_entries'

    

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)

    raw_image_path = Column(Text)

    latex_content = Column(Text)

    order_index = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


    # Quan hệ ngược lại với Document

    document = relationship("Document", back_populates="formulas")

    # Quan hệ: Một công thức có thể có nhiều log (nếu chạy OCR nhiều lần)

    logs = relationship("Log", back_populates="formula", cascade="all, delete-orphan")


class Log(Base):

    __tablename__ = 'logs'

    

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    formula_id = Column(UUID(as_uuid=True), ForeignKey('formula_entries.id', ondelete='CASCADE'))

    processing_time_ms = Column(Integer)

    confidence_score = Column(Numeric(3, 2))

    error_type = Column(String(100))

    error_message = Column(Text)

    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    environment_info = Column(JSONB) # Lưu trữ thông số CPU/GPU dưới dạng JSON


    # Quan hệ ngược lại với FormulaEntry

    formula = relationship("FormulaEntry", back_populates="logs")