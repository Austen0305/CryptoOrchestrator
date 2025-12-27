#!/bin/bash
# Prepare Release Script
# Helper script to prepare a release by running the automation script and creating a tag

set -e

VERSION="${1:-}"

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.2.3"
    exit 1
fi

# Validate version format
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Invalid version format: $VERSION"
    echo "Expected format: MAJOR.MINOR.PATCH (e.g., 1.2.3)"
    exit 1
fi

echo "🚀 Preparing release $VERSION"
echo "================================"

# Run release automation (dry run first)
echo ""
echo "📋 Running release automation (dry run)..."
python scripts/release_automation.py "$VERSION" --dry-run

echo ""
read -p "Review the changes above. Continue with release? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Release cancelled."
    exit 1
fi

# Run release automation for real
echo ""
echo "📝 Running release automation..."
python scripts/release_automation.py "$VERSION"

# Show changes
echo ""
echo "📊 Changes made:"
git diff --stat

echo ""
read -p "Review the changes. Commit and create tag? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Release preparation complete. Commit manually:"
    echo "  git add CHANGELOG.md package.json pyproject.toml"
    echo "  git commit -m 'chore(release): bump version to $VERSION'"
    echo "  git tag -a v$VERSION -m 'Release $VERSION'"
    echo "  git push origin main && git push origin v$VERSION"
    exit 0
fi

# Commit changes
echo ""
echo "💾 Committing changes..."
git add CHANGELOG.md package.json pyproject.toml
git commit -m "chore(release): bump version to $VERSION" || echo "No changes to commit"

# Create tag
echo ""
echo "🏷️  Creating tag..."
git tag -a "v$VERSION" -m "Release $VERSION"

echo ""
echo "✅ Release $VERSION prepared!"
echo ""
echo "Next steps:"
echo "  1. Review the changes: git show HEAD"
echo "  2. Push the commit: git push origin main"
echo "  3. Push the tag: git push origin v$VERSION"
echo ""
echo "The GitHub Actions workflow will automatically:"
echo "  - Create a GitHub release"
echo "  - Build Electron app"
echo "  - Upload release assets"

