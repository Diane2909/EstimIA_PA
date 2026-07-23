/** @type {import('next').NextConfig} */
const nextConfig = {
  // Build autonome pour l'image Docker (server.js minimal sans node_modules complet)
  output: "standalone",
};

export default nextConfig;
