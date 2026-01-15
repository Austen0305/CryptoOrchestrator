const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');

const projectRoot = __dirname;
const workspaceRoot = path.resolve(projectRoot, '../');

/**
 * Metro configuration for Expo
 * https://docs.expo.dev/guides/customizing-metro/
 */
const config = getDefaultConfig(__dirname);

// Watch the shared directory
config.watchFolders = [path.resolve(workspaceRoot, 'shared')];

// Ensure node_modules are resolved correctly
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, 'node_modules'),
  path.resolve(workspaceRoot, 'node_modules'),
];

module.exports = config;
