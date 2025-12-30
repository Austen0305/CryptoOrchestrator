#!/usr/bin/env node

/**
 * Build Verification Script
 * Verifies that all required dependencies are installed and the build can succeed
 */

import { execSync } from 'child_process';
import { existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = resolve(__dirname, '../..');

console.log('🔍 Verifying build configuration...\n');

// Check required dependencies
const requiredDeps = [
  '@vitejs/plugin-react',
  'vite',
  'react',
  'react-dom',
  'typescript'
];

let allGood = true;

console.log('📦 Checking dependencies...');
for (const dep of requiredDeps) {
  const depPath = resolve(rootDir, 'node_modules', dep);
  if (existsSync(depPath)) {
    console.log(`  ✅ ${dep}`);
  } else {
    console.log(`  ❌ ${dep} - MISSING`);
    allGood = false;
  }
}

// Check build output directory
console.log('\n📁 Checking build configuration...');
const distDir = resolve(rootDir, 'dist');
if (!existsSync(distDir)) {
  console.log('  ℹ️  dist/ directory will be created during build');
}

// Check vite.config.ts
const viteConfig = resolve(rootDir, 'vite.config.ts');
if (existsSync(viteConfig)) {
  console.log('  ✅ vite.config.ts exists');
} else {
  console.log('  ❌ vite.config.ts missing');
  allGood = false;
}

// Check package.json build script
console.log('\n🔧 Checking build scripts...');
try {
  const packageJson = JSON.parse(
    require('fs').readFileSync(resolve(rootDir, 'package.json'), 'utf8')
  );
  if (packageJson.scripts && packageJson.scripts.build) {
    console.log(`  ✅ Build script: ${packageJson.scripts.build}`);
  } else {
    console.log('  ❌ No build script found');
    allGood = false;
  }
} catch (e) {
  console.log('  ❌ Could not read package.json');
  allGood = false;
}

if (allGood) {
  console.log('\n✅ All checks passed! Build should succeed.');
  process.exit(0);
} else {
  console.log('\n❌ Some checks failed. Please install missing dependencies:');
  console.log('   npm install --legacy-peer-deps');
  process.exit(1);
}
