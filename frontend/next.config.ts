import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://1on1ai-production.up.railway.app/api/:path*',
      },
    ];
  },
};

export default nextConfig;
