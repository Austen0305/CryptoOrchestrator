/**
 * Post-pack script for Electron Builder
 * Performs additional setup after packaging
 */

const fs = require('fs');
const path = require('path');

exports.default = async function(context) {
  const { appOutDir, electronPlatformName } = context;
  
  console.log('[AfterPack] Running post-pack setup...');
  console.log(`[AfterPack] Platform: ${electronPlatformName}`);
  console.log(`[AfterPack] Output directory: ${appOutDir}`);

  // Verify Python runtime was bundled
  const pythonRuntimePath = path.join(appOutDir, '..', '..', 'python-runtime');
  if (fs.existsSync(pythonRuntimePath)) {
    console.log('[AfterPack] Python runtime found in resources');
  } else {
    console.warn('[AfterPack] Python runtime not found - app may not work correctly');
  }

  // Create version info file
  const versionInfo = {
    version: context.packager.appInfo.version,
    buildDate: new Date().toISOString(),
    platform: electronPlatformName,
    electronVersion: process.versions.electron,
    nodeVersion: process.versions.node,
  };

  const versionInfoPath = path.join(appOutDir, 'version-info.json');
  fs.writeFileSync(versionInfoPath, JSON.stringify(versionInfo, null, 2));
  console.log('[AfterPack] Version info file created');

  console.log('[AfterPack] Post-pack setup complete');
};
