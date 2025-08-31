# Release Workflow Testing Guide

This guide explains how to test the automated release workflow locally before pushing changes.

## Overview

The release workflow automatically:
1. Extracts version from Git tag (e.g., `v0.1.38`)
2. Updates `custom_components/petkit_ble/manifest.json` with the correct version
3. Commits and force-pushes the updated manifest
4. Creates a GitHub release with AI-generated or enhanced release notes

## Prerequisites

### Required Tools
- **Git**: For version control
- **Python 3.x**: For JSON manipulation
- **Bash**: For running test scripts

### Optional Tools
- **act**: For full workflow simulation ([install guide](https://github.com/nektos/act#installation))
- **Docker**: Required if using `act`

## Testing Methods

### Method 1: Simple Manifest Update Test (Recommended)

Test only the manifest version update logic:

```bash
# Test with a specific version
./.github/test-manifest-update.sh v0.2.0

# Test with current version
./.github/test-manifest-update.sh v0.1.38
```

This script:
- ✅ Backs up your current manifest.json
- ✅ Tests version update functionality
- ✅ Verifies JSON formatting
- ✅ Tests idempotency
- ✅ Automatically restores original manifest

### Method 2: Full Workflow Test with act

Test the complete workflow using `act`:

```bash
# Dry run (no actual changes)
./.github/test-release-workflow.sh v0.2.0 true

# Full test (makes local changes)
./.github/test-release-workflow.sh v0.2.0
```

**Note**: Requires `act` and Docker to be installed.

### Method 3: Manual Python Script Test

Test the Python update script directly:

```bash
# Update to a specific version
python .github/update-manifest-version.py 0.2.0

# With 'v' prefix (automatically stripped)
python .github/update-manifest-version.py v0.2.0

# Using environment variable
VERSION=0.2.0 python .github/update-manifest-version.py
```

## Installation of act (Optional)

If you want to test the full workflow:

### macOS
```bash
brew install act
```

### Linux
```bash
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

### Windows
```bash
choco install act-cli
```

## Workflow Behavior

### Version Update Process

1. **Tag Push**: When you push a tag like `v0.1.39`
2. **Version Extraction**: Workflow extracts `0.1.39` from the tag
3. **Manifest Update**: Updates `manifest.json` version field
4. **Commit & Push**: Commits change and force-updates the tag
5. **Release Creation**: Creates GitHub release with the updated manifest

### Edge Cases Handled

- ✅ Version already matches (idempotent)
- ✅ 'v' prefix in tags (automatically stripped)
- ✅ Invalid JSON in manifest (error reported)
- ✅ Missing manifest file (warning issued)
- ✅ Pre-release versions (e.g., `v0.1.39-beta.1`)

## Troubleshooting

### Common Issues

1. **act not found**
   - Install act using the installation guide above
   - Or use the simple test script instead

2. **Docker not running**
   - Start Docker Desktop or the Docker daemon
   - Or use the simple test script instead

3. **Permission denied**
   - Make scripts executable: `chmod +x .github/*.sh`

4. **Python not found**
   - Ensure Python 3.x is installed: `python3 --version`

## CI/CD Integration

The workflow runs automatically on GitHub when:
- A version tag is pushed (e.g., `v0.1.39`)
- Matches pattern: `v*.*.*`

### Manual Release Process

```bash
# Create and push a version tag
git tag v0.1.39 -m "Release v0.1.39"
git push origin v0.1.39
```

The workflow will:
1. Update manifest.json automatically
2. Create a GitHub release
3. Generate AI-powered release notes (if OpenAI API key is configured)

## Security Notes

- The workflow uses `github-actions[bot]` for commits
- Force-push is limited to the tagged commit
- Secrets are never exposed in logs
- Test scripts create temporary files that are cleaned up automatically