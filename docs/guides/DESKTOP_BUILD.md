# Desktop App Build Guide

This guide covers building, signing, and distributing the CryptoOrchestrator desktop application.

## Prerequisites

### All Platforms
- Node.js 18+ and npm
- Python 3.11+ (for bundling Python runtime)
- Git

### Windows Code Signing
- Code signing certificate (.pfx file)
- Windows SDK (for signtool.exe)

### macOS Code Signing & Notarization
- Apple Developer Account ($99/year)
- Xcode Command Line Tools
- App-specific password for notarization

### Linux
- No additional requirements (optional: GPG key for package signing)

## Python Runtime Bundling

The desktop app bundles a Python runtime to avoid requiring users to install Python separately.

### Windows
```powershell
.\scripts\bundle_python_runtime.ps1
```

### macOS/Linux
```bash
chmod +x scripts/bundle_python_runtime.sh
./scripts/bundle_python_runtime.sh
```

This creates a `python-runtime/` directory containing:
- Python virtual environment with all dependencies
- `server_fastapi/` directory
- `shared/` directory
- Startup scripts for each platform

## Environment Variables

Create a `.env.build` file (or set environment variables) for code signing:

### Windows
```env
WIN_CERT_PATH=C:\path\to\certificate.pfx
WIN_CERT_FILE=C:\path\to\certificate.pfx
WIN_CERT_PASSWORD=your_certificate_password
```

### macOS
```env
APPLE_ID=your@appleid.com
APPLE_APP_SPECIFIC_PASSWORD=xxxx-xxxx-xxxx-xxxx
APPLE_TEAM_ID=TEAM_ID_HERE
```

### GitHub Releases (for auto-updater)
```env
GITHUB_OWNER=yourusername
GITHUB_REPO=Crypto-Orchestrator
GITHUB_TOKEN=ghp_your_token_here
```

## Building the Desktop App

### Development Build (No Signing)
```bash
npm run build:electron
```

### Production Build (With Signing)

#### Windows
```bash
# Set environment variables first
$env:WIN_CERT_PATH="C:\path\to\certificate.pfx"
$env:WIN_CERT_PASSWORD="password"

npm run build:electron
```

#### macOS
```bash
# Set environment variables first
export APPLE_ID="your@appleid.com"
export APPLE_APP_SPECIFIC_PASSWORD="xxxx-xxxx-xxxx-xxxx"
export APPLE_TEAM_ID="TEAM_ID_HERE"

npm run build:electron
```

#### Linux
```bash
npm run build:electron
```

## Code Signing Setup

### Windows

1. **Obtain a Code Signing Certificate**
   - Purchase from a trusted CA (DigiCert, Sectigo, etc.)
   - Or use a self-signed certificate for testing (not recommended for distribution)

2. **Export Certificate**
   - Export as `.pfx` file with private key
   - Set password protection

3. **Configure electron-builder.json**
   - Set `WIN_CERT_PATH` environment variable
   - Set `WIN_CERT_FILE` to certificate path
   - Set `WIN_CERT_PASSWORD` to certificate password

4. **Build**
   ```powershell
   $env:WIN_CERT_PATH="C:\path\to\certificate.pfx"
   $env:WIN_CERT_PASSWORD="password"
   npm run build:electron
   ```

### macOS

1. **Apple Developer Account**
   - Sign up at https://developer.apple.com
   - Enroll in Apple Developer Program ($99/year)

2. **Create App-Specific Password**
   - Go to https://appleid.apple.com
   - Sign in → App-Specific Passwords
   - Generate password for "CryptoOrchestrator Notarization"

3. **Get Team ID**
   - Go to https://developer.apple.com/account
   - Find your Team ID (10-character string)

4. **Configure Environment Variables**
   ```bash
   export APPLE_ID="your@appleid.com"
   export APPLE_APP_SPECIFIC_PASSWORD="xxxx-xxxx-xxxx-xxxx"
   export APPLE_TEAM_ID="TEAM_ID_HERE"
   ```

5. **Build**
   ```bash
   npm run build:electron
   ```

   The build process will:
   - Sign the app with your Developer ID
   - Notarize with Apple
   - Create a DMG installer

### Linux

Linux code signing is optional but recommended:

1. **Generate GPG Key**
   ```bash
   gpg --gen-key
   ```

2. **Export Public Key**
   ```bash
   gpg --armor --export your@email.com > public.key
   ```

3. **Configure electron-builder.json**
   - Set `linux.sign` to your GPG key ID

## Auto-Updater Configuration

The app uses `electron-updater` to automatically check for and install updates from GitHub Releases.

### Setup

