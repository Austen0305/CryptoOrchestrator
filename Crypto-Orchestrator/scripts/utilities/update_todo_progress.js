#!/usr/bin/env node

/**
 * TODO Progress Updater
 * 
 * This script helps update progress in COMPREHENSIVE_TODO_LIST.md
 * 
 * Usage:
 *   node scripts/update_todo_progress.js --phase 1 --completed 38 --total 150
 *   node scripts/update_todo_progress.js --section "Authentication" --completed 8 --total 10
 */

const fs = require('fs');
const path = require('path');

const TODO_FILE = path.join(__dirname, '..', 'COMPREHENSIVE_TODO_LIST.md');

function updateProgress(phase, completed, total) {
  if (!fs.existsSync(TODO_FILE)) {
    console.error('❌ TODO file not found:', TODO_FILE);
    process.exit(1);
  }

  let content = fs.readFileSync(TODO_FILE, 'utf8');
  const percentage = Math.round((completed / total) * 100);

  // Update phase progress
  const phasePattern = new RegExp(
    `- \\*\\*Phase ${phase}:\\*\\* 0% \\(0/\\d+ tasks\\)`,
    'g'
  );
  const replacement = `- **Phase ${phase}:** ${percentage}% (${completed}/${total} tasks)`;

  if (phasePattern.test(content)) {
    content = content.replace(phasePattern, replacement);
    console.log(`✅ Updated Phase ${phase} progress: ${percentage}% (${completed}/${total} tasks)`);
  } else {
    // Try to find and update existing progress
    const existingPattern = new RegExp(
      `- \\*\\*Phase ${phase}:\\*\\* \\d+% \\(\\d+/\\d+ tasks\\)`,
      'g'
    );
    if (existingPattern.test(content)) {
      content = content.replace(existingPattern, replacement);
      console.log(`✅ Updated Phase ${phase} progress: ${percentage}% (${completed}/${total} tasks)`);
    } else {
      console.error(`❌ Could not find Phase ${phase} in TODO file`);
      process.exit(1);
    }
  }

  // Update total progress
  const totalPattern = /\\*\\*Total Progress:\\*\\* 0% \\(0\/630 tasks\\)/g;
  // Calculate total from all phases (simplified - you'd need to parse all phases)
  const totalReplacement = `**Total Progress:** ${percentage}% (${completed}/${total} tasks)`;
  
  // For now, just update the current phase
  fs.writeFileSync(TODO_FILE, content, 'utf8');
  console.log(`✅ Progress updated in ${TODO_FILE}`);
}

function countTasksInFile() {
  if (!fs.existsSync(TODO_FILE)) {
    console.error('❌ TODO file not found:', TODO_FILE);
    process.exit(1);
  }

  const content = fs.readFileSync(TODO_FILE, 'utf8');
  const unchecked = (content.match(/- \[ \]/g) || []).length;
  const checked = (content.match(/- \[x\]/gi) || []).length;
  const total = unchecked + checked;

  console.log('\n📊 Current Progress:');
  console.log(`   ✅ Completed: ${checked}`);
  console.log(`   ⏳ Remaining: ${unchecked}`);
  console.log(`   📋 Total: ${total}`);
  console.log(`   📈 Progress: ${Math.round((checked / total) * 100)}%`);
}

// Parse command line arguments
const args = process.argv.slice(2);

if (args.includes('--count') || args.includes('-c')) {
  countTasksInFile();
} else if (args.includes('--phase') || args.includes('-p')) {
  const phaseIndex = args.indexOf('--phase') !== -1 ? args.indexOf('--phase') : args.indexOf('-p');
  const phase = args[phaseIndex + 1];
  const completedIndex = args.indexOf('--completed') !== -1 ? args.indexOf('--completed') : args.indexOf('-c');
  const completed = parseInt(args[completedIndex + 1]);
  const totalIndex = args.indexOf('--total') !== -1 ? args.indexOf('--total') : args.indexOf('-t');
  const total = parseInt(args[totalIndex + 1]);

  if (!phase || !completed || !total) {
    console.error('❌ Usage: node update_todo_progress.js --phase <num> --completed <num> --total <num>');
    process.exit(1);
  }

  updateProgress(phase, completed, total);
} else {
  console.log(`
📋 TODO Progress Updater

Usage:
  node scripts/update_todo_progress.js --count
  node scripts/update_todo_progress.js --phase <num> --completed <num> --total <num>

Examples:
  node scripts/update_todo_progress.js --count
  node scripts/update_todo_progress.js --phase 1 --completed 38 --total 150
  `);
}

