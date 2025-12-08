const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  output: process.env.NODE_ENV === 'production' ? 'standalone' : undefined,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || 'Portfolio Superapp',
  },
  images: {
    domains: ['localhost'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
  experimental: {
    optimizePackageImports: ['lucide-react', 'recharts'],
    esmExternals: 'loose',
  },
  transpilePackages: ['lightweight-charts'],
  webpack: (config, { isServer }) => {
    // Resolve modules from workspace root for pnpm workspaces
    const originalResolve = config.resolve || {}

    // Ensure modules array exists
    const modules = [
      path.resolve(__dirname, 'node_modules'),
      path.resolve(__dirname, '../node_modules'),
      ...(Array.isArray(originalResolve.modules) ? originalResolve.modules : []),
      'node_modules',
    ]

    config.resolve = {
      ...originalResolve,
      modules,
    }

    // Add alias for lightweight-charts to resolve from root node_modules
    if (!config.resolve.alias) {
      config.resolve.alias = {}
    }

    // Set alias to local node_modules (symlink points to root)
    const localChartsPath = path.resolve(__dirname, 'node_modules/lightweight-charts')
    config.resolve.alias['lightweight-charts'] = localChartsPath

    // lightweight-charts is client-side only
    if (!isServer) {
      config.resolve.fallback = {
        ...(config.resolve.fallback || {}),
        fs: false,
      }
    }

    return config
  },
}

module.exports = nextConfig