1. **Create GitHub Release**
   - Tag releases: `v1.0.0`, `v1.0.1`, etc.
   - Upload installers: `.exe`, `.dmg`, `.AppImage`, `.deb`

2. **Configure electron-builder.json**
   ```json
   {
     "publish": {
       "provider": "github",
       "owner": "yourusername",
       "repo": "Crypto-Orchestrator",
       "releaseType": "release"
     }
   }
   ```

3. **Set Environment Variables**
   ```env
   GITHUB_OWNER=yourusername
   GITHUB_REPO=Crypto-Orchestrator
   GITHUB_TOKEN=ghp_your_token_here
   ```

### How It Works

- App checks for updates on startup (after 5 seconds)
- Checks every 4 hours automatically
- Downloads updates in background
- Prompts user to restart when ready
- Installs update on next launch

### Manual Update Check

Users can manually check for updates via the app menu or IPC:
```javascript
window.electronAPI.checkForUpdates();
```

## Build Output

### Windows
- `dist-electron/CryptoOrchestrator Setup x.x.x.exe` - NSIS installer
- `dist-electron/CryptoOrchestrator x.x.x.exe` - Portable executable

### macOS
- `dist-electron/CryptoOrchestrator-x.x.x.dmg` - Disk image installer
- `dist-electron/CryptoOrchestrator-x.x.x-mac.zip` - ZIP archive

### Linux
- `dist-electron/CryptoOrchestrator-x.x.x.AppImage` - AppImage
- `dist-electron/cryptoorchestrator_x.x.x_amd64.deb` - Debian package
- `dist-electron/cryptoorchestrator-x.x.x.x86_64.rpm` - RPM package

## Troubleshooting

### Python Runtime Not Found
- Ensure `python-runtime/` directory exists
- Run `npm run bundle:python` before building
- Check `electron-builder.json` includes `python-runtime/` in `extraResources`

### Code Signing Fails (Windows)
- Verify certificate path is correct
- Check certificate password
- Ensure certificate hasn't expired
- Run PowerShell as Administrator

### Notarization Fails (macOS)
- Verify Apple ID credentials
- Check app-specific password is correct
- Ensure Team ID matches your developer account
- Check Apple Developer account status

### Auto-Updater Not Working
- Verify GitHub token has `repo` scope
- Check release tags follow semantic versioning (v1.0.0)
- Ensure installers are uploaded to GitHub Releases
- Check network connectivity

### Build Size Too Large
- Python runtime adds ~200-300MB
- Consider using Python 3.11+ (smaller than 3.12)
- Remove unused dependencies from `requirements.txt`
- Use `--exclude` in electron-builder.json to exclude unnecessary files

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build Desktop App

on:
  release:
    types: [created]

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Bundle Python Runtime
        run: |
          if [ "$RUNNER_OS" == "Windows" ]; then
            powershell -File scripts/bundle_python_runtime.ps1
          else
            bash scripts/bundle_python_runtime.sh
          fi
      
      - name: Install Dependencies
        run: npm ci
      
      - name: Build Frontend
        run: npm run build
      
      - name: Build Electron App
        env:
          WIN_CERT_PATH: ${{ secrets.WIN_CERT_PATH }}
          WIN_CERT_PASSWORD: ${{ secrets.WIN_CERT_PASSWORD }}
          APPLE_ID: ${{ secrets.APPLE_ID }}
          APPLE_APP_SPECIFIC_PASSWORD: ${{ secrets.APPLE_APP_SPECIFIC_PASSWORD }}
          APPLE_TEAM_ID: ${{ secrets.APPLE_TEAM_ID }}
        run: npm run build:electron
      
      - name: Upload Artifacts
        uses: actions/upload-artifact@v3
        with:
          name: desktop-app-${{ matrix.os }}
          path: dist-electron/*
```

## Security Best Practices

1. **Never commit certificates or passwords**
   - Use environment variables or secrets management
   - Add `*.pfx`, `*.p12`, `*.key` to `.gitignore`

2. **Use app-specific passwords**
   - Don't use your main Apple ID password
   - Rotate passwords regularly

3. **Verify signatures**
   - Test signed builds on clean machines
   - Verify signatures before distribution

4. **Keep dependencies updated**
   - Regularly update `electron`, `electron-builder`, `electron-updater`
   - Check for security advisories

5. **Secure auto-updater**
   - Use HTTPS for update server
   - Verify update signatures
   - Use GitHub Releases (automatically signed)

## Additional Resources

- [Electron Builder Documentation](https://www.electron.build/)
- [Electron Updater Documentation](https://www.electron.build/auto-update)
- [Windows Code Signing Guide](https://www.electron.build/code-signing)
- [macOS Notarization Guide](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [GitHub Releases API](https://docs.github.com/en/rest/releases/releases)
