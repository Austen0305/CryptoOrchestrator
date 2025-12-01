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
      manifest: {
        name: 'CryptoOrchestrator',
        short_name: 'CryptoOrch',
        theme_color: '#18181b',
        background_color: '#09090b',
        display: 'standalone',
        icons: [
          {
            src: '/icons/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/icons/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      }
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
          // React and React DOM
          if (id.includes('node_modules/react') || id.includes('node_modules/react-dom')) {
            return 'react-vendor';
          }
          // React Query
          if (id.includes('node_modules/@tanstack/react-query')) {
            return 'react-query';
          }
          // Charts
          if (id.includes('node_modules/recharts') || id.includes('node_modules/lightweight-charts')) {
            return 'charts';
          }
          // UI Components (Radix UI)
          if (id.includes('node_modules/@radix-ui')) {
            return 'radix-ui';
          }
          // Icons
          if (id.includes('node_modules/lucide-react')) {
            return 'icons';
          }
          // TensorFlow (ML)
          if (id.includes('node_modules/@tensorflow')) {
            return 'tensorflow';
          }
          // Large libraries
          if (id.includes('node_modules/framer-motion')) {
            return 'animations';
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
  'lucide-react',
      'class-variance-authority',
  'recharts'
    ]
  }
}));
