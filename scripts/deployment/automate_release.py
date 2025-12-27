"""
Automated Release Notes and Version Bump Script
Generates release notes from commits and bumps versions across all files
"""
import re
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
import sys

def get_git_commits(since_tag: str = None) -> List[Dict[str, str]]:
    """Get git commits since last tag or since_tag"""
    if since_tag:
        cmd = ["git", "log", f"{since_tag}..HEAD", "--pretty=format:%H|%s|%an|%ad", "--date=short"]
    else:
        cmd = ["git", "log", "--pretty=format:%H|%s|%an|%ad", "--date=short", "-50"]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    commits = []
    
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        parts = line.split('|', 3)
        if len(parts) >= 4:
            commits.append({
                "hash": parts[0],
                "message": parts[1],
                "author": parts[2],
                "date": parts[3]
            })
    
    return commits


def categorize_commits(commits: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    """Categorize commits by type (feat, fix, perf, security, etc.)"""
    categories = {
        "features": [],
        "fixes": [],
        "performance": [],
        "security": [],
        "documentation": [],
        "refactor": [],
        "chore": [],
        "other": []
    }
    
    for commit in commits:
        message = commit["message"].lower()
        if message.startswith("feat:") or message.startswith("feature:"):
            categories["features"].append(commit)
        elif message.startswith("fix:") or message.startswith("bugfix:"):
            categories["fixes"].append(commit)
        elif message.startswith("perf:") or message.startswith("performance:"):
            categories["performance"].append(commit)
        elif message.startswith("security:") or message.startswith("sec:"):
            categories["security"].append(commit)
        elif message.startswith("docs:") or message.startswith("documentation:"):
            categories["documentation"].append(commit)
        elif message.startswith("refactor:"):
            categories["refactor"].append(commit)
        elif message.startswith("chore:") or message.startswith("ci:"):
            categories["chore"].append(commit)
        else:
            categories["other"].append(commit)
    
    return categories


def get_current_version() -> str:
    """Get current version from package.json"""
    package_json = Path("package.json")
    if package_json.exists():
        data = json.loads(package_json.read_text())
        return data.get("version", "1.0.0")
    return "1.0.0"


def bump_version(version: str, bump_type: str = "patch") -> str:
    """Bump version number"""
    parts = version.lstrip('v').split('.')
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    return f"{major}.{minor}.{patch}"


def update_package_json(version: str) -> None:
    """Update version in package.json"""
    package_json = Path("package.json")
    if package_json.exists():
        data = json.loads(package_json.read_text())
        data["version"] = version
        package_json.write_text(json.dumps(data, indent=2) + "\n")
        print(f"Updated package.json to version {version}")


def update_pyproject_toml(version: str) -> None:
    """Update version in pyproject.toml"""
    pyproject_toml = Path("pyproject.toml")
    if pyproject_toml.exists():
        content = pyproject_toml.read_text()
        # Update version if it exists
        content = re.sub(
            r'^version\s*=\s*["\']([^"\']+)["\']',
            f'version = "{version}"',
            content,
            flags=re.MULTILINE
        )
        pyproject_toml.write_text(content)
        print(f"Updated pyproject.toml to version {version}")


def update_electron_version(version: str) -> None:
    """Update version in Electron metadata"""
    electron_builder_json = Path("electron-builder.json")
    if electron_builder_json.exists():
        data = json.loads(electron_builder_json.read_text())
        data["appId"] = data.get("appId", "com.cryptoorchestrator.app")
        if "version" not in data:
            data["version"] = version
        else:
            data["version"] = version
        electron_builder_json.write_text(json.dumps(data, indent=2) + "\n")
        print(f"Updated electron-builder.json to version {version}")


def generate_release_notes(categories: Dict[str, List[Dict[str, str]]], version: str) -> str:
    """Generate release notes from categorized commits"""
    notes = [f"# Release {version}", "", f"**Release Date**: {datetime.now().strftime('%Y-%m-%d')}", ""]
    
    if categories["features"]:
        notes.append("## ✨ Features")
        for commit in categories["features"]:
            message = commit["message"].split(":", 1)[1].strip() if ":" in commit["message"] else commit["message"]
            notes.append(f"- {message}")
        notes.append("")
    
    if categories["fixes"]:
        notes.append("## 🐛 Bug Fixes")
        for commit in categories["fixes"]:
            message = commit["message"].split(":", 1)[1].strip() if ":" in commit["message"] else commit["message"]
            notes.append(f"- {message}")
        notes.append("")
    
    if categories["performance"]:
        notes.append("## ⚡ Performance")
        for commit in categories["performance"]:
            message = commit["message"].split(":", 1)[1].strip() if ":" in commit["message"] else commit["message"]
            notes.append(f"- {message}")
        notes.append("")
    
    if categories["security"]:
        notes.append("## 🔒 Security")
        for commit in categories["security"]:
            message = commit["message"].split(":", 1)[1].strip() if ":" in commit["message"] else commit["message"]
            notes.append(f"- {message}")
        notes.append("")
    
    if categories["refactor"]:
        notes.append("## ♻️ Refactoring")
        for commit in categories["refactor"]:
            message = commit["message"].split(":", 1)[1].strip() if ":" in commit["message"] else commit["message"]
            notes.append(f"- {message}")
        notes.append("")
    
    if categories["documentation"]:
        notes.append("## 📚 Documentation")
        for commit in categories["documentation"]:
            message = commit["message"].split(":", 1)[1].strip() if ":" in commit["message"] else commit["message"]
            notes.append(f"- {message}")
        notes.append("")
    
    if categories["chore"]:
        notes.append("## 🔧 Chores")
        for commit in categories["chore"][:10]:  # Limit to 10 most recent
            message = commit["message"].split(":", 1)[1].strip() if ":" in commit["message"] else commit["message"]
            notes.append(f"- {message}")
        notes.append("")
    
    return "\n".join(notes)


def update_changelog(release_notes: str, version: str) -> None:
    """Update CHANGELOG.md with new release notes"""
    changelog = Path("CHANGELOG.md")
    
    if changelog.exists():
        content = changelog.read_text()
    else:
        content = "# Changelog\n\n"
    
    # Insert new release notes at the top
    new_content = f"{release_notes}\n\n---\n\n{content.split('---', 1)[-1] if '---' in content else content}"
    changelog.write_text(new_content)
    print(f"Updated CHANGELOG.md with release {version}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Automate release notes and version bumps")
    parser.add_argument("--bump", choices=["major", "minor", "patch"], default="patch", help="Version bump type")
    parser.add_argument("--since", help="Git tag to get commits since")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually update files")
    parser.add_argument("--version", help="Specific version to use (overrides bump)")
    
    args = parser.parse_args()
    
    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    
    # Determine new version
    if args.version:
        new_version = args.version.lstrip('v')
    else:
        new_version = bump_version(current_version, args.bump)
    
    print(f"New version: {new_version}")
    
    # Get commits
    commits = get_git_commits(args.since)
    print(f"Found {len(commits)} commits")
    
    # Categorize commits
    categories = categorize_commits(commits)
    
    # Generate release notes
    release_notes = generate_release_notes(categories, new_version)
    
    if args.dry_run:
        print("\n" + "=" * 80)
        print("DRY RUN - Release Notes:")
        print("=" * 80)
        print(release_notes)
        print("=" * 80)
        print("\nFiles that would be updated:")
        print("- package.json")
        print("- pyproject.toml")
        print("- electron-builder.json")
        print("- CHANGELOG.md")
    else:
        # Update version files
        update_package_json(new_version)
        update_pyproject_toml(new_version)
        update_electron_version(new_version)
        
        # Update changelog
        update_changelog(release_notes, new_version)
        
        print(f"\n✅ Release {new_version} prepared!")
        print("\nNext steps:")
        print(f"1. Review CHANGELOG.md")
        print(f"2. Commit changes: git add -A && git commit -m 'chore: bump version to {new_version}'")
        print(f"3. Create tag: git tag -a v{new_version} -m 'Release {new_version}'")
        print(f"4. Push: git push origin main --tags")


if __name__ == "__main__":
    main()

