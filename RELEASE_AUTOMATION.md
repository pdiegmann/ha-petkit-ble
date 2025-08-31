# 🚀 Release Automation Guide

This document explains the automated release system for the PetKit BLE integration.

## Quick Start

```bash
# Most common usage - patch release
./release.sh

# With specific version type  
./release.sh minor "Add new device support"
./release.sh major "Breaking API changes"

# With specific version number
./release.sh v1.2.3 "Custom version release"

# Test what would happen (dry run)
./release.sh --dry-run minor
```

## How It Works

### 1. Automated Version Management
- ✅ **Never manually edit `manifest.json`** - the workflow handles this
- ✅ Uses semantic versioning: `major.minor.patch`
- ✅ Automatically increments versions based on your input
- ✅ Supports custom version numbers

### 2. Git Operations
The `release.sh` script automatically:
1. **Stages** all uncommitted changes (`git add -A`)
2. **Commits** with semantic commit message
3. **Pushes** commits to main branch
4. **Creates** annotated git tag
5. **Pushes** tag to trigger GitHub workflow

### 3. GitHub Workflow
The workflow (`.github/workflows/release.yml`) automatically:
1. **Updates** `manifest.json` version to match the tag
2. **Commits** the version update
3. **Creates** GitHub release with AI-generated notes
4. **Publishes** the release

## Version Types

| Command | Example | Result | Use Case |
|---------|---------|--------|----------|
| `./release.sh` | `0.1.39 → 0.1.40` | Patch | Bug fixes, minor improvements |
| `./release.sh minor` | `0.1.39 → 0.2.0` | Minor | New features, enhancements |
| `./release.sh major` | `0.1.39 → 1.0.0` | Major | Breaking changes |
| `./release.sh v2.0.0` | `0.1.39 → 2.0.0` | Custom | Specific version |

## Advanced Usage

### Dry Run Mode
Test what the script would do without making changes:

```bash
./release.sh --dry-run patch "Test message"
./release.sh -n minor  # Short form
```

### Custom Commit Messages
```bash
./release.sh minor "Add immediate BLE reconnection feature"
./release.sh patch "Fix connection timeout issue"
./release.sh major "Refactor to new API structure"
```

### Automated Commit Messages
If no message is provided, the script analyzes your changes and generates appropriate messages:

- **Features**: Detects new functionality
- **Fixes**: Identifies bug fixes
- **CI/CD**: Recognizes workflow changes
- **Documentation**: Finds documentation updates

## What Gets Committed

The release script stages **all** changes in your working directory:
- ✅ Modified files
- ✅ New files  
- ✅ Deleted files

Make sure you want to include all changes before running the script.

## Monitoring Releases

After running the release script, monitor:

1. **GitHub Actions**: https://github.com/pdiegmann/ha-petkit-ble/actions
2. **Releases**: https://github.com/pdiegmann/ha-petkit-ble/releases
3. **Tags**: Check that the tag was created successfully

## Troubleshooting

### Script Fails
- Check you're in the git repository root
- Ensure you have push permissions
- Verify the tag doesn't already exist

### Workflow Fails
- Check GitHub Actions logs
- Verify workflow permissions
- Ensure all required files exist

### Version Conflicts
- Never manually edit `manifest.json` version
- Delete problematic tags: `git tag -d v1.2.3 && git push origin :v1.2.3`
- Use specific version numbers to resolve conflicts

## Migration from Manual Process

**Before** (manual):
```bash
git add -A
git commit -m "feat: add new feature"  
python .github/update-manifest-version.py 0.1.40
git add custom_components/petkit_ble/manifest.json
git commit -m "chore: bump version to 0.1.40"
git push origin main
git tag -a v0.1.40 -m "Release v0.1.40"
git push origin v0.1.40
```

**After** (automated):
```bash
./release.sh minor "Add new feature"
```

## Best Practices

1. **Always use the script** - avoid manual git operations for releases
2. **Test with --dry-run** - verify changes before committing
3. **Use semantic versioning** - patch for fixes, minor for features, major for breaking changes
4. **Write clear messages** - help users understand what changed
5. **Monitor workflows** - ensure releases complete successfully

---

For more details, see [RELEASE_TESTING.md](.github/RELEASE_TESTING.md) for workflow testing information.