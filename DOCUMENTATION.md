# Ebook2LaTeX — Tài liệu Tổng quan Dự án

> **Phiên bản:** 1.1.0 | **Cập nhật:** 2026-05-10

---

## Mục lục

1. [Tổng quan Dự án](#1-tổng-quan-dự-án)
2. [Mục tiêu](#2-mục-tiêu)
3. [Kiến trúc Hệ thống](#3-kiến-trúc-hệ-thống)
4. [Công nghệ Sử dụng](#4-công-nghệ-sử-dụng)
5. [Cấu trúc Thư mục](#5-cấu-trúc-thư-mục)
6. [Cơ sở Dữ liệu](#6-cơ-sở-dữ-liệu)
7. [API Reference](#7-api-reference)
8. [Phân tích Chức năng](#8-phân-tích-chức-năng)
9. [Luồng Xử lý End-to-End](#9-luồng-xử-lý-end-to-end)
10. [Quản lý Công thức](#10-quản-lý-công-thức)
11. [Cấu hình Môi trường](#11-cấu-hình-môi-trường)
12. [Triển khai](#12-triển-khai)
13. [Supabase Cloud Database](#13-supabase-cloud-database)
14. [Giới hạn & Hướng phát triển](#14-giới-hạn--hướng-phát-triển)

---

## 1. Tổng quan Dự án

**Ebook2LaTeX** là một ứng dụng web full-stack cho phép người dùng tải lên file PDF chứa nội dung toán học và tự động trích xuất, nhận dạng các công thức toán học sang định dạng **LaTeX** — ngôn ngữ soạn thảo khoa học chuẩn quốc tế.

### Vấn đề giải quyết

Khi biên soạn tài liệu học thuật, sách giáo khoa số (ebook), hay chuyển đổi tài liệu sang định dạng LaTeX, người dùng phải gõ lại thủ công từng công thức toán học — công việc tốn thời gian, dễ sai sót, đặc biệt với các công thức phức tạp như tích phân, ma trận, phương trình vi phân.

Ebook2LaTeX **tự động hóa hoàn toàn** quy trình này:
- Phân tích PDF để định vị chính xác các vùng công thức
- Chạy OCR nhận dạng ảnh → LaTeX bằng mô hình AI
- Cho phép người dùng xem, chỉnh sửa và lưu kết quả

---

## 2. Mục tiêu

### Mục tiêu chính

| # | Mục tiêu | Mô tả |
|---|-----------|-------|
| FR1 | **Tải lên PDF** | Người dùng upload file PDF bất kỳ chứa công thức toán học |
| FR2 | **Trích xuất & OCR** | Hệ thống phát hiện công thức, render thành ảnh, nhận dạng thành LaTeX |
| FR3 | **Chỉnh sửa & Lưu** | Người dùng xem ảnh gốc, sửa LaTeX trong editor trực quan, lưu vào DB |

### Mục tiêu phi chức năng

- **Hiệu năng:** OCR chạy nền (background task), trả về HTTP 202 ngay lập tức; frontend polling mỗi 2 giây
- **Độ chính xác:** Ưu tiên mô hình pix2tex (offline/miễn phí), fallback sang Mathpix API
- **Khả năng mở rộng:** Kiến trúc tách biệt frontend/backend, containerized với Docker
- **Trải nghiệm người dùng:** Xem preview công thức trực tiếp (MathLive), không cần biết LaTeX
- **Bảo mật:** CORS giới hạn origin, dữ liệu file lưu server-side

---

## 3. Kiến trúc Hệ thống

```
┌─────────────────────────────────────────────────────────┐
│                     CLIENT (Browser)                    │
│  Next.js 14 + React + TailwindCSS + MathLive            │
│  Port: 3000                                             │
└─────────────────┬───────────────────────────────────────┘
                  │ HTTP /api/*  (proxy hoặc trực tiếp)
                  ▼
┌─────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                     │
│  Python + Uvicorn                                       │
│  Port: 8000                                             │
│                                                         │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐               │
│  │ /upload │  │ /process │  │  /save   │               │
│  └────┬────┘  └────┬─────┘  └────┬─────┘               │
│       │            │              │                     │
│  ┌────▼────────────▼──────────────▼───────┐             │
│  │        Services Layer                   │             │
│  │  pdf_parser (PyMuPDF)  │  ocr (pix2tex) │             │
│  └────────────────────────┴────────────────┘             │
│                    │                                    │
│             SQLAlchemy ORM                              │
└─────────────────────┬───────────────────────────────────┘
                      │ PostgreSQL protocol
                      ▼
┌─────────────────────────────────────────────────────────┐
│             DATABASE (Supabase Cloud)                   │
│  PostgreSQL 16 managed — truy cập qua internet          │
│  users | documents | formula_entries | logs             │
│  Kết nối: Transaction Pooler port 6543 (PgBouncer)      │
└─────────────────────────────────────────────────────────┘
```

### Mô hình giao tiếp

- **Frontend → Backend:** REST API qua Axios; Next.js rewrites proxy `/api/*` → `http://backend:8000/api/*`
- **Backend → Database:** SQLAlchemy ORM với PostgreSQL dialect (`psycopg2-binary`)
- **OCR Engine:** pix2tex chạy in-process (model được pre-warm lúc startup); fallback HTTP sang Mathpix API
- **Async Processing:** FastAPI `BackgroundTasks` — file được xử lý song song, không block request

---

## 4. Công nghệ Sử dụng

### Backend

| Thư viện | Phiên bản | Mục đích |
|----------|-----------|----------|
| FastAPI | ≥ 0.115 | Web framework, REST API, validation |
| Uvicorn | ≥ 0.30 | ASGI server |
| SQLAlchemy | ≥ 2.0 | ORM, quản lý session DB |
| Alembic | 1.18.4 | Database migration |
| PyMuPDF (fitz) | ≥ 1.24 | Parse PDF, phát hiện block công thức theo font |
| pix2tex | ≥ 0.1.2 | OCR ảnh → LaTeX (mô hình Transformer offline) |
| Pillow | ≥ 10.0 | Xử lý ảnh trước khi đưa vào OCR |
| httpx | ≥ 0.27 | HTTP client gọi Mathpix API (fallback) |
| python-dotenv | ≥ 1.0 | Đọc biến môi trường từ .env |
| psycopg2-binary | ≥ 2.9 | PostgreSQL driver |
| python-multipart | ≥ 0.0.9 | Xử lý file upload multipart/form-data |

### Frontend

| Thư viện | Phiên bản | Mục đích |
|----------|-----------|----------|
| Next.js | 14.2 | React framework, SSR, routing, rewrites |
| React | 18.3 | UI component library |
| MathLive | 0.101 | WYSIWYG math editor, render LaTeX trực tiếp |
| Axios | 1.7 | HTTP client gọi backend API |
| TailwindCSS | 3.4 | Utility-first CSS |

### Infrastructure

| Thành phần | Công nghệ |
|------------|-----------|
| Database | Supabase Cloud (PostgreSQL 16 managed) |
| Containerization | Docker + Docker Compose |
| DB Migration | Alembic (chạy tự động khi start container) |
| File Storage | Disk local (volume Docker) / Supabase Storage (tùy chọn) |

---

## 5. Cấu trúc Thư mục

```
Ebook2LaTeX/
├── docker-compose.yml          # Orchestration 3 services: db, backend, frontend
├── requirements.txt            # Root requirements (Alembic, greenlet)
│
├── backend/
│   ├── main.py                 # Entry point FastAPI, CORS, lifespan (pre-warm model)
│   ├── Dockerfile              # Python 3.11 slim image
│   ├── requirements.txt        # Backend dependencies
│   ├── seed.py                 # Script tạo dữ liệu mẫu
│   ├── alembic.ini             # Cấu hình Alembic migration
│   ├── uploads/                # Thư mục lưu PDF và ảnh công thức
│   ├── migrations/
│   │   ├── env.py              # Alembic env (đọc models để auto-detect changes)
│   │   └── versions/           # File migration tự động sinh
│   └── app/
│       ├── database.py         # SQLAlchemy engine + SessionLocal
│       ├── models.py           # ORM models: User, Document, FormulaEntry, Log
│       ├── api/
│       │   ├── upload.py       # POST /api/upload
│       │   ├── process.py      # POST /api/process/{id}, GET /api/process/{id}/status
│       │   └── save.py         # PUT /api/save/{id}, GET /api/documents/{id}/formulas
│       ├── core/
│       │   └── config.py       # Đọc env vars, UPLOAD_DIR
│       ├── schemas/
│       │   ├── document.py     # Pydantic: DocumentOut
│       │   └── formula.py      # Pydantic: FormulaOut, FormulaUpdate, ProcessResult
│       └── services/
│           ├── ocr.py          # run_ocr(): pix2tex → Mathpix fallback
│           └── pdf_parser.py   # extract_formula_images(): font-based detection
│
├── frontend/
│   ├── Dockerfile              # Node 20 + Next.js standalone build
│   ├── next.config.mjs         # Rewrites /api/* → backend, standalone output
│   ├── package.json
│   ├── app/
│   │   ├── layout.jsx          # Root layout
│   │   └── page.jsx            # Trang chủ: PDFUploader + FormulaList
│   ├── components/
│   │   ├── PDFUploader.jsx     # Upload file + polling xử lý
│   │   ├── FormulaList.jsx     # Danh sách FormulaCard
│   │   └── MathLiveEditor.jsx  # Web component MathLive (client-only)
│   └── services/
│       └── api.js              # Axios client: uploadPDF, processDocument, saveFormula, ...
│
└── PDF/debug/                  # (Tùy chọn) Ảnh debug khi phân tích PDF
```

---

## 6. Cơ sở Dữ liệu

### Sơ đồ ERD

```
┌──────────────────┐       ┌───────────────────┐       ┌─────────────────────┐
│      users       │       │    documents      │       │   formula_entries   │
├──────────────────┤       ├───────────────────┤       ├─────────────────────┤
│ user_id (PK/UUID)│──1──┐ │ id (PK/UUID)      │──1──┐ │ id (PK/UUID)        │
│ username_email   │     └►│ user_id (FK)      │     └►│ document_id (FK)    │
│ password_hash    │       │ file_name         │       │ raw_image_path      │
│ full_name        │       │ file_path_url     │       │ latex_content       │
│ role             │       │ upload_date       │       │ order_index         │
│ last_login       │       │ status            │       │ created_at          │
│ is_active        │       └───────────────────┘       │ updated_at          │
│ created_at       │                                   └──────────┬──────────┘
└──────────────────┘                                              │
                                                                  │ 1
                                                        ┌─────────▼──────────┐
                                                        │        logs        │
                                                        ├────────────────────┤
                                                        │ (log OCR attempts) │
                                                        └────────────────────┘
```

### Mô tả bảng

#### `users`
| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `user_id` | UUID PK | Định danh người dùng |
| `username_email` | VARCHAR(255) UNIQUE | Email đăng nhập |
| `password_hash` | TEXT | Mật khẩu đã hash |
| `full_name` | VARCHAR(100) | Tên hiển thị |
| `role` | VARCHAR(20) | `Admin` / `Editor` / `Viewer` |
| `is_active` | BOOLEAN | Tài khoản có hoạt động không |
| `created_at` | TIMESTAMPTZ | Thời điểm tạo |

#### `documents`
| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `id` | UUID PK | Định danh tài liệu |
| `user_id` | UUID FK | Người tải lên (nullable — SET NULL khi xóa user) |
| `file_name` | TEXT | Tên file gốc |
| `file_path_url` | TEXT | Đường dẫn lưu trên server |
| `status` | VARCHAR(50) | `Pending` → `Processing` → `Processed` / `Error` |
| `upload_date` | TIMESTAMPTZ | Thời điểm tải lên |

#### `formula_entries`
| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `id` | UUID PK | Định danh công thức |
| `document_id` | UUID FK | Tài liệu chứa công thức (CASCADE DELETE) |
| `raw_image_path` | TEXT | Đường dẫn file ảnh PNG của công thức |
| `latex_content` | TEXT | Chuỗi LaTeX (kết quả OCR hoặc đã sửa) |
| `order_index` | INTEGER | Thứ tự xuất hiện trong PDF |
| `created_at` | TIMESTAMPTZ | Thời điểm tạo |
| `updated_at` | TIMESTAMPTZ | Thời điểm cập nhật gần nhất |

### Vòng đời trạng thái Document

```
[Upload] → Pending → [Trigger Process] → Processing → [OCR xong] → Processed
                                                    ↘ [Lỗi] → Error
```

---

## 7. API Reference

### Base URL
- **Local dev:** `http://localhost:8000/api`
- **Docker:** Frontend proxy qua `/api` → `http://backend:8000/api`

### Endpoints

#### `POST /api/upload`
Tải lên file PDF, tạo bản ghi Document.

**Request:** `multipart/form-data`
```
file: <PDF file>
```

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "file_name": "Giao_trinh_Toan_12.pdf",
  "status": "Pending",
  "upload_date": "2026-05-10T08:00:00Z"
}
```

**Lỗi:**
- `400` — File không phải PDF

---

#### `POST /api/process/{document_id}`
Kích hoạt xử lý tài liệu (chạy nền). Trả về **ngay lập tức**.

**Response 202:**
```json
{
  "status": "Processing",
  "document_id": "550e8400-..."
}
```

**Lỗi:**
- `404` — Không tìm thấy tài liệu

---

#### `GET /api/process/{document_id}/status`
Kiểm tra trạng thái và lấy kết quả sau khi hoàn thành.

**Response (đang xử lý):**
```json
{
  "document_id": "550e8400-...",
  "status": "Processing",
  "formulas": []
}
```

**Response (hoàn thành):**
```json
{
  "document_id": "550e8400-...",
  "status": "Processed",
  "formulas": [
    {
      "id": "abc123-...",
      "order_index": 0,
      "latex_content": "\\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}",
      "image_base64": "iVBORw0KGgo...",
      "created_at": "2026-05-10T08:01:00Z",
      "updated_at": "2026-05-10T08:01:00Z"
    }
  ]
}
```

**Lỗi:**
- `404` — Không tìm thấy tài liệu
- `500` — Xử lý thất bại

---

#### `PUT /api/save/{formula_id}`
Lưu nội dung LaTeX đã chỉnh sửa.

**Request body:**
```json
{
  "latex_content": "\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}"
}
```

**Response 200:** FormulaOut (giống trên)

**Lỗi:**
- `404` — Công thức không tồn tại

---

#### `GET /api/documents/{document_id}/formulas`
Lấy toàn bộ danh sách công thức của một tài liệu theo thứ tự.

**Response 200:** `List[FormulaOut]`

---

## 8. Phân tích Chức năng

### 8.1 Module Tải lên PDF (`upload.py`)

**Luồng:**
1. Nhận file qua `multipart/form-data`
2. Kiểm tra phần mở rộng `.pdf`
3. Tạo UUID mới → lưu file vào `uploads/<uuid>.pdf`
4. Tạo bản ghi `Document` với `status = "Pending"`
5. Trả về `DocumentOut`

**Điểm chú ý:** File được lưu với tên UUID để tránh xung đột, không lưu tên gốc làm tên file hệ thống.

---

### 8.2 Module Phân tích PDF (`pdf_parser.py`)

Đây là module cốt lõi, dùng **phân tích font** (thay vì OCR toàn trang) để định vị chính xác công thức:

#### Chiến lược phát hiện công thức

PDF soạn thảo bằng LaTeX nhúng font Computer Modern với tên chuẩn:

| Font | Ý nghĩa |
|------|---------|
| `CMEX` | Ký hiệu toán lớn: ∑ ∫ ∏ ngoặc lớn — **chắc chắn là display formula** |
| `CMSY` | Ký hiệu toán nhỏ: ≤ ≥ → ∈ |
| `CMMI` | Math italic: *x*, *y*, *α* — chỉ xuất hiện trong công thức |
| `CMR` / `CMBX` | Văn bản thông thường / đậm |

**Ba quy tắc phân loại block:**

```
Rule 1: has_cmex AND non_math_ratio < 0.75  → Display formula (∑ ∫ …)
Rule 2: (has_cmex OR has_cmsy) AND has_cmmi AND ratio < 0.50 → Fragment (subscript)
Rule 3: Block hẹp (< 45% chiều rộng cột văn bản) có CMEX/CMSY → Fragment nhỏ
```

#### Gộp block thành công thức hoàn chỉnh

Các block liên quan (cách nhau ≤ 12pt theo chiều dọc) được **merge** thành một bbox duy nhất → render ảnh PNG toàn bộ công thức (scale 3× để rõ nét hơn cho OCR), padding 8pt.

---

### 8.3 Module OCR (`ocr.py`)

**Chiến lược dual-engine:**

```
               ┌──────────────┐
    image_bytes │              │
  ─────────────►│   pix2tex    │──► LaTeX string
                │  (offline)   │
                └──────┬───────┘
                       │ Lỗi / chưa cài
                       ▼
                ┌──────────────┐
                │  Mathpix API │──► LaTeX string
                │   (online)   │
                └──────────────┘
```

- **pix2tex:** Mô hình Transformer chạy hoàn toàn local (không cần internet, miễn phí), được pre-warm lúc server startup để tránh delay lần đầu
- **Mathpix:** Gọi `https://api.mathpix.com/v3/text`, cần `MATHPIX_APP_ID` + `MATHPIX_APP_KEY`

---

### 8.4 Module Xử lý nền (`process.py`)

**Background task `_do_process`:**
1. Đặt `status = "Processing"`, xóa công thức cũ (nếu xử lý lại)
2. Tạo thư mục `uploads/<document_id>/`
3. Gọi `extract_formula_images()` → danh sách `(order_index, image_bytes)`
4. Với từng ảnh: lưu file PNG → `run_ocr()` → tạo `FormulaEntry` → commit ngay (kết quả hiện dần)
5. Đặt `status = "Processed"`

**Thiết kế:** Commit từng công thức ngay sau OCR thay vì bulk-commit cuối → frontend có thể thấy kết quả hiện dần khi polling.

---

### 8.5 Giao diện Người dùng

#### `PDFUploader.jsx`
- Drag-and-drop / chọn file → gọi `uploadPDF()` → `processDocument()`
- Polling mỗi **2 giây** (tối đa **10 phút**) bằng `getProcessStatus()`
- Hiển thị trạng thái: "Đang tải lên…", "Đang OCR…", thanh loading

#### `FormulaList.jsx` + `FormulaCard`
Với mỗi công thức, hiển thị:
1. **Ảnh gốc** (base64 PNG) — xem công thức trong PDF
2. **Textarea LaTeX** — chỉnh sửa thô (font monospace)
3. **MathLive Editor** — preview render toán học WYSIWYG, đồng bộ 2 chiều với textarea
4. **Nút Submit** — gọi `saveFormula()` lưu vào DB

#### `MathLiveEditor.jsx`
- Dùng Web Component `<math-field>` từ thư viện MathLive
- Load **client-only** (Next.js `dynamic` với `ssr: false`) để tránh lỗi server-side render
- Phát sự kiện `input` → cập nhật state cha

---

## 9. Luồng Xử lý End-to-End

```
Người dùng                Frontend              Backend               Database
    │                        │                     │                      │
    │──── Chọn file PDF ─────►│                     │                      │
    │                        │──── POST /upload ───►│                      │
    │                        │                     │── Lưu file ──────────►│
    │                        │                     │── INSERT Document ────►│
    │                        │◄─── {id, status} ───│                      │
    │                        │                     │                      │
    │                        │── POST /process/{id}►│                      │
    │                        │◄── 202 Accepted ─────│                      │
    │                        │                     │ [Background Task]    │
    │                        │                     │── pdf_parser ─────────│
    │                        │                     │── pix2tex OCR ────────│
    │                        │                     │── INSERT Formula ─────►│ (từng cái)
    │                        │                     │                      │
    │   [Polling 2s]          │                     │                      │
    │                        │── GET /status ──────►│                      │
    │                        │◄── {Processing, []}──│                      │
    │                        │── GET /status ──────►│                      │
    │                        │◄── {Processed, [...]}│                      │
    │                        │                     │                      │
    │◄── Hiển thị danh sách ──│                     │                      │
    │                        │                     │                      │
    │── Sửa LaTeX + Submit ──►│                     │                      │
    │                        │── PUT /save/{id} ───►│                      │
    │                        │                     │── UPDATE Formula ─────►│
    │◄── ✓ Đã lưu ───────────│                     │                      │
```

---

## 10. Quản lý Công thức

### Xem công thức

Sau khi xử lý xong, toàn bộ công thức được hiển thị theo thứ tự xuất hiện trong PDF (`order_index`). Mỗi công thức bao gồm:

- **Số thứ tự:** `Công thức #1`, `#2`, ...
- **Ảnh gốc:** Vùng công thức được cắt từ PDF, scale 3× để rõ nét
- **Code LaTeX:** Có thể sao chép và dán trực tiếp vào tài liệu LaTeX
- **Preview WYSIWYG:** MathLive render công thức như trong sách toán

### Chỉnh sửa công thức

Khi pix2tex nhận dạng sai hoặc thiếu, người dùng có thể:
1. Sửa trực tiếp trong **textarea** (gõ code LaTeX)
2. Dùng **MathLive keyboard** (bảng phím toán ảo) để chèn ký hiệu
3. Xem preview cập nhật **real-time** ngay bên dưới

Hai chiều đồng bộ: sửa textarea → MathLive cập nhật và ngược lại.

### Lưu & Xuất

- **Lưu từng công thức:** Nhấn "Submit" để lưu LaTeX vào database
- **Lấy danh sách:** `GET /api/documents/{document_id}/formulas` trả về toàn bộ
- **Xử lý lại:** Gọi lại `POST /api/process/{document_id}` — xóa kết quả cũ và chạy lại từ đầu

### Dữ liệu mẫu

Script `backend/seed.py` tạo sẵn:
- 1 user test: `ty@dalat.edu.vn`
- 1 document: `Giao_trinh_Toan_12.pdf`
- 1 công thức mẫu: $\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$

```bash
cd backend
python seed.py
```

---

## 11. Cấu hình Môi trường

### File `.env` (backend)

Sao chép từ `backend/.env.example` rồi điền giá trị thực:

```env
# Database — Supabase Cloud (bắt buộc)
# Lấy từ: Supabase Dashboard → Project Settings → Database → URI
#
# Transaction mode (port 6543, qua PgBouncer — Recommended):
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
#
# Session mode (port 5432, kết nối trực tiếp — dùng khi gặp lỗi prepared statement):
# DATABASE_URL=postgresql://postgres.[project-ref]:[password]@db.[project-ref].supabase.co:5432/postgres?sslmode=require

# Mathpix API (tùy chọn — fallback khi pix2tex không khả dụng)
MATHPIX_APP_ID=your_app_id
MATHPIX_APP_KEY=your_app_key
```

### Biến môi trường Frontend

```env
# Tùy chọn — khi deploy production không qua proxy Next.js
NEXT_PUBLIC_API_URL=https://your-backend-domain.com
```

---

## 12. Triển khai

### 12.1 Chạy Local (Development)

#### Yêu cầu
- Python 3.11+
- Node.js 20+
- Tài khoản Supabase (free tier) — **không cần cài PostgreSQL local**

#### Backend

```bash
# 1. Tạo virtual environment
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS

# 2. Cài dependencies
pip install -r requirements.txt

# 3. Tạo file .env (xem mục 11)

# 4. Chạy migration
alembic upgrade head

# 5. Khởi động server (hot-reload)
uvicorn main:app --reload --port 8000
```

API docs tự động tại: http://localhost:8000/docs

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Ứng dụng tại: http://localhost:3000

---

### 12.2 Chạy với Docker Compose (Recommended)

```bash
# Clone repo và vào thư mục gốc
cd Ebook2LaTeX

# Tạo file .env từ template
copy backend\.env.example backend\.env
# Điền DATABASE_URL từ Supabase Dashboard vào backend/.env

# Build và start (chỉ 2 service: backend + frontend)
docker-compose up --build

# Chạy nền
docker-compose up -d --build
```

Các service:

| Service | URL | Mô tả |
|---------|-----|-------|
| Frontend | http://localhost:3000 | Next.js UI |
| Backend | http://localhost:8000 | FastAPI + Swagger docs tại /docs |
| Database | Supabase Cloud | PostgreSQL managed (không chạy local) |

**Alembic migration** chạy tự động khi backend container khởi động — kết nối thẳng lên Supabase.

#### Các lệnh Docker hữu ích

```bash
# Xem logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Dừng và xóa volumes
docker-compose down -v

# Rebuild sau khi thay đổi code
docker-compose up --build backend

# Chạy seed data trong container
docker-compose exec backend python seed.py
```

---

### 12.3 Deploy Production

#### Backend (VPS / Cloud VM)

```bash
# Cài Nginx làm reverse proxy
# Cấu hình /etc/nginx/sites-available/ebook2latex:
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Dùng Docker Compose hoặc Gunicorn + Supervisor
docker-compose -f docker-compose.prod.yml up -d
```

#### Frontend (Vercel — Recommended)

1. Push code lên GitHub
2. Import project vào Vercel
3. Đặt environment variable:
   ```
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com
   ```
4. Deploy tự động mỗi khi push

#### Frontend (Self-hosted Docker)

```bash
# Build standalone output (đã cấu hình trong next.config.mjs)
docker build -t ebook2latex-frontend ./frontend
docker run -p 3000:3000 -e API_URL=http://backend:8000 ebook2latex-frontend
```

---

### 12.4 Database Migration

```bash
# Tạo migration mới sau khi thay đổi models.py
alembic revision --autogenerate -m "mo_ta_thay_doi"

# Áp dụng migration
alembic upgrade head

# Rollback 1 bước
alembic downgrade -1

# Xem lịch sử
alembic history
```

---

## 13. Supabase Cloud Database

Ebook2LaTeX sử dụng **Supabase** làm database chính thức thay cho PostgreSQL local. Supabase là nền tảng Backend-as-a-Service mã nguồn mở, cung cấp PostgreSQL được quản lý hoàn toàn trên cloud.

### 13.1 Tại sao dùng Supabase?

| Tiêu chí | PostgreSQL Local (Docker) | Supabase Cloud ✅ (hiện tại) |
|----------|--------------------------|-----------------------------|
| **Cài đặt** | Cần Docker, tự quản lý | Managed hoàn toàn, free tier |
| **Backup** | Tự cấu hình | Tự động hàng ngày (30 ngày) |
| **Kết nối** | Chỉ truy cập trong mạng nội bộ | Truy cập từ mọi nơi qua internet |
| **Scale** | Giới hạn tài nguyên máy chủ | Scale theo nhu cầu |
| **Auth tích hợp** | Không có | Supabase Auth (JWT sẵn sàng) |
| **Storage** | File lưu local, mất khi container xóa | Supabase Storage (S3-compatible) |
| **Dashboard** | pgAdmin / psql | Giao diện web trực quan |
| **Chi phí** | Miễn phí (tự host) | Miễn phí ≤ 500 MB, gói Pro $25/tháng |

### 13.2 Cấu trúc kết nối

Supabase cung cấp **2 chế độ kết nối** — dự án dùng Transaction mode mặc định:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Supabase Cloud                           │
│                                                                 │
│  ┌──────────────────────┐    ┌───────────────────────────────┐  │
│  │  Transaction Pooler  │    │      Direct Connection        │  │
│  │  (PgBouncer)         │    │      (Session mode)           │  │
│  │  Port: 6543 ✅ dùng  │    │      Port: 5432               │  │
│  │  Tốt cho production  │    │  Dùng nếu lỗi prepared stmt   │  │
│  └──────────┬───────────┘    └───────────────────────────────┘  │
│             │                                                   │
│             └──────────────► PostgreSQL 16 Database             │
└─────────────────────────────────────────────────────────────────┘
                 ▲
                 │ DATABASE_URL
         Backend (FastAPI)
```

### 13.3 Tạo project Supabase

1. Đăng ký tại [https://supabase.com](https://supabase.com) (free tier)
2. **New Project** → đặt tên `ebook2latex`, chọn region **Singapore** (gần Việt Nam nhất)
3. Đặt **Database Password** mạnh → lưu lại ngay
4. Chờ ~2 phút để project khởi tạo
5. Vào **Project Settings → Database → Connection String → URI** → sao chép:

```
# Transaction mode (Recommended)
postgresql://postgres.[project-ref]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres

# Session mode (fallback)
postgresql://postgres.[project-ref]:[password]@db.[project-ref].supabase.co:5432/postgres?sslmode=require
```

### 13.4 Cấu hình `backend/.env`

Sao chép file mẫu và điền Connection String:

```bash
copy backend\.env.example backend\.env
```

```env
# backend/.env
DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres

# Mathpix API (tùy chọn)
MATHPIX_APP_ID=your_app_id
MATHPIX_APP_KEY=your_app_key
```

### 13.5 Khởi tạo Schema

Alembic tự động tạo toàn bộ bảng trên Supabase:

```bash
cd backend

# Kiểm tra kết nối
python -c "from app.database import engine; conn = engine.connect(); print('OK'); conn.close()"

# Chạy migration
alembic upgrade head

# (Tùy chọn) Tạo dữ liệu mẫu
python seed.py
```

Khi chạy `docker-compose up`, Alembic migration **tự động chạy** trước khi Uvicorn start.

### 13.6 Xử lý PgBouncer (Transaction mode)

Supabase Transaction Pooler dùng **PgBouncer** — `database.py` đã được cấu hình tự động nhận diện và xử lý:

```python
# backend/app/database.py — đã cấu hình sẵn
_is_supabase = "pooler.supabase.com" in SQLALCHEMY_DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"options": "-c statement_timeout=30000"} if _is_supabase else {},
    pool_pre_ping=True,   # Tự kiểm tra kết nối trước khi dùng
)
```

Nếu gặp lỗi `prepared statement does not exist`, chuyển sang **Session mode** (port 5432) trong `.env`.

### 13.7 Supabase Dashboard

Sau khi migration, có thể quản lý dữ liệu trực tiếp qua giao diện web:

| Tính năng | Đường dẫn |
|-----------|----------|
| Xem/sửa bảng | Table Editor → `formula_entries` / `documents` |
| Chạy SQL thủ công | SQL Editor |
| Xem logs kết nối | Logs → Database |
| Quản lý backup | Database → Backups |
| Monitoring | Reports → Database |

### 13.8 Supabase Storage (Tùy chọn — nâng cấp tiếp theo)

Hiện tại file PDF và ảnh PNG lưu trên **disk local** (Docker volume `uploads_data`). Khi cần bền vững hơn, nâng cấp lên Supabase Storage:

```bash
# Cài thêm SDK
pip install supabase
# Thêm vào backend/requirements.txt: supabase>=2.0.0
```

```env
# Thêm vào backend/.env
SUPABASE_URL=https://[project-ref].supabase.co
SUPABASE_SERVICE_KEY=eyJhbGci...   # Service role key (Settings → API)
```

Tạo bucket trên Supabase Storage:
- **Bucket name:** `uploads` (private)
- **Path pdfs:** `pdfs/<uuid>.pdf`
- **Path formulas:** `formulas/<document_id>/<order_index>.png`

### 13.9 Free Tier & Giới hạn

| Tài nguyên | Free Tier | Ghi chú |
|------------|-----------|--------|
| Database size | 500 MB | Đủ cho ~10,000 tài liệu với nhiều công thức |
| Storage | 1 GB | Nếu dùng Supabase Storage |
| Bandwidth | 5 GB/tháng | Outbound |
| Connections | 60 concurrent | Qua Transaction Pooler |
| Uptime | Pause sau 1 tuần không active | Chỉ free tier |

> **Lưu ý Free Tier:** Project tự động **pause** sau 1 tuần không có request. Resume thủ công trong Dashboard hoặc nâng lên gói Pro ($25/tháng) để tránh.

### 13.10 Backup & Restore

```bash
# Backup từ Supabase về local (dùng pg_dump)
pg_dump "postgresql://postgres.[ref]:[pwd]@db.[ref].supabase.co:5432/postgres" \
  -Fc -f backup_$(date +%Y%m%d).dump

# Restore lên Supabase mới
pg_restore -d "postgresql://postgres.[ref]:[pwd]@..." backup.dump
```

Supabase cũng cung cấp **Point-in-Time Recovery** (gói Pro) và download backup thủ công trong Dashboard → Database → Backups.

---

## 14. Giới hạn & Hướng phát triển

### Giới hạn hiện tại

| # | Vấn đề | Ghi chú |
|---|--------|---------|
| 1 | **Chỉ hỗ trợ PDF LaTeX-native** | PDF scan (ảnh) không phát hiện được font → không trích xuất được |
| 2 | **Chưa có xác thực người dùng** | Model `User` đã có trong DB nhưng API chưa implement JWT/auth |
| 3 | **OCR pix2tex cần GPU** để đạt tốc độ tối ưu | CPU inference chậm với tài liệu nhiều công thức |
| 4 | **Không có export** | Chưa có chức năng xuất toàn bộ công thức ra file `.tex` hay `.csv` |
| 5 | **Không có lịch sử chỉnh sửa** | Bảng `logs` đã được thiết kế nhưng chưa populate |
| 6 | **UI một trang duy nhất** | Chưa có routing, quản lý nhiều tài liệu cùng lúc |

### Hướng phát triển

- [ ] **Authentication** — Implement JWT login/register, phân quyền Admin/Editor/Viewer
- [ ] **Dashboard tài liệu** — Trang danh sách tài liệu đã upload, trạng thái, lịch sử
- [ ] **Export LaTeX** — Xuất toàn bộ công thức ra file `.tex`, copy-to-clipboard batch
- [ ] **Hỗ trợ PDF scan** — Tích hợp pdfplumber + OCR toàn trang trước khi phân tích
- [ ] **Celery + Redis** — Thay BackgroundTasks bằng task queue để xử lý nhiều file song song
- [ ] **WebSocket** — Thay polling bằng push notification khi từng công thức sẵn sàng
- [ ] **Lịch sử chỉnh sửa** — Populate bảng `logs`, cho phép revert về kết quả OCR gốc
- [ ] **Multi-language** — Hỗ trợ công thức hóa học (ChemDraw), ký hiệu vật lý

---

*Tài liệu được tạo tự động từ phân tích mã nguồn dự án Ebook2LaTeX.*
