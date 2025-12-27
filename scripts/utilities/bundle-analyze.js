/**
 * Bundle Analysis Script
 * Analyzes frontend bundle size and provides optimization recommendations
 */

import { readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const CHUNK_SIZE_WARNING = 1024 * 1024; // 1MB
const TOTAL_SIZE_WARNING = 5 * 1024 * 1024; // 5MB

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function analyzeBundle() {
  try {
    const distPath = join(__dirname, '..', 'dist');
    const manifestPath = join(distPath, '.vite', 'manifest.json');
    
    // Try to read Vite manifest
    let manifest = {};
    try {
      const manifestContent = readFileSync(manifestPath, 'utf-8');
      manifest = JSON.parse(manifestContent);
    } catch (err) {
      console.warn('⚠️  Could not read Vite manifest. Make sure to run `npm run build` first.');
      return;
    }

    console.log('\n📦 Bundle Analysis Report\n');
    console.log('='.repeat(60));

    const chunks = [];
    let totalSize = 0;

    // Analyze chunks from manifest
    for (const [file, info] of Object.entries(manifest)) {
      if (info.isEntry || info.isDynamicEntry) {
        const filePath = join(distPath, info.file);
        try {
          const stats = require('fs').statSync(filePath);
          chunks.push({
            name: file,
            size: stats.size,
            isEntry: info.isEntry,
            isDynamic: info.isDynamicEntry,
          });
          totalSize += stats.size;
        } catch (err) {
          // File might not exist
        }
      }
    }

    // Sort by size (largest first)
    chunks.sort((a, b) => b.size - a.size);

    // Display results
    console.log('\n📊 Bundle Chunks:\n');
    chunks.forEach((chunk, index) => {
      const size = formatBytes(chunk.size);
      const warning = chunk.size > CHUNK_SIZE_WARNING ? ' ⚠️  LARGE' : '';
      const type = chunk.isEntry ? '[ENTRY]' : chunk.isDynamic ? '[DYNAMIC]' : '[CHUNK]';
      console.log(`${(index + 1).toString().padStart(2)}. ${type} ${chunk.name.padEnd(40)} ${size.padStart(10)}${warning}`);
    });

    console.log('\n' + '-'.repeat(60));
    const totalFormatted = formatBytes(totalSize);
    const totalWarning = totalSize > TOTAL_SIZE_WARNING ? ' ⚠️  LARGE BUNDLE' : '';
    console.log(`Total Bundle Size: ${totalFormatted.padStart(20)}${totalWarning}`);

    // Recommendations
    console.log('\n💡 Recommendations:\n');
    
    const largeChunks = chunks.filter(c => c.size > CHUNK_SIZE_WARNING);
    if (largeChunks.length > 0) {
      console.log('⚠️  Large chunks detected:');
      largeChunks.forEach(chunk => {
        console.log(`   - ${chunk.name}: ${formatBytes(chunk.size)}`);
        console.log(`     Consider: Code splitting, lazy loading, or dependency optimization`);
      });
    }

    if (totalSize > TOTAL_SIZE_WARNING) {
      console.log('\n⚠️  Total bundle size exceeds 5MB:');
      console.log('   - Consider aggressive code splitting');
      console.log('   - Review large dependencies');
      console.log('   - Enable gzip/brotli compression');
    }

    // Check for common optimization opportunities
    console.log('\n🔍 Optimization Opportunities:\n');
    console.log('   ✓ Review Vite build output for detailed chunk analysis');
    console.log('   ✓ Use dynamic imports for heavy components');
    console.log('   ✓ Enable tree shaking for unused exports');
    console.log('   ✓ Consider replacing large libraries with lighter alternatives');

    console.log('\n' + '='.repeat(60));
    console.log('\n✅ Analysis complete!\n');

  } catch (error) {
    console.error('❌ Error analyzing bundle:', error.message);
    console.error('\nMake sure to:');
    console.error('  1. Run `npm run build` first');
    console.error('  2. Check that dist/ folder exists');
    process.exit(1);
  }
}

// Run analysis
analyzeBundle();

