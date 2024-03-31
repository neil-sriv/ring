// @ts-check

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  rewrites: async () => {
    return [
      {
        source: "/api/:path*",
        destination:
          process.env.ENVIRONMENT === "local"
            ? "http://localhost/api/v1/internal/:path*"
            : "http://34.203.31.64/api/v1/:path*", // Proxy to Backend
      },
    ];
  },
};

module.exports = nextConfig;
