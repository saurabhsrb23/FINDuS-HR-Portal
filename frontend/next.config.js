/** @type {import('next').NextConfig} */
const nextConfig = {
  // Required for multi-stage Docker build (copies only what's needed to run)
  output: "standalone",

  // Strict React mode
  reactStrictMode: true,

  // Expose public env vars to the browser bundle
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000",
  },

  // Allow images from the backend origin
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "localhost",
        port: "8000",
        pathname: "/**",
      },
    ],
  },

  // Compiler options
  compiler: {
    // Remove console.log in production
    removeConsole: process.env.NODE_ENV === "production",
  },

  // Reduce build noise
  logging: {
    fetches: {
      fullUrl: process.env.NODE_ENV === "development",
    },
  },
};

module.exports = nextConfig;
