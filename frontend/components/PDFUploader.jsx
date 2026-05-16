"use client";

import { useState } from "react";
import { uploadPDF, processDocument, getProcessStatus } from "../services/api";

const POLL_INTERVAL_MS = 2000;
const POLL_TIMEOUT_MS = 10 * 60 * 1000; // 10 phút

export default function PDFUploader({ onProcessed }) {
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [error, setError] = useState("");

  const handleFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setError("");
    setStatusMsg("");
    setLoading(true);

    try {
      // Bước 1: Tải lên PDF
      setStatusMsg("Đang tải lên tập tin…");
      const { data: doc } = await uploadPDF(file);

      // Bước 2: Bắt đầu xử lý (backend trả về 202 ngay)
      setStatusMsg(
        "Đang trích xuất công thức và chạy OCR… (có thể mất vài phút)",
      );
      await processDocument(doc.id);

      // Bước 3: Poll trạng thái cho đến khi hoàn thành
      const deadline = Date.now() + POLL_TIMEOUT_MS;
      while (Date.now() < deadline) {
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
        const { data: result } = await getProcessStatus(doc.id);

        if (result.status === "Processed") {
          onProcessed(result);
          return;
        }
        if (result.status === "Error") {
          throw new Error("Xử lý tài liệu thất bại trên máy chủ.");
        }
        // Vẫn đang Processing — tiếp tục poll
      }

      throw new Error("Quá thời gian chờ xử lý. Vui lòng thử lại.");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Có lỗi xảy ra khi xử lý tập tin.",
      );
    } finally {
      setLoading(false);
      setStatusMsg("");
    }
  };

  return (
    <div className="flex flex-col items-center gap-4 p-8 border-2 border-dashed border-blue-400 rounded-xl bg-blue-50">
      <p className="text-lg font-semibold text-blue-700">
        Tải lên tập tin PDF toán học
      </p>
      <input
        type="file"
        accept=".pdf"
        onChange={handleFile}
        disabled={loading}
        className="block text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0
                   file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer disabled:opacity-50"
      />
      {loading && <p className="text-blue-500 animate-pulse">{statusMsg}</p>}
      {error && <p className="text-red-500 text-sm">{error}</p>}
    </div>
  );
}
