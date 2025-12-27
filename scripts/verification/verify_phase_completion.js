/**
 * Verify Phase 7 & 8 Completion
 * Checks that all optimizations and code quality improvements are in place
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.join(__dirname, '../..');

const checks = {
  phase7: {
    name: 'Phase 7: Performance & Polish',
    checks: [
      {
        name: 'Load testing script',
        file: 'scripts/utilities/load_test.py',
        description: 'Comprehensive load testing with 10+ endpoints',
      },
      {
        name: 'Bundle optimization config',
        file: 'vite.config.ts',
        description: 'Manual chunk splitting configured',
        contains: ['manualChunks'],
      },
      {
        name: 'Image optimization utility',
        file: 'client/src/utils/imageOptimization.ts',
        description: 'WebP/AVIF optimization',
      },
      {
        name: 'LazyImage component',
        file: 'client/src/components/LazyImage.tsx',
        description: 'Lazy loading image component',
      },
      {
        name: 'Virtual scrolling hook',
        file: 'client/src/hooks/useVirtualScroll.ts',
        description: 'Virtual scrolling for large lists',
      },
      {
        name: 'VirtualizedList component',
        file: 'client/src/components/VirtualizedList.tsx',
        description: 'Virtualized list component',
      },
      {
        name: 'Request deduplication',
        file: 'client/src/utils/performance.ts',
        description: 'Request deduplication utility',
        contains: ['deduplicateRequest'],
      },
      {
        name: 'Query client deduplication',
        file: 'client/src/lib/queryClient.ts',
        description: 'React Query deduplication configured',
      },
    ],
  },
  phase8: {
    name: 'Phase 8: Code Quality & Cleanup',
    checks: [
      {
        name: 'Black formatter config',
        file: 'pyproject.toml',
        description: 'Black Python formatter configured',
        contains: ['[tool.black]'],
      },
      {
        name: 'ESLint config',
        file: '.eslintrc.json',
        description: 'ESLint TypeScript linting configured',
      },
      {
        name: 'MyPy config',
        file: 'pyproject.toml',
        description: 'MyPy type checking configured',
        contains: ['[tool.mypy]'],
      },
      {
        name: 'Unused imports finder',
        file: 'scripts/find_unused_imports.py',
        description: 'Tool to find unused Python imports',
        optional: true, // Mentioned in Todo.md but may not exist yet
      },
      {
        name: 'Unused components finder',
        file: 'scripts/find_unused_components.js',
        description: 'Tool to find unused React components',
        optional: true, // Mentioned in Todo.md but may not exist yet
      },
      {
        name: 'Deprecated packages checker',
        file: 'scripts/utilities/check_deprecated_packages.js',
        description: 'Tool to check for deprecated npm packages',
      },
    ],
  },
};

function checkFile(filePath, contains = null, optional = false) {
  const fullPath = path.join(projectRoot, filePath);
  
  if (!fs.existsSync(fullPath)) {
    return { exists: false, error: 'File not found', optional };
  }

  if (contains) {
    const content = fs.readFileSync(fullPath, 'utf8');
    const hasContent = contains.some((str) => content.includes(str));
    return { exists: true, hasContent };
  }

  return { exists: true };
}

function verifyPhase(phase) {
  console.log(`\n🔍 Verifying ${phase.name}...\n`);

  let passed = 0;
  let failed = 0;

  for (const check of phase.checks) {
    const result = checkFile(check.file, check.contains, check.optional);
    
    if (!result.exists) {
      if (check.optional) {
        console.log(`⏸️  ${check.name} (optional)`);
        console.log(`   ${check.description}`);
        console.log(`   Note: File not found but marked as optional`);
        // Don't count optional as failed
      } else {
        console.log(`❌ ${check.name}`);
        console.log(`   File: ${check.file}`);
        console.log(`   Error: ${result.error || 'Not found'}`);
        failed++;
      }
    } else if (check.contains && !result.hasContent) {
      console.log(`⚠️  ${check.name}`);
      console.log(`   File: ${check.file}`);
      console.log(`   Warning: Expected content not found`);
      failed++;
    } else {
      console.log(`✅ ${check.name}`);
      console.log(`   ${check.description}`);
      passed++;
    }
  }

  return { passed, failed, total: phase.checks.length };
}

function main() {
  console.log('🚀 Phase 7 & 8 Completion Verification\n');
  console.log('=' .repeat(60));

  const phase7Results = verifyPhase(checks.phase7);
  const phase8Results = verifyPhase(checks.phase8);

  console.log('\n' + '='.repeat(60));
  console.log('\n📊 Summary:\n');

  console.log(`Phase 7: ${phase7Results.passed}/${phase7Results.total} checks passed`);
  if (phase7Results.failed > 0) {
    console.log(`   ⚠️  ${phase7Results.failed} checks failed`);
  }

  console.log(`Phase 8: ${phase8Results.passed}/${phase8Results.total} checks passed`);
  if (phase8Results.failed > 0) {
    console.log(`   ⚠️  ${phase8Results.failed} checks failed`);
  }

  const totalPassed = phase7Results.passed + phase8Results.passed;
  const totalChecks = phase7Results.total + phase8Results.total;
  const percentage = ((totalPassed / totalChecks) * 100).toFixed(1);

  console.log(`\nOverall: ${totalPassed}/${totalChecks} checks passed (${percentage}%)`);

  if (totalPassed === totalChecks) {
    console.log('\n✅ All checks passed! Phases 7 & 8 are complete.');
  } else {
    console.log('\n⚠️  Some checks failed. Review the output above.');
  }

  // Write report
  const reportPath = path.join(projectRoot, 'docs/PHASE_VERIFICATION_REPORT.md');
  const report = {
    generated: new Date().toISOString(),
    phase7: {
      ...phase7Results,
      percentage: ((phase7Results.passed / phase7Results.total) * 100).toFixed(1),
    },
    phase8: {
      ...phase8Results,
      percentage: ((phase8Results.passed / phase8Results.total) * 100).toFixed(1),
    },
    overall: {
      passed: totalPassed,
      total: totalChecks,
      percentage,
    },
  };

  fs.writeFileSync(
    reportPath,
    `# Phase 7 & 8 Verification Report\n\n` +
      `Generated: ${report.generated}\n\n` +
      `## Phase 7: Performance & Polish\n\n` +
      `- Passed: ${report.phase7.passed}/${report.phase7.total} (${report.phase7.percentage}%)\n` +
      `- Failed: ${report.phase7.failed}\n\n` +
      `## Phase 8: Code Quality & Cleanup\n\n` +
      `- Passed: ${report.phase8.passed}/${report.phase8.total} (${report.phase8.percentage}%)\n` +
      `- Failed: ${report.phase8.failed}\n\n` +
      `## Overall\n\n` +
      `- Passed: ${report.overall.passed}/${report.overall.total} (${report.overall.percentage}%)\n\n` +
      `**Status**: ${totalPassed === totalChecks ? '✅ All checks passed' : '⚠️ Some checks failed'}\n`
  );

  console.log(`\n📄 Report saved to: ${reportPath}`);
}

main();
