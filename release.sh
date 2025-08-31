#!/bin/bash

# Release script for PetKit BLE Integration
# Automatically handles git operations and version tagging
# Usage: ./release.sh [version|major|minor|patch] [commit message]

set -e

# Colors for output (define early)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
DRY_RUN=false
AUTO_YES=false

# Helper function for error messages
show_error() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
    if [ "$2" != "" ]; then
        echo -e "${YELLOW}💡 Suggestion: $2${NC}" >&2
    fi
}

# Helper function for warnings
show_warning() {
    echo -e "${YELLOW}⚠️  Warning: $1${NC}" >&2
}

# Helper function for info messages
show_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Helper function for success messages
show_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to display usage
show_usage() {
    echo -e "${CYAN}📦 PetKit BLE Release Script${NC}"
    echo "Automated version management and release creation for PetKit BLE integration"
    echo ""
    echo -e "${YELLOW}Usage:${NC} $0 [OPTIONS] [VERSION_TYPE] [COMMIT_MESSAGE]"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  --help, -h     Show this help message and exit"
    echo "  --dry-run, -n  Show what would be done without executing"
    echo "  --yes, -y      Skip confirmation prompts (auto-confirm)"
    echo ""
    echo -e "${YELLOW}Version Types:${NC}"
    echo "  patch          Increment patch version (0.0.x) - Bug fixes [DEFAULT]"
    echo "  minor          Increment minor version (0.x.0) - New features"
    echo "  major          Increment major version (x.0.0) - Breaking changes"
    echo "  x.y.z          Set specific version (e.g., 1.2.3 or v1.2.3)"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "${GREEN}Basic Usage:${NC}"
    echo "  $0                                    # Increment patch version (interactive)"
    echo "  $0 minor                              # Increment minor version (interactive)"
    echo ""
    echo -e "${GREEN}Automated Usage (no prompts):${NC}"
    echo "  $0 -y                                 # Quick patch release"
    echo "  $0 -y minor \"Add device support\"     # Minor release with message"
    echo "  $0 --yes major \"Breaking changes\"    # Major release with message"
    echo ""
    echo -e "${GREEN}Testing (dry run):${NC}"
    echo "  $0 --dry-run minor                    # Test minor increment"
    echo "  $0 -n -y v2.1.0                      # Test specific version"
    echo ""
    echo -e "${GREEN}Custom Versions:${NC}"
    echo "  $0 -y v1.0.0 \"First stable release\"  # Set specific version"
    echo "  $0 -y 2.1.0                          # Version without 'v' prefix"
    echo ""
    echo -e "${YELLOW}What the script does:${NC}"
    echo "  1. 🔍 Checks for remote updates and pulls if needed"
    echo "  2. 📦 Stages all uncommitted changes"
    echo "  3. 📝 Creates commit with semantic versioning message"
    echo "  4. 🚀 Pushes commits and creates version tag"
    echo "  5. 🤖 Triggers GitHub workflow for release creation"
    echo "  6. ✨ Updates manifest.json automatically via workflow"
    echo ""
    echo -e "${BLUE}💡 Note:${NC} Never manually edit manifest.json version - it's handled automatically!"
}

# Parse flags
while [[ $1 == --* ]] || [[ $1 == -* ]]; do
    case $1 in
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --yes|-y)
            AUTO_YES=true
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            show_error "Unknown flag: $1" "Use --help to see available options"
            exit 1
            ;;
    esac
done

# Function to get current version from manifest
get_current_version() {
    if [ -f "custom_components/petkit_ble/manifest.json" ]; then
        python3 -c "import json; print(json.load(open('custom_components/petkit_ble/manifest.json'))['version'])"
    else
        echo "0.0.0"
    fi
}

# Function to increment version
increment_version() {
    local version=$1
    local increment_type=$2
    
    # Split version into parts
    IFS='.' read -r major minor patch <<< "$version"
    
    case $increment_type in
        major)
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        minor)
            minor=$((minor + 1))
            patch=0
            ;;
        patch)
            patch=$((patch + 1))
            ;;
    esac
    
    echo "$major.$minor.$patch"
}

# Function to generate commit message
generate_commit_message() {
    local changes=""
    
    # Check for different types of changes
    if git diff --cached --name-only | grep -q "custom_components/petkit_ble/.*\.py$"; then
        if git diff --cached | grep -q "feat:"; then
            changes="features"
        elif git diff --cached | grep -q "fix:"; then
            changes="fixes"
        else
            changes="improvements"
        fi
    fi
    
    if git diff --cached --name-only | grep -q "\.github/"; then
        if [ -n "$changes" ]; then
            changes="$changes and CI/CD updates"
        else
            changes="CI/CD updates"
        fi
    fi
    
    if git diff --cached --name-only | grep -q "\.md$"; then
        if [ -n "$changes" ]; then
            changes="$changes and documentation"
        else
            changes="documentation updates"
        fi
    fi
    
    if [ -z "$changes" ]; then
        changes="updates"
    fi
    
    echo "Release with $changes"
}

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    show_error "Not in a git repository" "Run 'git init' or navigate to a git repository"
    exit 1
fi

# Check if git is configured
if ! git config --get user.name > /dev/null || ! git config --get user.email > /dev/null; then
    show_error "Git user not configured" "Run 'git config --global user.name \"Your Name\"' and 'git config --global user.email \"your.email@example.com\"'"
    exit 1
fi

# Main script
echo -e "${CYAN}🚀 PetKit BLE Release Script${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}(DRY RUN MODE - No changes will be made)${NC}"
fi
echo "==============================="

