import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

DATABASE_URL: str = os.getenv("DATABASE_URL", "")

# Danh sách origin được phép (phân cách bằng dấu phẩy)
# Ví dụ: http://localhost:3000,https://your-app.vercel.app
_cors_raw: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
CORS_ORIGINS: list[str] = [o.strip() for o in _cors_raw.split(",") if o.strip()]

# Thư mục lưu tạm các tập tin PDF người dùng tải lên
UPLOAD_DIR: str = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
