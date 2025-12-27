import { chromium } from '@playwright/test';
import { readFileSync, writeFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '..');

async function convertSvgToPng() {
  const svgPath = join(projectRoot, 'client', 'public', 'favicon.svg');
  const pngPath = join(projectRoot, 'client', 'public', 'favicon.png');
  
  const svgContent = readFileSync(svgPath, 'utf-8');
  
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  // Set viewport to 64x64 for favicon size
  await page.setViewportSize({ width: 64, height: 64 });
  
  // Create data URI from SVG
  const dataUri = `data:image/svg+xml;base64,${Buffer.from(svgContent).toString('base64')}`;
  
  // Load the SVG
  await page.goto(dataUri);
  
  // Wait for it to render
  await page.waitForTimeout(100);
  
  // Take screenshot as PNG
  await page.screenshot({
    path: pngPath,
    type: 'png',
    clip: { x: 0, y: 0, width: 64, height: 64 }
  });
  
  await browser.close();
  console.log(`✅ Favicon converted: ${pngPath}`);
}

convertSvgToPng().catch(console.error);

