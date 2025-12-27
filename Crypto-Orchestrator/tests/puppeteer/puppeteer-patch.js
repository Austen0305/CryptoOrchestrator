/**
 * Puppeteer Patch for Node.js 25 Compatibility
 * Fixes "Cannot add property logLevel, object is not extensible" error
 * 
 * This patch works around a bug in Puppeteer where it tries to modify
 * a non-extensible configuration object in Node.js 25
 */

// Set environment variable before Puppeteer loads to prevent it from trying to modify config
if (typeof process !== 'undefined' && process.env) {
  process.env.PUPPETEER_LOGLEVEL = process.env.PUPPETEER_LOGLEVEL || 'warn';
}

// Re-export puppeteer - the environment variable should prevent the error
export { default } from 'puppeteer';
