"use client";

import { useState } from "react";
import PDFUploader from "../components/PDFUploader";
import FormulaList from "../components/FormulaList";

export default function Home() {
  const [processResult, setProcessResult] = useState(null);

  const handleReset = () => setProcessResult(null);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-blue-700 text-white px-8 py-4 shadow flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Ebook2LaTeX</h1>
          <p className="text-blue-200 text-sm">
            Chuyển đổi công thức toán học từ PDF sang LaTeX
          </p>
        </div>
        {processResult && (
          <button
            onClick={handleReset}
            className="text-sm bg-white text-blue-700 font-semibold px-4 py-2 rounded hover:bg-blue-50"
          >
            Tải tập tin mới
          </button>
        )}
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8 flex flex-col gap-8">
        {!processResult && <PDFUploader onProcessed={setProcessResult} />}
        {processResult && <FormulaList formulas={processResult.formulas} />}
      </main>
    </div>
  );
}
