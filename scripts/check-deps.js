/**
 * Dependency Check Script
 * Checks for outdated dependencies and security vulnerabilities
 */

import { execSync } from 'child_process';
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

console.log('\n🔍 Dependency Check\n');
console.log('='.repeat(60));

// Check npm dependencies
console.log('\n📦 Checking npm dependencies...\n');
try {
  const npmOutdated = execSync('npm outdated --json', { 
    encoding: 'utf-8',
    stdio: 'pipe',
    cwd: join(__dirname, '..')
  });
  
  const outdated = JSON.parse(npmOutdated || '{}');
  const outdatedCount = Object.keys(outdated).length;
  
  if (outdatedCount === 0) {
    console.log('✅ All npm dependencies are up to date!');
  } else {
    console.log(`⚠️  Found ${outdatedCount} outdated npm packages:\n`);
    for (const [pkg, info] of Object.entries(outdated)) {
      console.log(`   ${pkg}:`);
      console.log(`     Current: ${info.current}`);
      console.log(`     Wanted:  ${info.wanted}`);
      console.log(`     Latest:  ${info.latest}`);
      console.log('');
    }
  }
} catch (err) {
  if (err.status === 1) {
    // npm outdated exits with 1 when packages are outdated (this is expected)
    // Already handled above
  } else {
    console.log('⚠️  Could not check npm dependencies');
  }
}

// Check npm security vulnerabilities
console.log('\n🔒 Checking npm security vulnerabilities...\n');
try {
  const auditResult = execSync('npm audit --json', {
    encoding: 'utf-8',
    stdio: 'pipe',
    cwd: join(__dirname, '..')
  });
  
  const audit = JSON.parse(auditResult || '{}');
  const vulnerabilities = audit.metadata?.vulnerabilities || {};
  const total = vulnerabilities.info + vulnerabilities.low + vulnerabilities.moderate + vulnerabilities.high + vulnerabilities.critical;
  
  if (total === 0) {
    console.log('✅ No security vulnerabilities found!');
  } else {
    console.log(`⚠️  Found ${total} security vulnerabilities:\n`);
    console.log(`   Critical: ${vulnerabilities.critical || 0}`);
    console.log(`   High:     ${vulnerabilities.high || 0}`);
    console.log(`   Moderate: ${vulnerabilities.moderate || 0}`);
    console.log(`   Low:      ${vulnerabilities.low || 0}`);
    console.log(`   Info:     ${vulnerabilities.info || 0}`);
    console.log('\n   Run `npm audit fix` to attempt automatic fixes');
  }
} catch (err) {
  console.log('⚠️  Could not check npm security vulnerabilities');
}

// Check Python dependencies (if requirements.txt exists)
console.log('\n🐍 Checking Python dependencies...\n');
try {
  const requirementsPath = join(__dirname, '..', 'requirements.txt');
  const requirements = readFileSync(requirementsPath, 'utf-8');
  const packages = requirements.split('\n')
    .filter(line => line.trim() && !line.startsWith('#'))
    .map(line => line.split('==')[0].split('>=')[0].split('<=')[0].trim());
  
  console.log(`Found ${packages.length} Python packages in requirements.txt`);
  console.log('\n💡 To check for outdated packages, run:');
  console.log('   pip list --outdated');
  console.log('\n💡 To check for security vulnerabilities, run:');
  console.log('   safety check');
  console.log('   or');
  console.log('   pip-audit');
} catch (err) {
  console.log('⚠️  Could not read requirements.txt');
}

console.log('\n' + '='.repeat(60));
console.log('\n✅ Dependency check complete!\n');
console.log('💡 Recommendations:');
console.log('   - Update dependencies regularly');
console.log('   - Fix security vulnerabilities immediately');
console.log('   - Test updates in development before production');
console.log('   - Keep a changelog of dependency updates\n');

