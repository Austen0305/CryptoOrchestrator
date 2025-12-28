import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";
import { visualizer } from 'rollup-plugin-visualizer';
import { VitePWA } from 'vite-plugin-pwa';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
    visualizer({
      open: mode === 'development',
      gzipSize: true,
      brotliSize: true
    }),
    VitePWA({
      registerType: 'autoUpdate',
      // Disable service worker in development to prevent caching issues
      devOptions: {
        enabled: false,
        type: 'module',
      },
      // Only enable in production
      injectRegister: mode === 'production' ? 'auto' : null,
      // Use auto-generated service worker (simpler for Vercel deployment)
      strategies: 'generateSW',
      // Workbox options
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\./,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 5 * 60, // 5 minutes
              },
            },
          },
          {
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
            handler: 'CacheFirst',
            options: {
              cacheName: 'image-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 7 * 24 * 60 * 60, // 7 days
              },
            },
          },
        ],
      },
      manifest: {
        name: 'CryptoOrchestrator',
        short_name: 'CryptoOrch',
        description: 'Professional cryptocurrency trading automation platform',
        theme_color: '#18181b',
        background_color: '#09090b',
        display: 'standalone',
        orientation: 'portrait',
        start_url: '/',
        scope: '/',
        icons: [
          {
            src: '/icons/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png',
            purpose: 'any maskable',
          },
          {
            src: '/icons/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable',
          },
        ],
        shortcuts: [
          {
            name: 'Dashboard',
            short_name: 'Dashboard',
            description: 'View trading dashboard',
            url: '/dashboard',
            icons: [{ src: '/icons/icon-192x192.png', sizes: '192x192' }],
          },
          {
            name: 'Trading',
            short_name: 'Trading',
            description: 'Open trading interface',
            url: '/trading',
            icons: [{ src: '/icons/icon-192x192.png', sizes: '192x192' }],
          },
        ],
        categories: ['finance', 'productivity'],
        screenshots: [],
      },
    })
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "client", "src"),
      "@shared": path.resolve(__dirname, "shared"),
    },
  },
  root: path.resolve(__dirname, "client"),
  build: {
    outDir: path.resolve(__dirname, "dist"),
    emptyOutDir: true,
    sourcemap: mode === 'production' ? false : true, // Disable sourcemaps in production for smaller bundles
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: mode === 'production', // Remove console.log in production
        drop_debugger: true,
      },
    },
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // CRITICAL: React and React DOM must load FIRST in a separate chunk
          // This ensures React is available before any React-dependent libraries
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
            return 'react-vendor'; // Separate chunk that loads first
          }
          // All React-dependent libraries go in vendor chunk (loads after react-vendor)
          // UI Components (Radix UI) - depends on React
          if (id.includes('node_modules/@radix-ui')) {
            return 'vendor';
          }
          // React Query - depends on React
          if (id.includes('node_modules/@tanstack/react-query')) {
            return 'vendor';
          }
          // Web3 libraries - depend on React (wagmi uses React hooks)
          // Include all wagmi-related packages (@wagmi, wagmi, viem, web3modal, reown)
          if (id.includes('node_modules/wagmi') || 
              id.includes('node_modules/@wagmi') ||
              id.includes('node_modules/viem') || 
              id.includes('node_modules/@web3modal') ||
              id.includes('node_modules/@reown')) {
            return 'vendor';
          }
          // Form libraries - depend on React (react-hook-form uses React hooks)
          if (id.includes('node_modules/react-hook-form') || id.includes('node_modules/@hookform')) {
            return 'vendor';
          }
          // Charts - both recharts and lightweight-charts can have initialization issues when split
          // Put both in vendor to avoid chunk loading order problems
          if (id.includes('node_modules/recharts') || id.includes('node_modules/lightweight-charts')) {
            return 'vendor'; // Avoid initialization order issues
          }
          // Icons - tree-shake unused icons
          if (id.includes('node_modules/lucide-react')) {
            return 'icons';
          }
          // TensorFlow (ML) - lazy load when needed
          if (id.includes('node_modules/@tensorflow')) {
            return 'tensorflow';
          }
          // Large libraries
          if (id.includes('node_modules/framer-motion')) {
            return 'animations';
          }
          // Date utilities
          if (id.includes('node_modules/date-fns')) {
            return 'date-utils';
          }
          // Validation
          if (id.includes('node_modules/zod')) {
            return 'validation';
          }
          // All other node_modules
          if (id.includes('node_modules')) {
            return 'vendor';
          }
        },
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: 'assets/[ext]/[name]-[hash].[ext]',
      },
    },
    chunkSizeWarningLimit: 1000, // Warn if chunk exceeds 1MB
  },
  server: {
    host: 'localhost',
    port: 5173,
    strictPort: false,
    open: false,
    // Enable HMR (Hot Module Replacement) for better dev experience
    hmr: {
      overlay: true,
    },
    // Force reload on file changes
    watch: {
      usePolling: false,
      interval: 100,
    },
    fs: {
      strict: true,
      deny: ["**/.*"],
    },
    proxy: mode === 'development' ? {
      "/api": {
        target: "http://localhost:8000", // FastAPI server
        changeOrigin: true,
        secure: false,
      },
      "/ws": {
        target: "ws://localhost:8000",
        ws: true,
        changeOrigin: true,
        secure: false,
      }
    } : undefined,
  },
  base: mode === 'production' ? './' : '/', // Relative paths for Electron
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'class-variance-authority',
      '@tanstack/react-query',
    ],
    exclude: [
      // Exclude heavy libraries that should be lazy loaded
      '@tensorflow/tfjs',
    ]
  }
}));
