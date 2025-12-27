#!/usr/bin/env python3
"""
Release Automation Script
Automates version bumps and changelog generation from conventional commits.
Updates: CHANGELOG.md, package.json, pyproject.toml, and Electron metadata.
"""

import re
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class Commit:
    """Represents a conventional commit."""
    type: str
    scope: Optional[str]
    description: str
    body: Optional[str]
    breaking: bool
    hash: str


class ReleaseAutomation:
    """Handles release automation tasks."""
    
    def __init__(self, version: str, dry_run: bool = False):
        self.version = version
        self.dry_run = dry_run
        self.changelog_path = PROJECT_ROOT / "CHANGELOG.md"
        self.package_json_path = PROJECT_ROOT / "package.json"
        self.pyproject_toml_path = PROJECT_ROOT / "pyproject.toml"
        
    def parse_commits(self, from_tag: Optional[str] = None) -> List[Commit]:
        """Parse conventional commits since the last tag."""
        try:
            # Get commits since last tag
            if from_tag:
                cmd = ["git", "log", f"{from_tag}..HEAD", "--pretty=format:%H|%s|%b"]
            else:
                cmd = ["git", "log", "--pretty=format:%H|%s|%b", "-50"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            commits = []
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|', 2)
                if len(parts) < 2:
                    continue
                
                hash_part = parts[0]
                subject = parts[1]
                body = parts[2] if len(parts) > 2 else ""
                
                # Parse conventional commit format: type(scope): description
                match = re.match(r'^(\w+)(?:\(([^)]+)\))?(!)?:\s*(.+)$', subject)
                if not match:
                    continue
                
                commit_type, scope, breaking_marker, description = match.groups()
                breaking = breaking_marker == '!'
                
                # Check for BREAKING CHANGE in body
                if 'BREAKING CHANGE' in body or 'BREAKING:' in body:
                    breaking = True
                
                commits.append(Commit(
                    type=commit_type,
                    scope=scope,
                    description=description,
                    body=body if body else None,
                    breaking=breaking,
                    hash=hash_part[:7]
                ))
            
            return commits
        except subprocess.CalledProcessError as e:
            print(f"Error parsing commits: {e}", file=sys.stderr)
            return []
    
    def categorize_commits(self, commits: List[Commit]) -> Dict[str, List[Commit]]:
        """Categorize commits by type."""
        categories = {
            'features': [],
            'fixes': [],
            'performance': [],
            'security': [],
            'breaking': [],
            'other': []
        }
        
        type_mapping = {
            'feat': 'features',
            'fix': 'fixes',
            'perf': 'performance',
            'security': 'security',
            'chore': 'other',
            'refactor': 'other',
            'docs': 'other',
            'test': 'other',
            'ci': 'other',
            'build': 'other'
        }
        
        for commit in commits:
            if commit.breaking:
                categories['breaking'].append(commit)
            else:
                category = type_mapping.get(commit.type, 'other')
                categories[category].append(commit)
        
        return categories
    
    def generate_changelog_entry(self, categories: Dict[str, List[Commit]]) -> str:
        """Generate changelog entry from categorized commits."""
        lines = [f"## [{self.version}] - {datetime.now().strftime('%Y-%m-%d')}", ""]
        
        # Breaking changes first
        if categories['breaking']:
            lines.append("### 🚨 Breaking Changes")
            lines.append("")
            for commit in categories['breaking']:
                scope_text = f"**{commit.scope}**: " if commit.scope else ""
                lines.append(f"- {scope_text}{commit.description} ({commit.hash})")
            lines.append("")
        
        # Features
        if categories['features']:
            lines.append("### ✨ Features")
            lines.append("")
            for commit in categories['features']:
                scope_text = f"**{commit.scope}**: " if commit.scope else ""
                lines.append(f"- {scope_text}{commit.description} ({commit.hash})")
            lines.append("")
        
        # Bug fixes
        if categories['fixes']:
            lines.append("### 🐛 Bug Fixes")
            lines.append("")
            for commit in categories['fixes']:
                scope_text = f"**{commit.scope}**: " if commit.scope else ""
                lines.append(f"- {scope_text}{commit.description} ({commit.hash})")
            lines.append("")
        
        # Performance improvements
        if categories['performance']:
            lines.append("### ⚡ Performance Improvements")
            lines.append("")
            for commit in categories['performance']:
                scope_text = f"**{commit.scope}**: " if commit.scope else ""
                lines.append(f"- {scope_text}{commit.description} ({commit.hash})")
            lines.append("")
        
        # Security updates
        if categories['security']:
            lines.append("### 🔒 Security Updates")
            lines.append("")
            for commit in categories['security']:
                scope_text = f"**{commit.scope}**: " if commit.scope else ""
                lines.append(f"- {scope_text}{commit.description} ({commit.hash})")
            lines.append("")
        
        # Other changes
        if categories['other']:
            lines.append("### 📝 Other Changes")
            lines.append("")
            for commit in categories['other']:
                scope_text = f"**{commit.scope}**: " if commit.scope else ""
                lines.append(f"- {scope_text}{commit.description} ({commit.hash})")
            lines.append("")
        
        return "\n".join(lines)
    
    def update_changelog(self, new_entry: str):
        """Update CHANGELOG.md with new release entry."""
        if not self.changelog_path.exists():
            # Create new changelog
            content = f"# Changelog\n\n{new_entry}\n"
        else:
            content = self.changelog_path.read_text(encoding='utf-8')
            
            # Find [Unreleased] section and replace with new version
            unreleased_pattern = r'## \[Unreleased\].*?(?=## \[|\Z)'
            if re.search(unreleased_pattern, content, re.DOTALL):
                # Replace [Unreleased] with new version
                content = re.sub(
                    r'## \[Unreleased\].*?(?=## \[|\Z)',
                    new_entry + '\n',
                    content,
                    flags=re.DOTALL
                )
            else:
                # Insert at the beginning after title
                if content.startswith('# Changelog'):
                    content = content.replace('# Changelog', f'# Changelog\n\n{new_entry}', 1)
                else:
                    content = f"# Changelog\n\n{new_entry}\n\n{content}"
        
        if not self.dry_run:
            self.changelog_path.write_text(content, encoding='utf-8')
        else:
            print(f"[DRY RUN] Would update CHANGELOG.md:\n{new_entry}")
    
    def update_package_json(self):
        """Update version in package.json."""
        if not self.package_json_path.exists():
            print(f"Warning: {self.package_json_path} not found", file=sys.stderr)
            return
        
        content = json.loads(self.package_json_path.read_text(encoding='utf-8'))
        old_version = content.get('version', '0.0.0')
        content['version'] = self.version
        
        if not self.dry_run:
            self.package_json_path.write_text(
                json.dumps(content, indent=2, ensure_ascii=False) + '\n',
                encoding='utf-8'
            )
            print(f"Updated package.json: {old_version} -> {self.version}")
        else:
            print(f"[DRY RUN] Would update package.json: {old_version} -> {self.version}")
    
    def update_pyproject_toml(self):
        """Update version in pyproject.toml."""
        if not self.pyproject_toml_path.exists():
            print(f"Warning: {self.pyproject_toml_path} not found", file=sys.stderr)
            return
        
        content = self.pyproject_toml_path.read_text(encoding='utf-8')
        
        # Check if [project] section exists
        if '[project]' in content:
            # Update existing version
            pattern = r'(\[project\]\s+.*?version\s*=\s*")[^"]+(")'
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, rf'\1{self.version}\2', content, flags=re.DOTALL)
            else:
                # Add version to [project] section
                content = re.sub(
                    r'(\[project\])',
                    rf'\1\nversion = "{self.version}"',
                    content
                )
        else:
            # Add [project] section at the beginning
            content = f'[project]\nversion = "{self.version}"\n\n{content}'
        
        if not self.dry_run:
            self.pyproject_toml_path.write_text(content, encoding='utf-8')
            print(f"Updated pyproject.toml: -> {self.version}")
        else:
            print(f"[DRY RUN] Would update pyproject.toml: -> {self.version}")
    
    def get_last_tag(self) -> Optional[str]:
        """Get the last git tag."""
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
    
    def run(self):
        """Run the full release automation process."""
        print(f"🚀 Release Automation for version {self.version}")
        print("=" * 50)
        
        # Get last tag
        last_tag = self.get_last_tag()
        print(f"Last tag: {last_tag or 'None (initial release)'}")
        
        # Parse commits
        print("\n📝 Parsing commits...")
        commits = self.parse_commits(from_tag=last_tag)
        print(f"Found {len(commits)} conventional commits")
        
        if not commits:
            print("⚠️  No conventional commits found. Creating empty release entry.")
        
        # Categorize commits
        categories = self.categorize_commits(commits)
        
        # Generate changelog entry
        print("\n📋 Generating changelog entry...")
        changelog_entry = self.generate_changelog_entry(categories)
        
        # Update files
        print("\n📝 Updating files...")
        self.update_changelog(changelog_entry)
        self.update_package_json()
        self.update_pyproject_toml()
        
        print("\n✅ Release automation complete!")
        
        if self.dry_run:
            print("\n⚠️  DRY RUN: No files were modified")
        else:
            print(f"\n📦 Version {self.version} ready for release")
            print("\nNext steps:")
            print("1. Review the changes:")
            print("   git diff")
            print("2. Commit the changes:")
            print(f"   git add CHANGELOG.md package.json pyproject.toml")
            print(f"   git commit -m 'chore(release): bump version to {self.version}'")
            print("3. Create and push the tag:")
            print(f"   git tag -a v{self.version} -m 'Release {self.version}'")
            print(f"   git push origin v{self.version}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automate release version bumps and changelog generation')
    parser.add_argument('version', help='Version number (e.g., 1.2.3)')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without modifying files')
    
    args = parser.parse_args()
    
    # Validate version format
    if not re.match(r'^\d+\.\d+\.\d+$', args.version):
        print(f"Error: Invalid version format: {args.version}", file=sys.stderr)
        print("Expected format: MAJOR.MINOR.PATCH (e.g., 1.2.3)", file=sys.stderr)
        sys.exit(1)
    
    automation = ReleaseAutomation(args.version, dry_run=args.dry_run)
    automation.run()


if __name__ == '__main__':
    main()

