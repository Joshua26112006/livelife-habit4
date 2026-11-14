// The Python demo service (services/demo-livelife) serves the static demo pages.
// Next.js forwards /demo-livelife/* to it, so everything is one address (http://localhost:3000).
const DEMO = (process.env.DEMO_SERVICE_URL || "http://localhost:8080").replace(/\/+$/, "");

/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      { source: "/demo-livelife", destination: `${DEMO}/demo-livelife` },
      { source: "/demo-livelife/:path*", destination: `${DEMO}/demo-livelife/:path*` },
    ];
  },
};
export default nextConfig;
