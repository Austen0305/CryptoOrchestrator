/**
 * Global E2E Test Teardown
 * Runs after all E2E tests to clean up test environment
 * Updated: December 6, 2025 - Improved cleanup
 */

import { FullConfig } from '@playwright/test';
import { existsSync, unlinkSync } from 'fs';
import path from 'path';

async function globalTeardown(config: FullConfig) {
  console.log('[INFO] Starting global E2E test teardown...');

  // Clean up test database
  const testDbPath = path.join(process.cwd(), 'test_e2e.db');
  if (existsSync(testDbPath)) {
    try {
      unlinkSync(testDbPath);
      console.log('[SUCCESS] Test database cleaned up');
    } catch (error: any) {
      console.warn('[WARN] Could not clean up test database:', error.message);
    }
  } else {
    console.log('[INFO] Test database does not exist, skipping cleanup');
  }

  // Note: Backend and frontend processes are managed by Playwright's webServer
  // and the global setup, so they should be cleaned up automatically

  console.log('[SUCCESS] Global E2E test teardown complete');
}

export default globalTeardown;
