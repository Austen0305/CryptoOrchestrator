/**
 * Notarize macOS app for distribution
 * Required for macOS apps distributed outside the App Store
 */

const { notarize } = require('@electron/notarize');

exports.default = async function notarizing(context) {
  const { electronPlatformName, appOutDir } = context;
  
  // Only notarize macOS builds
  if (electronPlatformName !== 'darwin') {
    return;
  }

  // Skip notarization if credentials not provided
  if (!process.env.APPLE_ID || !process.env.APPLE_APP_SPECIFIC_PASSWORD) {
    console.warn('[Notarize] Skipping notarization - credentials not provided');
    return;
  }

  const appName = context.packager.appInfo.productFilename;

  console.log(`[Notarize] Notarizing ${appName}...`);

  try {
    await notarize({
      appBundleId: 'com.cryptoorchestrator.app',
      appPath: `${appOutDir}/${appName}.app`,
      appleId: process.env.APPLE_ID,
      appleIdPassword: process.env.APPLE_APP_SPECIFIC_PASSWORD,
      teamId: process.env.APPLE_TEAM_ID,
    });

    console.log('[Notarize] Notarization successful');
  } catch (error) {
    console.error('[Notarize] Notarization failed:', error);
    throw error;
  }
};
