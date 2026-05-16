"""
pdf_parser.py — Trích xuất công thức toán học từ PDF dùng PyMuPDF.

Chiến lược (block-level font detection):
- CMEX10 xuất hiện trong block → chắc chắn là display formula (∑ ∫ ngoặc lớn)
- CMSY + tỉ lệ ký tự văn bản < 15% → công thức ký hiệu nhỏ
"""

import base64
from typing import List, Tuple

import fitz  # PyMuPDF

# ---------------------------------------------------------------------------
# Cấu hình
# ---------------------------------------------------------------------------

# Font văn bản thông thường (không phải toán)
_TEXT_FONTS = (
    "cmr",          # Computer Modern Roman (body text)
    "cmbx",         # Computer Modern Bold (headings)
    "cmti",         # Computer Modern Text Italic (emphasis)
    "libertinus",   # Libertinus Serif (body text)
    "sfrm",         # Sans-Serif Roman
    "times", "arial", "helvetica", "georgia",
    "palatino", "garamond", "calibri", "cambria", "verdana",
)

# Ngưỡng non-math ratio cho công thức không có CMEX (rule CMSY)
_MAX_TEXT_RATIO_NO_CMEX = 0.15

# Ngưỡng non-math ratio cho CMEX blocks
# Công thức thực sự có equation numbers → ratio tối đa ~0.71
# Đoạn văn bản với inline CMEX → ratio ≥ 0.78
_MAX_TEXT_RATIO_CMEX = 0.75

# Ngưỡng non-math ratio khi block có cả CMSY lẫn CMMI (math italic)
# CMMI chỉ xuất hiện trong công thức → nới lỏng ngưỡng lên 0.50
_MAX_TEXT_RATIO_CMSY_CMMI = 0.50

# Nếu block chứa CMEX/CMSY VÀ chiều rộng < _NARROW_RATIO × text_col_width
# → là fragment công thức hiển thị (display math luôn nhỏ hơn cột văn bản)
_NARROW_FORMULA_RATIO = 0.45

SCALE = 3   # độ phân giải render (3× = rõ nét cho OCR)
PAD   = 8   # padding quanh công thức (points)
_MIN_H = 8  # chiều cao tối thiểu của vùng công thức


# ---------------------------------------------------------------------------
# Hàm phân tích block
# ---------------------------------------------------------------------------

def _analyse_block(block: dict) -> tuple[bool, bool, bool, float]:
    """
    Trả về (has_cmex, has_cmsy, has_cmmi, non_math_ratio).

    has_cmex  — block chứa font CMEX (ký hiệu lớn ∑ ∫ …) → display formula chắc chắn
    has_cmsy  — block chứa font CMSY (ký hiệu toán ≤ ≥ → …)
    has_cmmi  — block chứa font CMMI (math italic, chỉ dùng trong công thức)
    non_math_ratio — tỉ lệ ký tự thuộc font văn bản thông thường
    """
    total = 0
    non_math = 0
    has_cmex = False
    has_cmsy = False
    has_cmmi = False

    for line in block.get("lines", []):
        for span in line.get("spans", []):
            fl = span.get("font", "").lower()
            n = len(span.get("chars", []))
            total += n
            if "cmex" in fl:
                has_cmex = True
            if "cmsy" in fl:
                has_cmsy = True
            if "cmmi" in fl:
                has_cmmi = True
            if any(k in fl for k in _TEXT_FONTS):
                non_math += n

    ratio = non_math / total if total > 0 else 1.0
    return has_cmex, has_cmsy, has_cmmi, ratio


def _block_is_formula(block: dict, text_col_width: float = 0) -> bool:
    """
    True nếu block là display formula.

    Quy tắc (theo thứ tự ưu tiên):
    1. Có CMEX + non_math_ratio < 0.75 → display formula (∑ ∫ ngoặc lớn).
       Ngưỡng 0.75 loại đoạn văn bản có inline CMEX (ratio ≥ 0.78).
    2. Có CMSY + CMMI + ratio < 0.50 → fragment công thức (subscript/script).
       CMMI chỉ xuất hiện trong công thức → nới ngưỡng từ 0.15 lên 0.50.
    3. Block hẹp (< 45 % cột văn bản) với CMEX/CMSY → fragment nhỏ của
       display math (vd: "arg max" viết bằng CMR, hay ngoặc đơn lẻ).
    """
    has_cmex, has_cmsy, has_cmmi, text_ratio = _analyse_block(block)

    # Rule 1: ký hiệu lớn CMEX chiếm ưu thế
    if has_cmex and text_ratio < _MAX_TEXT_RATIO_CMEX:
        return True

    # Rule 2: CMSY + CMMI (đồng thời) trong block không quá nhiều text
    if (has_cmex or has_cmsy) and has_cmmi and text_ratio < _MAX_TEXT_RATIO_CMSY_CMMI:
        return True

    # Rule 3: block hẹp chứa ký hiệu toán → fragment của công thức hiển thị
    if text_col_width > 0 and (has_cmex or has_cmsy):
        block_width = fitz.Rect(block["bbox"]).width
        if block_width < text_col_width * _NARROW_FORMULA_RATIO:
            return True

    return False


