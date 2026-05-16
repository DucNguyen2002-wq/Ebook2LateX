import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import upload, process, save
from app.core.config import CORS_ORIGINS

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warm pix2tex model khi server khởi động để tránh delay lần đầu."""
    logger.info("[Startup] Đang tải model pix2tex…")
    try:
        from app.services.ocr import _get_model
        _get_model()
        logger.info("[Startup] Model pix2tex đã sẵn sàng.")
    except Exception as e:
        logger.warning("[Startup] Không tải được pix2tex: %s", e)
    yield


app = FastAPI(title="Ebook2LaTeX API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(process.router)
app.include_router(save.router)


@app.get("/")
def read_root():
    return {"message": "Chào mừng bạn đến với Ebook2LaTeX!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        # Bỏ qua thư mục uploads/ và PDF/debug/ khỏi watchfiles
        # để tránh restart khi background task ghi ảnh ra đĩa
        reload_excludes=["uploads", "uploads/*", "PDF"],
    )