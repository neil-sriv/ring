// @ts-check

/** @type {import('next').NextConfig} */
const nextConfig = {
  rewrites: async () => {
    return [
      {
        source: "/:path*",
        destination:
          process.env.ENVIRONMENT === "LOCAL"
            ? "http://127.0.0.1:8001/internal/:path*"
            : "http://34.203.31.64:8001/internal/:path*", // Proxy to Backend
      },
    ];
  },
};

module.exports = nextConfig;
