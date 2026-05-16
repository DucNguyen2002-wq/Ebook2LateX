"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { saveFormula } from "../services/api";

// MathLive dùng Web Component — chỉ chạy phía client, không SSR
const MathLiveEditor = dynamic(() => import("./MathLiveEditor"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-12 border border-gray-300 rounded-lg bg-gray-50 animate-pulse" />
  ),
});

function FormulaCard({ formula }) {
  const [latex, setLatex] = useState(formula.latex_content ?? "");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    setSaving(true);
    setError("");
    try {
      await saveFormula(formula.id, latex);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch {
      setError("Lưu thất bại, thử lại.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="border border-gray-200 rounded-xl p-5 bg-white shadow-sm flex flex-col gap-4">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">
        Công thức #{formula.order_index + 1}
      </p>

      {formula.image_base64 && (
        <div>
          <p className="text-xs text-gray-500 mb-1">Ảnh gốc</p>
          <img
            src={`data:image/png;base64,${formula.image_base64}`}
            alt={`Công thức ${formula.order_index + 1}`}
            className="max-h-28 object-contain border border-gray-100 rounded bg-gray-50 p-1"
          />
        </div>
      )}

      <div>
        <label className="text-sm font-semibold text-gray-600 block mb-1">
          LaTeX
        </label>
        <textarea
          className="w-full font-mono text-sm border border-gray-300 rounded p-2 resize-none
                     focus:outline-none focus:ring-2 focus:ring-blue-400"
          rows={2}
          value={latex}
          onChange={(e) => setLatex(e.target.value)}
        />
      </div>

      <div>
        <label className="text-sm font-semibold text-gray-600 block mb-1">
          Biểu thức toán học (MathLive)
        </label>
        <MathLiveEditor value={latex} onChange={setLatex} />
      </div>

      {error && <p className="text-red-500 text-sm">{error}</p>}

      <button
        onClick={handleSubmit}
        disabled={saving}
        className="self-end px-5 py-2 bg-green-600 text-white text-sm rounded-lg
                   hover:bg-green-700 disabled:opacity-50 transition-colors"
      >
        {saving ? "Đang lưu…" : saved ? "✓ Đã lưu" : "Submit"}
      </button>
    </div>
  );
}

export default function FormulaList({ formulas }) {
  if (!formulas?.length) return null;

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-xl font-bold text-gray-700">
        Kết quả OCR — {formulas.length} công thức
      </h2>
      {formulas.map((f) => (
        <FormulaCard key={f.id} formula={f} />
      ))}
    </div>
  );
}
