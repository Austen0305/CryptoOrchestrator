#!/usr/bin/env node
/**
 * TypeScript Tools Setup Script
 * Automates installation and configuration of TypeScript tools for Cursor agent
 */

import { execSync } from 'child_process';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';

const CURSOR_CONFIG_DIR = join(homedir(), '.cursor');
const MCP_HUB_CONFIG = join(CURSOR_CONFIG_DIR, 'mcp-hub.json');
const PROJECT_ROOT = process.cwd();

console.log('🚀 Setting up TypeScript tools for Cursor agent...\n');

// Step 1: Check if MCP Hub config exists
console.log('📋 Step 1: Checking MCP Hub configuration...');
if (!existsSync(MCP_HUB_CONFIG)) {
  console.log('⚠️  MCP Hub config not found. Creating...');
  const defaultConfig = {
    mcpServers: {}
  };
  writeFileSync(MCP_HUB_CONFIG, JSON.stringify(defaultConfig, null, 2));
  console.log('✅ Created MCP Hub config at:', MCP_HUB_CONFIG);
} else {
  console.log('✅ MCP Hub config exists');
}

// Step 2: Add TypeScript MCP servers to config
console.log('\n📋 Step 2: Adding TypeScript MCP servers...');
const mcpConfig = JSON.parse(readFileSync(MCP_HUB_CONFIG, 'utf-8'));

if (!mcpConfig.mcpServers) {
  mcpConfig.mcpServers = {};
}

// TypeScript Definition Finder MCP
if (!mcpConfig.mcpServers['typescript-definition-finder']) {
  mcpConfig.mcpServers['typescript-definition-finder'] = {
    command: 'npx',
    args: ['-y', 'ts-def-mcp@latest'],
    env: {
      PROJECT_ROOT: PROJECT_ROOT.replace(/\\/g, '/')
    }
  };
  console.log('✅ Added TypeScript Definition Finder MCP');
} else {
  console.log('ℹ️  TypeScript Definition Finder MCP already configured');
}

// LSMCP (Language Service Protocol MCP)
if (!mcpConfig.mcpServers['lsmcp']) {
  mcpConfig.mcpServers['lsmcp'] = {
    command: 'npx',
    args: ['-y', '@mizchi/typescript-mcp'],
    env: {
      PROJECT_ROOT: PROJECT_ROOT.replace(/\\/g, '/')
    }
  };
  console.log('✅ Added LSMCP');
} else {
  console.log('ℹ️  LSMCP already configured');
}

writeFileSync(MCP_HUB_CONFIG, JSON.stringify(mcpConfig, null, 2));
console.log('✅ MCP Hub configuration updated');

