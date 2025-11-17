#!/usr/bin/env python3
"""
GitHub Release Automation Script
Automates version bumps, changelog updates, and GitHub Releases.
Can be used with GitHub MCP or GitHub Actions.
"""

import os
import re
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

import httpx


class GitHubRelease:
    """Automates GitHub releases with version bumps and changelog updates."""
    
    def __init__(self, repo: str, token: Optional[str] = None):
        self.repo = repo
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = f"https://api.github.com/repos/{repo}"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        } if self.token else {}
    
    def get_current_version(self) -> str:
        """Get current version from package.json."""
        package_json = Path("package.json")
        if package_json.exists():
            with open(package_json) as f:
                data = json.load(f)
                return data.get("version", "0.0.0")
        return "0.0.0"
    
    def bump_version(self, bump_type: str = "patch") -> str:
        """Bump version number. Returns new version."""
        current = self.get_current_version()
        major, minor, patch = map(int, current.split("."))
        
        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
        
        new_version = f"{major}.{minor}.{patch}"
        return new_version
    
    def update_version_files(self, new_version: str) -> None:
        """Update version in package.json, pyproject.toml, and CHANGELOG.md."""
        # Update package.json
        package_json = Path("package.json")
        if package_json.exists():
            with open(package_json) as f:
                data = json.load(f)
            data["version"] = new_version
            with open(package_json, "w") as f:
                json.dump(data, f, indent=2)
            print(f"✓ Updated package.json to {new_version}")
        
        # Update pyproject.toml
        pyproject_toml = Path("pyproject.toml")
        if pyproject_toml.exists():
            content = pyproject_toml.read_text()
            content = re.sub(
                r'version\s*=\s*"[\d.]+"',
                f'version = "{new_version}"',
                content
            )
            pyproject_toml.write_text(content)
            print(f"✓ Updated pyproject.toml to {new_version}")
        
        # Update Electron metadata (if in electron-builder.json)
        electron_builder = Path("electron-builder.json")
        if electron_builder.exists():
            with open(electron_builder) as f:
                data = json.load(f)
            if "appId" in data or "productName" in data:
                data.setdefault("extraMetadata", {})["version"] = new_version
                with open(electron_builder, "w") as f:
                    json.dump(data, f, indent=2)
                print(f"✓ Updated electron-builder.json to {new_version}")
    
    def update_changelog(self, new_version: str, release_notes: str) -> None:
        """Update CHANGELOG.md with new release."""
        changelog = Path("CHANGELOG.md")
        
        if not changelog.exists():
            changelog.write_text(f"# Changelog\n\n")
        
        content = changelog.read_text()
        date = datetime.now().strftime("%Y-%m-%d")
        
        new_entry = f"""## [{new_version}] - {date}

### Added
{release_notes}

### Changed
- Automated release via GitHub Actions

### Fixed
- Various bug fixes and improvements

---
"""
        # Insert at the beginning (after title)
        if content.startswith("# Changelog"):
            lines = content.split("\n", 1)
            content = f"{lines[0]}\n\n{new_entry}\n{lines[1] if len(lines) > 1 else ''}"
        else:
            content = f"# Changelog\n\n{new_entry}\n{content}"
        
        changelog.write_text(content)
        print(f"✓ Updated CHANGELOG.md with {new_version}")
    
    def create_github_release(
        self,
        version: str,
        release_notes: str,
        draft: bool = False,
        prerelease: bool = False
    ) -> dict:
        """Create a GitHub release."""
        tag = f"v{version}"
        url = f"{self.base_url}/releases"
        
        payload = {
            "tag_name": tag,
            "name": f"Release {tag}",
            "body": release_notes,
            "draft": draft,
            "prerelease": prerelease
        }
        
        response = httpx.post(url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()
        
        return response.json()
    
    def create_release(
        self,
        bump_type: str = "patch",
        release_notes: Optional[str] = None,
        create_tag: bool = True,
        push_changes: bool = False
    ) -> Tuple[str, dict]:
        """Create a complete release: bump version, update files, create GitHub release."""
        new_version = self.bump_version(bump_type)
        release_notes = release_notes or f"Release {new_version} - See CHANGELOG.md for details"
        
        print(f"Creating release {new_version}...")
        
        # Update version files
        self.update_version_files(new_version)
        self.update_changelog(new_version, release_notes)
        
        # Create git tag
        if create_tag:
            tag = f"v{new_version}"
            subprocess.run(["git", "add", "package.json", "pyproject.toml", "CHANGELOG.md", "electron-builder.json"], check=False)
            subprocess.run(["git", "commit", "-m", f"chore: bump version to {new_version}"], check=False)
            subprocess.run(["git", "tag", "-a", tag, "-m", f"Release {tag}"], check=False)
            
            if push_changes:
                subprocess.run(["git", "push", "origin", "main"], check=False)
                subprocess.run(["git", "push", "origin", tag], check=False)
                print(f"✓ Pushed changes and tag {tag}")
        
        # Create GitHub release
        release = None
        if self.token:
            try:
                release = self.create_github_release(new_version, release_notes)
                print(f"✓ Created GitHub release: {release.get('html_url')}")
            except Exception as e:
                print(f"⚠ Failed to create GitHub release: {e}")
        
        return new_version, release


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automate GitHub releases")
    parser.add_argument("--bump", choices=["major", "minor", "patch"], default="patch")
    parser.add_argument("--notes", help="Release notes")
    parser.add_argument("--repo", help="GitHub repo (owner/repo)", required=True)
    parser.add_argument("--token", help="GitHub token (or use GITHUB_TOKEN env)")
    parser.add_argument("--no-tag", action="store_true", help="Don't create git tag")
    parser.add_argument("--push", action="store_true", help="Push changes to GitHub")
    
    args = parser.parse_args()
    
    release = GitHubRelease(args.repo, args.token)
    version, github_release = release.create_release(
        bump_type=args.bump,
        release_notes=args.notes,
        create_tag=not args.no_tag,
        push_changes=args.push
    )
    
    print(f"\n✅ Release {version} created successfully!")
    if github_release:
        print(f"🔗 {github_release.get('html_url')}")


if __name__ == "__main__":
    main()

