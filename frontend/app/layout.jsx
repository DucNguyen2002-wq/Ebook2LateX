import "./globals.css";

export const metadata = {
  title: "Ebook2LaTeX",
  description: "Chuyển đổi công thức toán học từ PDF sang LaTeX",
};

export default function RootLayout({ children }) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
