import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // When undefined: warn-only mode (requests work, warning shown). When set: block mode.
  // Add ["192.168.1.12", "localhost"] to suppress warning (restart dev server after change).
  allowedDevOrigins: undefined,
  experimental: {
    // PDF processing can take 1–2 min for large/scanned docs; default ~30s causes ECONNRESET
    proxyTimeout: 180_000, // 3 minutes
    proxyClientMaxBodySize: "60mb", // allow large PDF uploads (backend max 50MB)
  },
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://localhost:8000/api/v1/:path*",
      },
    ];
  },
};

export default nextConfig;