# ---------------------------------------------------------------------------
# Gộp các bbox gần nhau thành một công thức hoàn chỉnh
# ---------------------------------------------------------------------------

# Khoảng cách dọc tối đa (points) giữa hai block để coi là cùng một công thức
# ~12pt = nhỏ hơn khoảng cách giữa các dòng văn bản (~14.4pt)
_MERGE_V_GAP = 12


def _merge_formula_bboxes(rects: list) -> list:
    """
    Gộp các fitz.Rect gần nhau theo chiều dọc thành một bbox lớn hơn.

    Thuật toán:
    1. Sắp xếp theo y0.
    2. Nếu hai bbox liên tiếp có khoảng cách dọc <= _MERGE_V_GAP → hợp nhất.
    """
    if not rects:
        return []
    sorted_rects = sorted(rects, key=lambda r: r.y0)
    merged = [sorted_rects[0]]
    for r in sorted_rects[1:]:
        last = merged[-1]
        if r.y0 <= last.y1 + _MERGE_V_GAP:
            merged[-1] = last | r   # hợp nhất hai bbox
        else:
            merged.append(r)
    return merged


# ---------------------------------------------------------------------------
# Hàm chính
# ---------------------------------------------------------------------------

def extract_formula_images(pdf_path: str) -> List[Tuple[int, bytes]]:
    """
    Trích xuất ảnh công thức toán học từ PDF.

    Trả về danh sách (order_index, png_bytes) theo thứ tự xuất hiện trong tài liệu.
    """
    doc = fitz.open(pdf_path)
    results: List[Tuple[int, bytes]] = []
    order = 0
    mat = fitz.Matrix(SCALE, SCALE)

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_dict = page.get_text("rawdict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        all_text_blocks = [b for b in page_dict.get("blocks", []) if b.get("type") == 0]

        # Chiều rộng cột văn bản = chiều rộng lớn nhất của bất kỳ block nào
        # (văn bản body luôn trải full cột; công thức hiển thị thì hẹp hơn nhiều)
        text_col_width = max(
            (fitz.Rect(b["bbox"]).width for b in all_text_blocks),
            default=0,
        )

        # Bước 1: Thu thập bbox của tất cả formula blocks
        formula_rects = []
        for block in all_text_blocks:
            if not _block_is_formula(block, text_col_width):
                continue
            bbox = fitz.Rect(block["bbox"])
            if bbox.height >= _MIN_H:
                formula_rects.append(bbox)

        if not formula_rects:
            continue

        # Bước 2: Gộp các block gần nhau theo chiều dọc
        merged = _merge_formula_bboxes(formula_rects)

        # Bước 3: Mở rộng theo chiều NGANG (x) — lấy block nằm bên cạnh công thức
        # (vd: số thứ tự phương trình "(3.1)" ở cột phải).
        # Chỉ mở rộng x0/x1, KHÔNG mở rộng y — tránh hiệu ứng snowball kéo text xung quanh.
        # Dùng y-range của merged region gốc làm điều kiện lọc (không thay đổi).
        expanded = []
        for region in merged:
            x0, y0, x1, y1 = region.x0, region.y0, region.x1, region.y1
            for block in all_text_blocks:
                b = fitz.Rect(block["bbox"])
                y_center = (b.y0 + b.y1) / 2
                if y0 <= y_center <= y1:
                    x0 = min(x0, b.x0)
                    x1 = max(x1, b.x1)
            expanded.append(fitz.Rect(x0, y0, x1, y1))

        # Bước 4: Gộp lại lần nữa (mở rộng có thể tạo ra các vùng giao nhau mới)
        final = _merge_formula_bboxes(expanded)

        for region in final:
            # Bỏ qua các vùng quá nhỏ (fragment)
            if region.width < 20:
                continue

            clip = fitz.Rect(
                region.x0 - PAD, region.y0 - PAD,
                region.x1 + PAD, region.y1 + PAD,
            ) & page.rect

            if clip.is_empty:
                continue

            pix = page.get_pixmap(matrix=mat, clip=clip)
            results.append((order, pix.tobytes("png")))
            order += 1

    doc.close()
    return results


def image_bytes_to_base64(image_bytes: bytes) -> str:
    """Chuyển bytes ảnh sang chuỗi base64 để trả về JSON."""
    return base64.b64encode(image_bytes).decode("utf-8")
