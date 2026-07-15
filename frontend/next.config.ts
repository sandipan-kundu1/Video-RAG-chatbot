import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://65.0.168.199:8000/api/:path*',
      },
    ]
  },
};

export default nextConfig;
