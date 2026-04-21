const publicApiUrl = process.env.NEXT_PUBLIC_API_URL || "/api";

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  api: {
    bodyParser: {
      sizeLimit: '50mb',
    },
  },
  env: {
    NEXT_PUBLIC_API_URL: publicApiUrl,
  },
};

module.exports = nextConfig;
