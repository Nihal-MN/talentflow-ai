/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone output keeps the Docker image small (no node_modules copy).
  output: "standalone",
  reactStrictMode: true,
};

export default nextConfig;
