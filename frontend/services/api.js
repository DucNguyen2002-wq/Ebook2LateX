import axios from "axios";

// Nếu NEXT_PUBLIC_API_URL được đặt (ví dụ trên Vercel), gọi thẳng tới backend
// Nếu không, dùng /api → Next.js rewrites proxy về backend (local/Docker)
const baseURL = process.env.NEXT_PUBLIC_API_URL
  ? `${process.env.NEXT_PUBLIC_API_URL}/api`
  : "/api";

const api = axios.create({ baseURL });

/** Tải lên tập tin PDF và tạo bản ghi Document */
export const uploadPDF = (file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

/** Chạy OCR trên tài liệu đã tải lên (trả về 202 ngay lập tức) */
export const processDocument = (documentId) =>
  api.post(`/process/${documentId}`);

/** Kiểm tra trạng thái xử lý và lấy kết quả khi hoàn thành */
export const getProcessStatus = (documentId) =>
  api.get(`/process/${documentId}/status`);

/** Lưu nội dung LaTeX đã chỉnh sửa (FR3) */
export const saveFormula = (formulaId, latexContent) =>
  api.put(`/save/${formulaId}`, { latex_content: latexContent });

/** Lấy danh sách công thức của một tài liệu */
export const getFormulas = (documentId) =>
  api.get(`/documents/${documentId}/formulas`);
