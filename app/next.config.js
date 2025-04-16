/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Uncomment for static export (Option 4 in README)
  // output: 'export',
  
  // Load environment variables based on runtime environment
  publicRuntimeConfig: {
    apiBaseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1',
    apiAuthToken: process.env.NEXT_PUBLIC_API_AUTH_TOKEN,
    featureFlags: {
      enableTelemetry: process.env.NEXT_PUBLIC_ENABLE_TELEMETRY === 'true',
      enableAdvancedSearch: process.env.NEXT_PUBLIC_ENABLE_ADVANCED_SEARCH === 'true',
      enableDarkMode: process.env.NEXT_PUBLIC_ENABLE_DARK_MODE === 'true',
    },
    // Production flag - always false for mock data
    useMock: false
  },
  
  // Configure webpack if needed
  webpack: (config, { isServer }) => {
    // Add any webpack customizations here
    return config;
  },
  
  // Image configuration
  images: {
    domains: ['localhost'],
  },
  
  // Add rewrites if needed
  async rewrites() {
    return [
      // Example: redirect API requests when developing locally
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*'
      }
    ]
  },
  
  async headers() {
    return [
      {
        // Apply these headers to all routes
        source: "/:path*",
        headers: [
          {
            key: "Access-Control-Allow-Origin",
            value: "*",
          },
          {
            key: "Access-Control-Allow-Methods",
            value: "GET, POST, PUT, DELETE, OPTIONS",
          },
          {
            key: "Access-Control-Allow-Headers",
            value: "X-Requested-With, Content-Type, Accept",
          },
        ],
      },
    ];
  },
  
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
    NEXT_PUBLIC_USE_MOCK: process.env.NEXT_PUBLIC_USE_MOCK
  }
};

module.exports = nextConfig; 