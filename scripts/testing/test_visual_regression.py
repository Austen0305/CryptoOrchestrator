#!/usr/bin/env python3
"""
Visual Regression Testing
Captures screenshots and compares them to detect visual changes.
"""

import asyncio
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

try:
    from playwright.async_api import async_playwright, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Run: pip install playwright && playwright install")

from PIL import Image, ImageChops, ImageDraw, ImageFont

class VisualRegressionTester:
    """Visual regression testing using screenshot comparison."""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.screenshots_dir = Path("visual_regression")
        self.baseline_dir = self.screenshots_dir / "baseline"
        self.current_dir = self.screenshots_dir / "current"
        self.diff_dir = self.screenshots_dir / "diff"
        
        # Create directories
        for dir_path in [self.baseline_dir, self.current_dir, self.diff_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.test_pages = [
            {"name": "home", "path": "/", "wait_for": "text=Crypto Orchestrator"},
            {"name": "login", "path": "/login", "wait_for": "button:has-text('Login')"},
            {"name": "dashboard", "path": "/dashboard", "auth_required": True},
            {"name": "bots", "path": "/bots", "auth_required": True},
            {"name": "analytics", "path": "/analytics", "auth_required": True},
            {"name": "wallet", "path": "/wallet", "auth_required": True},
        ]
        
        self.results = []
    
    async def capture_screenshot(self, page: Page, name: str, directory: Path) -> Path:
        """Capture a screenshot of the current page."""
        filepath = directory / f"{name}.png"
        await page.screenshot(path=str(filepath), full_page=True)
        return filepath
    
    def compare_images(self, baseline: Path, current: Path, diff_output: Path, 
                      threshold: float = 0.01) -> Dict:
        """Compare two images and generate diff."""
        try:
            img1 = Image.open(baseline).convert('RGB')
            img2 = Image.open(current).convert('RGB')
            
            # Resize if dimensions don't match
            if img1.size != img2.size:
                # Resize to smaller size
                min_width = min(img1.width, img2.width)
                min_height = min(img1.height, img2.height)
                img1 = img1.resize((min_width, min_height))
                img2 = img2.resize((min_width, min_height))
            
            # Calculate difference
            diff = ImageChops.difference(img1, img2)
            
            # Calculate percentage difference
            diff_pixels = sum(sum(pixel) for pixel in diff.getdata())
            total_pixels = img1.width * img1.height * 3  # RGB channels
            diff_percentage = (diff_pixels / total_pixels) * 100
            
            # Generate diff image with highlights
            diff_highlight = img2.copy()
            diff_data = diff.getdata()
            
            for i, pixel in enumerate(diff_data):
                if sum(pixel) > 30:  # Threshold for visible difference
                    x = i % diff.width
                    y = i // diff.width
                    # Highlight in red
                    draw = ImageDraw.Draw(diff_highlight)
                    draw.rectangle([x, y, x+1, y+1], fill=(255, 0, 0))
            
            diff_highlight.save(diff_output)
            
            passed = diff_percentage < threshold
            
            return {
                "baseline": str(baseline),
                "current": str(current),
                "diff": str(diff_output),
                "diff_percentage": round(diff_percentage, 4),
                "threshold": threshold,
                "passed": passed,
                "status": "PASS" if passed else "FAIL"
            }
        
        except Exception as e:
            return {
                "error": str(e),
                "passed": False,
                "status": "ERROR"
            }
    
    async def test_page(self, page: Page, test_config: Dict, mode: str = "compare") -> Dict:
        """Test a single page."""
        name = test_config["name"]
        path = test_config["path"]
        
        print(f"  Testing: {name} ({path})")
        
        try:
            # Navigate to page
            await page.goto(f"{self.base_url}{path}", wait_until="networkidle")
            
            # Wait for specific element if specified
            if "wait_for" in test_config:
                try:
                    await page.wait_for_selector(test_config["wait_for"], timeout=5000)
                except:
                    pass  # Continue even if wait fails
            
            # Additional wait for dynamic content
            await asyncio.sleep(1)
            
            if mode == "baseline":
                # Capture baseline
                screenshot_path = await self.capture_screenshot(page, name, self.baseline_dir)
                return {
                    "name": name,
                    "path": path,
                    "mode": "baseline",
                    "screenshot": str(screenshot_path),
                    "status": "CAPTURED"
                }
            
            else:  # compare mode
                # Capture current
                current_path = await self.capture_screenshot(page, name, self.current_dir)
                
                # Check if baseline exists
                baseline_path = self.baseline_dir / f"{name}.png"
                if not baseline_path.exists():
                    return {
                        "name": name,
                        "path": path,
                        "mode": "compare",
                        "status": "NO_BASELINE",
                        "message": "No baseline screenshot found. Run in baseline mode first."
                    }
                
                # Compare with baseline
                diff_path = self.diff_dir / f"{name}_diff.png"
                comparison = self.compare_images(baseline_path, current_path, diff_path)
                
                return {
                    "name": name,
                    "path": path,
                    "mode": "compare",
                    **comparison
                }
        
        except Exception as e:
            return {
                "name": name,
                "path": path,
                "error": str(e),
                "status": "ERROR"
            }
    
    async def run_tests(self, mode: str = "compare", headless: bool = True):
        """Run all visual regression tests."""
        if not PLAYWRIGHT_AVAILABLE:
            print("❌ Playwright is not installed")
            return
        
        print(f"🎨 Starting Visual Regression Testing")
        print(f"Mode: {mode}")
        print(f"Base URL: {self.base_url}")
        print("-" * 80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()
            
            for test_config in self.test_pages:
                # Skip auth-required pages for now (would need login implementation)
                if test_config.get("auth_required"):
                    print(f"  Skipping: {test_config['name']} (auth required)")
                    continue
                
                result = await self.test_page(page, test_config, mode)
                self.results.append(result)
            
            await browser.close()
        
        self.print_summary()
        self.save_report()
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 80)
        print("VISUAL REGRESSION TEST SUMMARY")
        print("=" * 80)
        
        for result in self.results:
            status_icon = {
                "PASS": "✅",
                "FAIL": "❌",
                "ERROR": "⚠️",
                "CAPTURED": "📸",
                "NO_BASELINE": "⚠️"
            }.get(result["status"], "❓")
            
            print(f"{status_icon} {result['name']}: {result['status']}")
            
            if result.get("diff_percentage") is not None:
                print(f"   Difference: {result['diff_percentage']:.4f}%")
            
            if result.get("error"):
                print(f"   Error: {result['error']}")
            
            if result.get("message"):
                print(f"   {result['message']}")
        
        if any(r["mode"] == "compare" for r in self.results):
            passed = sum(1 for r in self.results if r.get("passed"))
            failed = sum(1 for r in self.results if r.get("passed") == False and r["status"] != "NO_BASELINE")
            
            print(f"\nTests Passed: {passed}")
            print(f"Tests Failed: {failed}")
        
        print("=" * 80)
    
    def save_report(self):
        """Save test report to JSON."""
        report_file = self.screenshots_dir / "report.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "results": self.results
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved: {report_file}")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Visual regression testing")
    parser.add_argument("--url", default="http://localhost:3000", help="Base URL to test")
    parser.add_argument("--mode", choices=["baseline", "compare"], default="compare",
                       help="baseline: capture reference screenshots, compare: test against baseline")
    parser.add_argument("--headed", action="store_true", help="Run browser in headed mode")
    
    args = parser.parse_args()
    
    tester = VisualRegressionTester(base_url=args.url)
    asyncio.run(tester.run_tests(mode=args.mode, headless=not args.headed))

if __name__ == "__main__":
    main()
