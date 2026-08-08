
/** @type {import('next').NextConfig} */
const nextConfig = {
  trailingSlash: true,
  basePath: "/legalRag",
  // Optional but recommended: if any <img> tags reference assets by
  // absolute path, this keeps those consistent too.
  assetPrefix: "/legalRag",
};

module.exports = nextConfig;
// Also update wherever your frontend calls the backend API - point it at
// the public HTTPS URL directly (see .env.production.example), e.g.:
//   fetch(`${process.env.NEXT_PUBLIC_API_URL}/query`, ...)
// rather than a relative /api/query path, since NEXT_PUBLIC_API_URL will
// resolve to https://app.adityakashyap.work/legalRag/api directly.
