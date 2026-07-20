/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {},
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://sentinel-review-api.railway.app',
  },
}

module.exports = nextConfig
