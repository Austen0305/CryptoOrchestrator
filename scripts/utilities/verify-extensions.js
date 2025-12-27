#!/usr/bin/env node

/**
 * Extension Verification Script
 * 
 * Checks which VS Code/Cursor extensions are installed by phase
 * and reports missing extensions per phase.
 * 
 * Usage: node scripts/utilities/verify-extensions.js
 */

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Extension phases configuration
const PHASES = {
  phase1: {
    name: 'Phase 1: Essential Code Quality & Core Development Tools',
    priority: 'CRITICAL',
    // Note: 16 extensions (added Black Formatter)
    extensions: [
      { id: 'usernamehw.errorlens', name: 'Error Lens' },
      { id: 'dbaeumer.vscode-eslint', name: 'ESLint' },
      { id: 'esbenp.prettier-vscode', name: 'Prettier' },
      { id: 'sonarsource.sonarlint-vscode', name: 'SonarLint' },
      { id: 'snyk.snyk-vscode', name: 'Snyk' },
      { id: 'ms-python.python', name: 'Python' },
      { id: 'ms-python.vscode-pylance', name: 'Pylance' },
      { id: 'ms-python.black-formatter', name: 'Black Formatter' },
      { id: 'njpwerner.autodocstring', name: 'Python Docstring Generator' },
      { id: 'njqdev.vscode-python-typehint', name: 'Python Type Hint' },
      { id: 'littlefoxteam.vscode-python-test-adapter', name: 'Python Test Explorer' },
      { id: 'eamodio.gitlens', name: 'GitLens' },
      { id: 'mhutchie.vscode-git-graph', name: 'Git Graph' },
      { id: 'donjayamanne.githistory', name: 'Git History' },
      { id: 'github.vscode-pull-request-github', name: 'GitHub Pull Requests and Issues' },
      { id: 'mikestead.dotenv', name: 'DotEnv' }
    ]
  },
  phase2: {
    name: 'Phase 2: Database, API Testing & Testing Tools',
    priority: 'HIGH',
    extensions: [
      { id: 'ms-ossdata.vscode-postgresql', name: 'PostgreSQL' },
      { id: 'qwtel.sqlite-viewer', name: 'SQLite Viewer' },
      { id: 'yy0931.sqlite3-editor', name: 'SQLite3 Editor' },
      { id: 'humao.rest-client', name: 'REST Client' },
      { id: 'rapidapi.rapidapi-client', name: 'RapidAPI Client' },
      { id: 'ryanluker.vscode-coverage-gutters', name: 'Coverage Gutters' },
      { id: 'firsttris.vscode-jest-runner', name: 'Jest Runner' },
      { id: 'redhat.vscode-yaml', name: 'YAML Language Support' },
      { id: 'daniel-hillmann.vscode-yaml-json', name: 'YAML ❤️ JSON' }
    ]
  },
  phase3: {
    name: 'Phase 3: Documentation, Markdown & Productivity Tools',
    priority: 'MEDIUM',
    extensions: [
      { id: 'yzhang.markdown-all-in-one', name: 'Markdown All in One' },
      { id: 'shd101wyy.markdown-preview-enhanced', name: 'Markdown Preview Enhanced' },
      { id: 'davidanson.vscode-markdownlint', name: 'markdownlint' },
      { id: 'hediet.vscode-drawio', name: 'Draw.io Integration' },
      { id: 'mushan.vscode-paste-image', name: 'Paste Image' },
      { id: 'jebbs.plantuml', name: 'PlantUML' },
      { id: 'aaron-bond.better-comments', name: 'Better Comments' },
      { id: 'christian-kohler.path-intellisense', name: 'Path Intellisense' },
      { id: 'wix.vscode-import-cost', name: 'Import Cost' },
      { id: 'gruntfuggly.todo-tree', name: 'Todo Tree' },
      { id: 'streetsidesoftware.code-spell-checker', name: 'Code Spell Checker' },
      { id: 'alefragnani.project-manager', name: 'Project Manager' }
    ]
  },
  phase4: {
    name: 'Phase 4: Specialized Tools & Advanced Features',
    priority: 'MEDIUM-LOW',
    extensions: [
      { id: 'ms-azuretools.vscode-docker', name: 'Docker' },
      { id: 'ms-kubernetes-tools.vscode-kubernetes-tools', name: 'Kubernetes Tools' },
      { id: 'ms-vscode-remote.remote-containers', name: 'Dev Containers' },
      { id: 'ritwickdey.liveserver', name: 'Live Server' },
      { id: 'ms-vscode.live-server', name: 'Live Preview' },
      { id: 'formulahendry.auto-rename-tag', name: 'Auto Rename Tag' },
      { id: 'dsznajder.es7-react-js-snippets', name: 'ES7+ React/Redux/React-Native snippets' },
      { id: 'oderwat.indent-rainbow', name: 'Indent Rainbow' },
      { id: 'dotenv.dotenv-vscode', name: 'Dotenv Official' },
      { id: 'kisstkondoros.codemetrics', name: 'CodeMetrics' },
      { id: 'brobeson.vscode-lizard', name: 'VS Code Lizard' },
      { id: 'wakatime.vscode-wakatime', name: 'WakaTime' },
      { id: 'mbparvezme.pomodoro-vscode-extension', name: 'Pomodoro for Dev' },
      { id: 'alefragnani.bookmarks', name: 'Bookmarks' },
      { id: 'msjsdiag.vscode-react-native', name: 'React Native Tools' },
      { id: 'expo.vscode-expo-tools', name: 'Expo Tools' },
      { id: 'electron.electron-snippets', name: 'Electron Snippets' }
    ]
  }
};

