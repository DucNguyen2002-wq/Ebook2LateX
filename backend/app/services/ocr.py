"""
Dịch vụ OCR: chuyển ảnh công thức toán sang chuỗi LaTeX.

Ưu tiên sử dụng pix2tex (chạy local, miễn phí).
Nếu pix2tex chưa được cài, fallback sang Mathpix API.
"""
import io
import logging
import os
import warnings
from typing import Optional

# Tắt thông báo cập nhật Albumentations
os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

# Bỏ qua cảnh báo Pydantic serialization từ nội bộ pix2tex/Albumentations
warnings.filterwarnings(
    "ignore",
    message="Pydantic serializer warnings",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message=".*PydanticSerializationUnexpectedValue.*",
    category=UserWarning,
)

from PIL import Image

logger = logging.getLogger(__name__)

# Load model một lần duy nhất khi module được import
_pix2tex_model = None

def _get_model():
    global _pix2tex_model
    if _pix2tex_model is None:
        try:
            from pix2tex.cli import LatexOCR  # type: ignore
            logger.info("Đang tải model pix2tex lần đầu…")
            _pix2tex_model = LatexOCR()
            logger.info("Model pix2tex đã sẵn sàng.")
        except ImportError:
            _pix2tex_model = None
    return _pix2tex_model


def run_ocr(image_bytes: bytes) -> Optional[str]:
    """Nhận bytes ảnh PNG, trả về chuỗi LaTeX tương ứng."""
    model = _get_model()
    if model is not None:
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            return model(img) #trả về chuỗi LaTeX
        except Exception as e:
            logger.warning("pix2tex lỗi: %s", e)

    # Fallback: Mathpix API
    return _run_mathpix_api(image_bytes)


def _run_mathpix_api(image_bytes: bytes) -> Optional[str]:
    """
    Gọi Mathpix Snip API để OCR công thức.
    Cần khai báo MATHPIX_APP_ID và MATHPIX_APP_KEY trong tập tin .env.
    """
    import os
    import base64

    app_id = os.getenv("MATHPIX_APP_ID")
    app_key = os.getenv("MATHPIX_APP_KEY")
    if not app_id or not app_key:
        return None

    try:
        import httpx

        image_b64 = base64.b64encode(image_bytes).decode()
        resp = httpx.post(
            "https://api.mathpix.com/v3/text",
            headers={"app_id": app_id, "app_key": app_key},
            json={
                "src": f"data:image/png;base64,{image_b64}",
                "formats": ["latex_simplified"],
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("latex_simplified")
    except Exception as e:
        logger.warning("Mathpix API lỗi: %s", e)
        return None
