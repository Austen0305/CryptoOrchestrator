/**
 * Global E2E Test Setup
 * Runs before all E2E tests to set up test environment
 */

import { chromium, FullConfig } from '@playwright/test';
import { spawn } from 'child_process';
import path from 'path';

let fastapiProcess: any = null;
let frontendProcess: any = null;

async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting global E2E test setup...');

  // Start FastAPI backend
  console.log('📦 Starting FastAPI backend...');
  const fastapiPath = path.join(process.cwd(), 'server_fastapi');
  fastapiProcess = spawn('python', ['-m', 'uvicorn', 'main:app', '--port', '8000'], {
    cwd: fastapiPath,
    stdio: 'pipe',
    env: {
      ...process.env,
      TESTING: 'true',
      DATABASE_URL: 'sqlite+aiosqlite:///./test_e2e.db',
    },
  });

  fastapiProcess.stdout.on('data', (data: Buffer) => {
    if (data.toString().includes('Application startup complete')) {
      console.log('✅ FastAPI backend started');
    }
  });

  fastapiProcess.stderr.on('data', (data: Buffer) => {
    console.error(`FastAPI error: ${data}`);
  });

  // Wait for backend to be ready
  await new Promise((resolve) => setTimeout(resolve, 5000));

  // Check if backend is responding
  try {
    const response = await fetch('http://localhost:8000/health');
    if (!response.ok) {
      throw new Error('Backend health check failed');
    }
    console.log('✅ Backend health check passed');
  } catch (error) {
    console.error('❌ Backend not responding:', error);
    throw error;
  }

  // Start frontend dev server if not already running
  const frontendUrl = config.projects[0].use.baseURL || 'http://localhost:5173';
  try {
    const response = await fetch(frontendUrl);
    if (response.ok) {
      console.log('✅ Frontend already running');
    }
  } catch (error) {
    console.log('📦 Starting frontend dev server...');
    frontendProcess = spawn('npm', ['run', 'dev'], {
      stdio: 'pipe',
      env: {
        ...process.env,
        VITE_API_URL: 'http://localhost:8000',
      },
    });

    frontendProcess.stdout.on('data', (data: Buffer) => {
      if (data.toString().includes('Local:')) {
        console.log('✅ Frontend started');
      }
    });

    // Wait for frontend to be ready
    await new Promise((resolve) => setTimeout(resolve, 10000));
  }

  console.log('✅ Global E2E test setup complete');
}

export default globalSetup;