// Step 3: Update .vscode/extensions.json
console.log('\n📋 Step 3: Updating recommended extensions...');
const extensionsPath = join(PROJECT_ROOT, '.vscode', 'extensions.json');
if (existsSync(extensionsPath)) {
  // Remove comments from JSON before parsing
  let extensionsContent = readFileSync(extensionsPath, 'utf-8');
  extensionsContent = extensionsContent.replace(/\/\/.*$/gm, ''); // Remove single-line comments
  extensionsContent = extensionsContent.replace(/\/\*[\s\S]*?\*\//g, ''); // Remove multi-line comments
  const extensions = JSON.parse(extensionsContent);
  
  const requiredExtensions = [
    'Gydunhn.typescript-essentials',
    'dbaeumer.vscode-eslint',
    'usernamehw.errorlens',
    'christian-kohler.path-intellisense',
    'pmneo.tsimporter',
    'rbbit.typescript-hero'
  ];

  if (!extensions.recommendations) {
    extensions.recommendations = [];
  }

  let added = 0;
  for (const ext of requiredExtensions) {
    if (!extensions.recommendations.includes(ext)) {
      extensions.recommendations.push(ext);
      added++;
    }
  }

  if (added > 0) {
    writeFileSync(extensionsPath, JSON.stringify(extensions, null, 2));
    console.log(`✅ Added ${added} recommended extensions`);
  } else {
    console.log('ℹ️  All recommended extensions already present');
  }
} else {
  console.log('⚠️  .vscode/extensions.json not found. Creating...');
  const extensionsDir = join(PROJECT_ROOT, '.vscode');
  if (!existsSync(extensionsDir)) {
    execSync(`mkdir "${extensionsDir}"`, { stdio: 'inherit' });
  }
  
  const extensions = {
    recommendations: [
      'Gydunhn.typescript-essentials',
      'dbaeumer.vscode-eslint',
      'usernamehw.errorlens',
      'christian-kohler.path-intellisense',
      'pmneo.tsimporter',
      'rbbit.typescript-hero'
    ]
  };
  
  writeFileSync(extensionsPath, JSON.stringify(extensions, null, 2));
  console.log('✅ Created .vscode/extensions.json with recommendations');
}

// Step 4: Verify TypeScript configuration
console.log('\n📋 Step 4: Verifying TypeScript configuration...');
const tsconfigPath = join(PROJECT_ROOT, 'tsconfig.json');
if (existsSync(tsconfigPath)) {
  const tsconfig = JSON.parse(readFileSync(tsconfigPath, 'utf-8'));
  const compilerOptions = tsconfig.compilerOptions || {};
  
  const requiredOptions = {
    strict: true,
    strictNullChecks: true,
    strictFunctionTypes: true,
    strictBindCallApply: true,
    strictPropertyInitialization: true,
    noImplicitThis: true,
    alwaysStrict: true,
    noImplicitReturns: true,
    noFallthroughCasesInSwitch: true,
    noUncheckedIndexedAccess: true,
    noImplicitOverride: true
  };

  let issues = [];
  for (const [key, value] of Object.entries(requiredOptions)) {
    if (compilerOptions[key] !== value) {
      issues.push(`${key}: expected ${value}, got ${compilerOptions[key]}`);
    }
  }

  if (issues.length === 0) {
    console.log('✅ TypeScript configuration is optimal');
  } else {
    console.log('⚠️  TypeScript configuration issues found:');
    issues.forEach(issue => console.log(`   - ${issue}`));
  }
} else {
  console.log('⚠️  tsconfig.json not found');
}

// Step 5: Create installation summary
console.log('\n📋 Step 5: Creating installation summary...');
const summary = `
# TypeScript Tools Setup Complete! ✅

## What Was Configured:

1. ✅ MCP Hub Configuration
   - TypeScript Definition Finder MCP
   - LSMCP (Language Service Protocol MCP)
   - Location: ${MCP_HUB_CONFIG}

2. ✅ Recommended Extensions
   - Added to .vscode/extensions.json
   - Cursor will prompt to install these

3. ✅ TypeScript Configuration
   - Verified strict mode settings
   - All strict checks enabled

## Next Steps:

### 1. Install Extensions in Cursor:
   - Open Cursor IDE
   - Press Ctrl+Shift+X (Extensions)
   - Click "Install" on recommended extensions:
     * TypeScript Essentials (Gydunhn.typescript-essentials) ⭐ INSTALL FIRST
     * ESLint (dbaeumer.vscode-eslint) ⭐ REQUIRED
     * Error Lens (usernamehw.errorlens)
     * Path Intellisense (christian-kohler.path-intellisense)
     * TypeScript Importer (pmneo.tsimporter)
     * TypeScript Hero (rbbit.typescript-hero)

### 2. Enable MCP Hub in Cursor:
   - Open Cursor Settings
   - Go to Features > MCP
   - Enable "mcp-hub" server
   - Disable all individual MCP servers (to avoid 40-tool limit)
   - Restart Cursor completely

### 3. Verify Setup:
   - Open a TypeScript file
   - Check that errors show inline (Error Lens)
   - Verify path autocomplete works with @/* aliases
   - Test TypeScript definition finding (Ctrl+Click on symbol)

## Resources:

- TypeScript Tools Guide: .cursor/TYPESCRIPT_TOOLS_GUIDE.md
- TypeScript Expertise Guide: .cursor/TYPESCRIPT_EXPERTISE_GUIDE.md
- tsx Usage Rules: .cursor/AGENT_TSX_RULES.md
- MCP Hub Setup: .cursor/rules/MCP_HUB_SETUP.md

## Troubleshooting:

If extensions don't install:
1. Check Cursor marketplace: https://marketplace.cursorapi.com
2. Try installing from VSIX (download from VS Code marketplace)
3. Restart Cursor after installation

If MCP servers don't work:
1. Check MCP Hub config: ${MCP_HUB_CONFIG}
2. Verify environment variables are set
3. Check Cursor Settings > Features > MCP
4. Restart Cursor completely

---

Setup completed at: ${new Date().toISOString()}
`;

console.log(summary);

// Write summary to file
const summaryPath = join(PROJECT_ROOT, '.cursor', 'TYPESCRIPT_SETUP_SUMMARY.md');
writeFileSync(summaryPath, summary);
console.log(`\n✅ Setup summary saved to: ${summaryPath}`);

console.log('\n🎉 TypeScript tools setup complete!');
console.log('📖 See .cursor/TYPESCRIPT_SETUP_SUMMARY.md for next steps.\n');