/**
 * Get list of installed extensions
 * @returns {string[]} List of installed extension IDs
 */
function getInstalledExtensions() {
  try {
    // Try Cursor CLI first (primary for this project)
    const output = execSync('cursor --list-extensions', { encoding: 'utf-8' });
    return output.trim().split('\n').filter(Boolean);
  } catch (cursorError) {
    try {
      // Fallback to VS Code CLI if Cursor not available
      const output = execSync('code --list-extensions', { encoding: 'utf-8' });
      return output.trim().split('\n').filter(Boolean);
    } catch (error) {
      // If neither command works, return empty array and show warning
      console.warn('⚠️  Warning: Could not list extensions. Make sure Cursor or VS Code is installed and in PATH.');
      console.warn('   Try: cursor --list-extensions (Cursor) or code --list-extensions (VS Code)');
      console.warn('   Continuing with empty extension list for verification...\n');
      return [];
    }
  }
}

/**
 * Check extension installation status
 * @param {string[]} installedExtensions - List of installed extension IDs
 * @param {Object} phase - Phase configuration
 * @returns {Object} Installation status
 */
function checkPhase(installedExtensions, phase) {
  const installed = [];
  const missing = [];

  phase.extensions.forEach(ext => {
    if (installedExtensions.includes(ext.id)) {
      installed.push(ext);
    } else {
      missing.push(ext);
    }
  });

  return {
    installed,
    missing,
    total: phase.extensions.length,
    installedCount: installed.length,
    missingCount: missing.length,
    completionPercent: Math.round((installed.length / phase.extensions.length) * 100)
  };
}

/**
 * Generate installation commands for missing extensions
 * @param {Object[]} missingExtensions - List of missing extensions
 * @returns {string[]} Installation commands
 */
function generateInstallCommands(missingExtensions) {
  return missingExtensions.map(ext => {
    return `code --install-extension ${ext.id}`;
  });
}

/**
 * Print phase report
 * @param {string} phaseKey - Phase key
 * @param {Object} phase - Phase configuration
 * @param {Object} status - Installation status
 */
