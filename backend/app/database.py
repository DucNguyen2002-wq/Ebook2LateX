import os

from dotenv import load_dotenv

from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker, declarative_base


# Tải các biến môi trường từ tập tin .env

load_dotenv()


# 1. Lấy chuỗi kết nối từ biến môi trường (Supabase Transaction Pooler)

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Supabase dùng PgBouncer (Transaction mode, port 6543) → cần tắt prepared statements
# để tránh lỗi "prepared statement does not exist"
_connect_args: dict = {}
if SQLALCHEMY_DATABASE_URL and "pooler.supabase.com" in SQLALCHEMY_DATABASE_URL:
    _connect_args = {"options": "-c statement_timeout=30000"}

# 2. Tạo Engine: Đây là "nguồn" kết nối chính tới Database
# pool_pre_ping=True: tự kiểm tra kết nối trước khi dùng (quan trọng với cloud DB)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
)


# 3. Tạo SessionLocal: Mỗi thực thể của lớp này sẽ là một phiên làm việc database

# autocommit=False: Đảm bảo dữ liệu chỉ được lưu khi ta ra lệnh commit()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 4. Tạo Base class: Các models (User, Document...) sẽ kế thừa từ đây

Base = declarative_base()