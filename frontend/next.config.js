const publicApiUrl = process.env.NEXT_PUBLIC_API_URL || "/api";

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  env: {
    NEXT_PUBLIC_API_URL: publicApiUrl,
  },
};

module.exports = nextConfig;
