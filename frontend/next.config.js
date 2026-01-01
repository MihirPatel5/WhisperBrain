/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/voice',
        destination: 'http://localhost:8009/voice',
      },
    ];
  },
}

module.exports = nextConfig

