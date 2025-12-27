/**
 * Check for deprecated packages in package.json and package-lock.json
 * Identifies packages that should be updated or replaced
 */

const fs = require('fs');
const path = require('path');

const projectRoot = path.join(__dirname, '../..');
const packageJsonPath = path.join(projectRoot, 'package.json');
const packageLockPath = path.join(projectRoot, 'package-lock.json');

function checkDeprecatedPackages() {
  console.log('🔍 Checking for deprecated packages...\n');

  if (!fs.existsSync(packageLockPath)) {
    console.log('❌ package-lock.json not found');
    return;
  }

  const packageLock = JSON.parse(fs.readFileSync(packageLockPath, 'utf8'));
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));

  const deprecatedPackages = [];
  const allPackages = {};

  // Collect all packages from package-lock.json
  function collectPackages(obj, parent = '') {
    if (obj.dependencies) {
      for (const [name, pkg] of Object.entries(obj.dependencies)) {
        const fullName = parent ? `${parent} > ${name}` : name;
        if (pkg.deprecated) {
          deprecatedPackages.push({
            name,
            fullName,
            version: pkg.version,
            deprecated: pkg.deprecated,
            parent: parent || 'root',
          });
        }
        allPackages[name] = {
          version: pkg.version,
          deprecated: pkg.deprecated,
        };
        if (pkg.dependencies) {
          collectPackages(pkg, fullName);
        }
      }
    }
  }

  collectPackages(packageLock);

  // Check direct dependencies in package.json
  const directDeps = {
    ...packageJson.dependencies,
    ...packageJson.devDependencies,
  };

  console.log('📦 Deprecated Packages Found:\n');

  if (deprecatedPackages.length === 0) {
    console.log('✅ No deprecated packages found in package-lock.json');
    return;
  }

  // Group by package name
  const grouped = {};
  for (const pkg of deprecatedPackages) {
    if (!grouped[pkg.name]) {
      grouped[pkg.name] = [];
    }
    grouped[pkg.name].push(pkg);
  }

  // Report findings
  let hasDirectDeprecated = false;
  for (const [name, instances] of Object.entries(grouped)) {
    const isDirect = name in directDeps;
    const marker = isDirect ? '⚠️  DIRECT' : '   ';
    if (isDirect) hasDirectDeprecated = true;

    console.log(`${marker} ${name}@${instances[0].version}`);
    console.log(`   Deprecated: ${instances[0].deprecated}`);
    if (isDirect) {
      console.log(`   ⚠️  This is a direct dependency - should be updated!`);
    }
    if (instances.length > 1) {
      console.log(`   Found in ${instances.length} dependency chains`);
    }
    console.log('');
  }

  // Summary
  console.log('\n📊 Summary:');
  console.log(`   Total deprecated packages: ${deprecatedPackages.length}`);
  console.log(`   Unique deprecated packages: ${Object.keys(grouped).length}`);
  console.log(`   Direct dependencies deprecated: ${hasDirectDeprecated ? 'YES ⚠️' : 'NO ✅'}`);

  // Recommendations
  console.log('\n💡 Recommendations:');
  const recommendations = [];

  for (const [name] of Object.entries(grouped)) {
    if (name in directDeps) {
      if (name.includes('web3modal') || name.includes('@web3modal')) {
        recommendations.push(
          `  - ${name}: Migrate to @reown/appkit (see https://docs.reown.com/appkit/upgrade/from-w3m-to-reown)`
        );
      } else if (name.includes('eslint')) {
        recommendations.push(
          `  - ${name}: Update to latest ESLint flat config format`
        );
      } else if (name.includes('glob') && name.match(/^glob@[0-8]\./)) {
        recommendations.push(`  - ${name}: Update to glob@^9.0.0`);
      } else {
        recommendations.push(`  - ${name}: Check package documentation for migration guide`);
      }
    }
  }

  if (recommendations.length > 0) {
    console.log('\n  Action Items:');
    recommendations.forEach((rec) => console.log(rec));
  } else {
    console.log('  ✅ No direct dependencies need immediate attention');
    console.log('  (Deprecated packages are only in transitive dependencies)');
  }

  // Write report
  const reportPath = path.join(projectRoot, 'docs/DEPRECATED_PACKAGES_REPORT.md');
  const report = {
    generated: new Date().toISOString(),
    summary: {
      total: deprecatedPackages.length,
      unique: Object.keys(grouped).length,
      direct: hasDirectDeprecated,
    },
    packages: grouped,
    recommendations,
  };

  fs.writeFileSync(
    reportPath,
    `# Deprecated Packages Report\n\nGenerated: ${report.generated}\n\n` +
      `## Summary\n\n` +
      `- Total deprecated packages: ${report.summary.total}\n` +
      `- Unique deprecated packages: ${report.summary.unique}\n` +
      `- Direct dependencies deprecated: ${report.summary.direct ? 'YES ⚠️' : 'NO ✅'}\n\n` +
      `## Packages\n\n` +
      Object.entries(grouped)
        .map(
          ([name, instances]) =>
            `### ${name}\n\n` +
            `- Version: ${instances[0].version}\n` +
            `- Deprecated: ${instances[0].deprecated}\n` +
            `- Direct dependency: ${name in directDeps ? 'YES' : 'NO'}\n` +
            `- Found in ${instances.length} dependency chain(s)\n`
        )
        .join('\n') +
      `\n## Recommendations\n\n` +
      recommendations.map((r) => `- ${r.replace(/^  - /, '')}`).join('\n') +
      `\n`
  );

  console.log(`\n📄 Report saved to: ${reportPath}`);
}

checkDeprecatedPackages();
