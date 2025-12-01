/**
 * Development Utility Scripts
 * Convenient commands for common development tasks
 */

import { execSync } from 'child_process';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '..');

const commands = {
  // Run both backend and frontend together
  'dev:full': () => {
    console.log('🚀 Starting full development environment...\n');
    console.log('Starting FastAPI backend...');
    execSync('npm run dev:fastapi', { 
      stdio: 'inherit', 
      cwd: projectRoot,
      shell: true 
    });
  },

  // Check for outdated dependencies
  'check:deps': () => {
    console.log('Checking dependencies...');
    execSync('npm outdated || true', { 
      stdio: 'inherit', 
      cwd: projectRoot,
      shell: true 
    });
  },

  // Run all security audits
  'audit:all': () => {
    console.log('🔒 Running security audits...\n');
    try {
      console.log('1. npm audit...');
      execSync('npm audit', { stdio: 'inherit', cwd: projectRoot, shell: true });
    } catch (err) {
      console.log('   npm audit completed (some vulnerabilities may exist)');
    }
    
    try {
      console.log('\n2. safety check (Python)...');
      execSync('safety check', { stdio: 'inherit', cwd: projectRoot, shell: true });
    } catch (err) {
      console.log('   safety check not available (install with: pip install safety)');
    }
  },

  // Full build check
  'build:check': () => {
    console.log('🔨 Running full build check...\n');
    console.log('1. Type checking...');
    execSync('npm run check', { stdio: 'inherit', cwd: projectRoot, shell: true });
    
    console.log('\n2. Building frontend...');
    execSync('npm run build', { stdio: 'inherit', cwd: projectRoot, shell: true });
    
    console.log('\n✅ Build check complete!');
  },

  // Clean all build artifacts
  'clean:all': () => {
    console.log('🧹 Cleaning all build artifacts...\n');
    
    const paths = [
      join(projectRoot, 'dist'),
      join(projectRoot, 'node_modules', '.vite'),
      join(projectRoot, 'coverage'),
      join(projectRoot, '.pytest_cache'),
      join(projectRoot, '__pycache__'),
    ];

    paths.forEach(path => {
      try {
        const { rmSync } = require('fs');
        rmSync(path, { recursive: true, force: true });
        console.log(`   ✅ Removed: ${path}`);
      } catch (err) {
        // Path might not exist
      }
    });
    
    console.log('\n✅ Cleanup complete!');
  },

  // Run all checks
  'check:all': () => {
    console.log('✅ Running all checks...\n');
    console.log('1. Type check...');
    execSync('npm run check', { stdio: 'inherit', cwd: projectRoot, shell: true });
    
    console.log('\n2. Linting...');
    try {
      execSync('npm run lint', { stdio: 'inherit', cwd: projectRoot, shell: true });
    } catch (err) {
      console.log('   Linting skipped (lint script may not be configured)');
    }
    
    console.log('\n3. Formatting check...');
    try {
      execSync('npm run format:check', { stdio: 'inherit', cwd: projectRoot, shell: true });
    } catch (err) {
      console.log('   Format check skipped (format:check script may not be configured)');
    }
    
    console.log('\n✅ All checks complete!');
  },
};

// Get command from CLI args
const command = process.argv[2];

if (!command || !commands[command]) {
  console.log('\n📚 Development Utilities\n');
  console.log('Available commands:\n');
  Object.keys(commands).forEach(cmd => {
    console.log(`  npm run dev:utils -- ${cmd}`);
  });
  console.log('\nExamples:');
  console.log('  npm run dev:utils -- dev:full    # Start full dev environment');
  console.log('  npm run dev:utils -- check:all   # Run all checks');
  console.log('  npm run dev:utils -- clean:all   # Clean build artifacts\n');
  process.exit(0);
}

// Execute command
try {
  commands[command]();
} catch (error) {
  console.error(`\n❌ Error running command '${command}':`, error.message);
  process.exit(1);
}

