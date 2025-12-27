/**
 * Puppeteer Configuration
 * Centralized configuration for all Puppeteer tests
 */

export default {
  // Browser launch options
  launch: {
    headless: process.env.CI === 'true' || process.env.HEADLESS === 'true',
    devtools: false,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--no-first-run',
      '--no-zygote',
      '--disable-gpu',
    ],
    defaultViewport: {
      width: 1280,
      height: 720,
    },
    timeout: 30000, // 30 seconds
  },

  // Screenshot settings
  screenshot: {
    path: './tests/puppeteer/screenshots',
    fullPage: false,
    type: 'png',
  },

  // Test settings
  test: {
    timeout: 30000, // 30 seconds per test
    retries: process.env.CI ? 2 : 0,
    slowMo: process.env.SLOW_MO ? parseInt(process.env.SLOW_MO) : 0,
  },

  // URLs
  urls: {
    base: process.env.BASE_URL || 'http://localhost:5173',
    api: process.env.API_URL || 'http://localhost:8000',
  },

  // Viewport sizes for responsive testing
  viewports: {
    desktop: { width: 1920, height: 1080 },
    laptop: { width: 1366, height: 768 },
    tablet: { width: 768, height: 1024 },
    mobile: { width: 375, height: 667 },
  },

  // Wait times (in milliseconds)
  waits: {
    short: 1000,
    medium: 3000,
    long: 5000,
    veryLong: 10000,
  },
};
