"use client";

import { useEffect, useRef } from "react";

/**
 * Trình soạn thảo MathLive (FR2).
 * Đồng bộ 2 chiều giữa prop `value` (LaTeX string) và <math-field>.
 * Component này KHÔNG render phía server (được import với ssr: false).
 */
export default function MathLiveEditor({ value, onChange }) {
  const mathRef = useRef(null);
  const suppressRef = useRef(false);
  const readyRef = useRef(false);

  // Load mathlive client-side only.
  // Sau khi thư viện load xong (custom element được đăng ký và upgrade),
  // mới set giá trị ban đầu — tránh mất giá trị do element chưa được upgrade.
  useEffect(() => {
    import("mathlive").then(({ MathfieldElement }) => {
      MathfieldElement.fontsDirectory = "https://unpkg.com/mathlive/dist/fonts";
      readyRef.current = true;
      const mf = mathRef.current;
      if (mf) {
        suppressRef.current = true;
        mf.value = value ?? "";
        suppressRef.current = false;
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Khi LaTeX thay đổi từ bên ngoài (ô textarea) → cập nhật math-field
  // Chỉ thực hiện sau khi mathlive đã sẵn sàng
  useEffect(() => {
    const mf = mathRef.current;
    if (!readyRef.current || !mf) return;
    if (mf.value !== (value ?? "")) {
      suppressRef.current = true;
      mf.value = value ?? "";
      suppressRef.current = false;
    }
  }, [value]);

  // Khi người dùng sửa trong math-field → phát sự kiện ra ngoài
  const handleInput = (e) => {
    if (suppressRef.current) return;
    onChange(e.target.value);
  };

  return (
    <math-field
      ref={mathRef}
      onInput={handleInput}
      style={{
        width: "100%",
        fontSize: "1.25rem",
        border: "1px solid #d1d5db",
        borderRadius: "0.5rem",
        padding: "0.5rem",
        minHeight: "3rem",
      }}
    />
  );
}
