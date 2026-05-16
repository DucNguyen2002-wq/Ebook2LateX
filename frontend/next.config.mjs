/** @type {import('next').NextConfig} */
const nextConfig = {
  // Dùng standalone output để deploy bằng Docker
  output: "standalone",

  async rewrites() {
    // Khi chạy local/Docker, proxy /api/* về backend
    // Trên Vercel, đặt NEXT_PUBLIC_API_URL → api.js gọi thẳng, bỏ qua rewrites
    const apiUrl = process.env.API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
