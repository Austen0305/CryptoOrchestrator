/**
 * Global E2E Test Teardown
 * Runs after all E2E tests to clean up test environment
 */

import { FullConfig } from '@playwright/test';
import { unlinkSync } from 'fs';
import path from 'path';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Starting global E2E test teardown...');

  // Clean up test database
  const testDbPath = path.join(process.cwd(), 'test_e2e.db');
  try {
    unlinkSync(testDbPath);
    console.log('✅ Test database cleaned up');
  } catch (error) {
    // Database might not exist, that's okay
    console.log('ℹ️  Test database cleanup skipped');
  }

  console.log('✅ Global E2E test teardown complete');
}

export default globalTeardown;