function printPhaseReport(phaseKey, phase, status) {
  const statusIcon = status.completionPercent === 100 ? '✅' : status.missingCount > 0 ? '⚠️' : '❌';
  
  console.log(`\n${statusIcon} ${phase.name} (${phase.priority})`);
  console.log(`   Progress: ${status.installedCount}/${status.total} (${status.completionPercent}%)`);
  
  if (status.installed.length > 0) {
    console.log(`\n   ✅ Installed (${status.installed.length}):`);
    status.installed.forEach(ext => {
      console.log(`      - ${ext.name}`);
    });
  }
  
  if (status.missing.length > 0) {
    console.log(`\n   ❌ Missing (${status.missing.length}):`);
    status.missing.forEach(ext => {
      console.log(`      - ${ext.name} (${ext.id})`);
    });
    
    console.log(`\n   📦 Installation commands:`);
    const commands = generateInstallCommands(status.missing);
    commands.forEach(cmd => {
      console.log(`      ${cmd}`);
    });
  }
}

/**
 * Generate summary report
 * @param {Object} allStatuses - All phase statuses
 */
function printSummary(allStatuses) {
  const totalExtensions = Object.values(PHASES).reduce((sum, phase) => sum + phase.extensions.length, 0);
  const totalInstalled = Object.values(allStatuses).reduce((sum, status) => sum + status.installedCount, 0);
  const overallCompletion = Math.round((totalInstalled / totalExtensions) * 100);

  console.log('\n' + '='.repeat(60));
  console.log('📊 SUMMARY REPORT');
  console.log('='.repeat(60));
  console.log(`Total Extensions: ${totalExtensions}`);
  console.log(`Installed: ${totalInstalled}`);
  console.log(`Missing: ${totalExtensions - totalInstalled}`);
  console.log(`Overall Completion: ${overallCompletion}%`);
  
  console.log('\nPhase Breakdown:');
  Object.keys(PHASES).forEach(phaseKey => {
    const status = allStatuses[phaseKey];
    const icon = status.completionPercent === 100 ? '✅' : '⚠️';
    console.log(`  ${icon} ${PHASES[phaseKey].name}: ${status.installedCount}/${status.total} (${status.completionPercent}%)`);
  });
}

/**
 * Main function
 */
function main() {
  console.log('🔍 Checking VS Code/Cursor Extensions...');
  console.log('='.repeat(60));

  const installedExtensions = getInstalledExtensions();
  console.log(`Found ${installedExtensions.length} installed extensions\n`);

  const allStatuses = {};

  // Check each phase
  Object.keys(PHASES).forEach(phaseKey => {
    const phase = PHASES[phaseKey];
    const status = checkPhase(installedExtensions, phase);
    allStatuses[phaseKey] = status;
    printPhaseReport(phaseKey, phase, status);
  });

  // Print summary
  printSummary(allStatuses);

  // Check if extensions.json exists
  const projectRoot = path.resolve(__dirname, '../..');
  const extensionsJsonPath = path.join(projectRoot, '.vscode', 'extensions.json');
  if (fs.existsSync(extensionsJsonPath)) {
    console.log('\n✅ .vscode/extensions.json found');
    console.log('   Extensions are configured in workspace recommendations');
  } else {
    console.log('\n⚠️  .vscode/extensions.json not found');
    console.log('   Consider adding extensions.json to workspace');
  }

  // Check if settings.json exists
  const settingsJsonPath = path.join(projectRoot, '.vscode', 'settings.json');
  if (fs.existsSync(settingsJsonPath)) {
    console.log('✅ .vscode/settings.json found');
    console.log('   Extension configurations are available');
  } else {
    console.log('⚠️  .vscode/settings.json not found');
    console.log('   Consider adding settings.json for extension configuration');
  }

  console.log('\n' + '='.repeat(60));
  console.log('✨ Verification complete!');
  console.log('='.repeat(60));
}

// Run main function
main();