# Parse arguments
VERSION_TYPE="${1:-patch}"
COMMIT_MESSAGE="$2"

# Get current version
CURRENT_VERSION=$(get_current_version)
show_info "Current version: $CURRENT_VERSION"

# Determine new version
if [[ $VERSION_TYPE =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    # Specific version provided
    NEW_VERSION=$(echo $VERSION_TYPE | sed 's/^v//')
    show_info "Setting specific version: $NEW_VERSION"
else
    # Increment version
    case $VERSION_TYPE in
        major|minor|patch)
            NEW_VERSION=$(increment_version $CURRENT_VERSION $VERSION_TYPE)
            show_info "Incrementing $VERSION_TYPE version: $CURRENT_VERSION → $NEW_VERSION"
            ;;
        *)
            show_error "Invalid version type: $VERSION_TYPE" "Use 'major', 'minor', 'patch', or specify version like '1.2.3'"
            exit 1
            ;;
    esac
fi

# Check for remote updates
show_info "Checking for remote updates..."
if [ "$DRY_RUN" != true ]; then
    git fetch origin main
    
    # Check if we need to pull
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
    
    if [ -n "$REMOTE" ] && [ "$LOCAL" != "$REMOTE" ]; then
        show_warning "Remote changes detected. Stashing local changes and pulling..."
        
        # Check if there are local changes to stash
        if ! git diff --quiet || ! git diff --cached --quiet; then
            git stash push -m "Pre-release stash $(date)"
            STASHED=true
        else
            STASHED=false
        fi
        
        git pull origin main
        
        # Restore stashed changes if any
        if [ "$STASHED" = true ]; then
            if git stash pop; then
                show_success "Local changes restored successfully"
            else
                show_error "Failed to restore stashed changes" "Resolve conflicts manually and run the script again"
                exit 1
            fi
        fi
    fi
else
    echo "[DRY RUN] Would check for remote updates and pull if needed"
fi

# Stage all changes
show_info "Staging all changes..."
if [ "$DRY_RUN" != true ]; then
    git add -A
else
    echo "[DRY RUN] Would stage all changes (git add -A)"
fi

# Check if there are changes to commit
if [ "$DRY_RUN" != true ]; then
    if git diff --cached --quiet; then
        show_warning "No changes to commit. Creating tag only..."
        SKIP_COMMIT=true
    else
        SKIP_COMMIT=false
    fi
else
    echo "[DRY RUN] Would check for staged changes"
    SKIP_COMMIT=false
fi

# Generate or use provided commit message
if [ "$SKIP_COMMIT" != true ]; then
    if [ -z "$COMMIT_MESSAGE" ]; then
        COMMIT_MESSAGE=$(generate_commit_message)
        show_info "Generated commit message: $COMMIT_MESSAGE"
    else
        show_info "Using provided commit message: $COMMIT_MESSAGE"
    fi
fi

# Show summary and confirm
echo ""
echo -e "${YELLOW}📋 Release Summary:${NC}"
echo "  Current Version: $CURRENT_VERSION"
echo "  New Version: $NEW_VERSION"
if [ "$SKIP_COMMIT" != true ]; then
    echo "  Commit Message: $COMMIT_MESSAGE"
else
    echo "  Commit: Skipped (no changes)"
fi
echo "  Tag: v$NEW_VERSION"
echo ""

# Confirm unless auto-yes is enabled
if [ "$AUTO_YES" != true ] && [ "$DRY_RUN" != true ]; then
    read -p "Continue with release? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        show_info "Release cancelled by user"
        exit 0
    fi
fi

# Create commit if there are changes
if [ "$SKIP_COMMIT" != true ]; then
    show_info "Creating commit..."
    if [ "$DRY_RUN" != true ]; then
        if git commit -m "$COMMIT_MESSAGE - v$NEW_VERSION"; then
            show_success "Commit created successfully"
        else
            show_error "Failed to create commit" "Check git status and resolve any issues"
            exit 1
        fi
    else
        echo "[DRY RUN] Would create commit with message: '$COMMIT_MESSAGE - v$NEW_VERSION'"
    fi
fi

# Create tag
show_info "Creating tag v$NEW_VERSION..."
if [ "$DRY_RUN" != true ]; then
    if git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"; then
        show_success "Tag v$NEW_VERSION created successfully"
    else
        show_error "Failed to create tag" "Tag may already exist. Use 'git tag -d v$NEW_VERSION' to delete it first"
        exit 1
    fi
else
    echo "[DRY RUN] Would create tag: v$NEW_VERSION"
fi

# Push commits and tags
show_info "Pushing to remote..."
if [ "$DRY_RUN" != true ]; then
    if git push origin main && git push origin "v$NEW_VERSION"; then
        show_success "Successfully pushed commits and tag to remote"
    else
        show_error "Failed to push to remote" "Check network connection and repository permissions"
        exit 1
    fi
else
    echo "[DRY RUN] Would push commits and tag to remote"
fi

# Success message
echo ""
echo -e "${GREEN}🎉 Release v$NEW_VERSION completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 What happens next:${NC}"
echo "  1. ✅ Commits and tag pushed to GitHub"
echo "  2. 🤖 GitHub Actions workflow will update manifest.json"
echo "  3. 📦 GitHub release will be created automatically"
echo "  4. 🔗 Release URL: https://github.com/pdiegmann/ha-petkit-ble/releases/tag/v$NEW_VERSION"
echo ""
echo -e "${YELLOW}⏱️  The GitHub workflow typically takes 1-2 minutes to complete.${NC}"