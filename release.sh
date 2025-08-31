#!/bin/bash

# Release script for PetKit BLE Integration
# Automatically handles git operations and version tagging
# Usage: ./release.sh [version|major|minor|patch] [commit message]

set -e

# Dry run mode (set to true for testing)
DRY_RUN=false
AUTO_YES=false

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
        *)
            echo -e "${RED}❌ Unknown flag: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to display usage
show_usage() {
    echo -e "${CYAN}📦 PetKit BLE Release Script${NC}"
    echo ""
    echo "Usage: $0 [--dry-run] [--yes] [version|major|minor|patch] [commit message]"
    echo ""
    echo "Options:"
    echo "  --dry-run, -n  - Show what would be done without executing"
    echo "  --yes, -y      - Skip confirmation prompts (auto-confirm)"
    echo ""
    echo "Arguments:"
    echo "  version    - Specific version (e.g., 1.2.3 or v1.2.3)"
    echo "  major      - Increment major version (x.0.0)"
    echo "  minor      - Increment minor version (0.x.0)"
    echo "  patch      - Increment patch version (0.0.x) [default]"
    echo "  (none)     - Same as 'patch'"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Increment patch version"
    echo "  $0 -y patch                           # Increment patch (auto-confirm)"  
    echo "  $0 --dry-run minor                    # Test minor increment"
    echo "  $0 -y minor \"Add new feature\"        # Increment minor with message"
    echo "  $0 --yes major \"Breaking changes\"    # Increment major with message"
    echo "  $0 -y v2.1.0 \"Custom version\"        # Set specific version"
    echo "  $0 --dry-run --yes 2.1.0             # Test specific version"
}

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

# Main script
echo -e "${CYAN}🚀 PetKit BLE Release Script${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}(DRY RUN MODE - No changes will be made)${NC}"
fi
echo "==============================="

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

# Check if we need to pull changes from remote
echo -e "${BLUE}🔍 Checking remote status...${NC}"
git fetch origin main

# Check if local is behind remote
LOCAL_COMMIT=$(git rev-parse HEAD)
REMOTE_COMMIT=$(git rev-parse origin/main)

if [ "$LOCAL_COMMIT" != "$REMOTE_COMMIT" ]; then
    echo -e "${YELLOW}⚠️  Local branch is behind remote${NC}"
    
    # Check if there are local changes
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}📝 Found local changes - stashing for pull...${NC}"
        
        # Stash changes temporarily
        git stash push -m "Temporary stash for release script pull"
        
        # Pull the latest changes
        echo -e "${BLUE}→ Pulling latest changes...${NC}"
        if git pull origin main; then
            echo -e "${GREEN}✅ Successfully pulled latest changes${NC}"
            
            # Restore stashed changes
            echo -e "${BLUE}→ Restoring local changes...${NC}"
            if git stash pop; then
                echo -e "${GREEN}✅ Local changes restored${NC}"
            else
                echo -e "${RED}❌ Failed to restore local changes${NC}"
                echo -e "${YELLOW}ℹ️  Your changes are in the stash. You can restore them with:${NC}"
                echo "  git stash pop"
                exit 1
            fi
        else
            echo -e "${RED}❌ Failed to pull latest changes${NC}"
            echo -e "${BLUE}→ Restoring stashed changes...${NC}"
            git stash pop
            exit 1
        fi
    else
        echo -e "${BLUE}→ Pulling latest changes...${NC}"
        git pull origin main
        echo -e "${GREEN}✅ Successfully pulled latest changes${NC}"
    fi
    
    echo ""
fi

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}📝 Found uncommitted changes${NC}"
    
    # Show changes
    echo ""
    echo -e "${BLUE}Modified files:${NC}"
    git status --short
    echo ""
fi

# Parse arguments
VERSION_ARG="${1:-patch}"
COMMIT_MESSAGE="${2:-}"

# Determine version increment type or specific version
CURRENT_VERSION=$(get_current_version)
echo -e "${BLUE}📌 Current version: ${CURRENT_VERSION}${NC}"

# Check if first argument is a version number
if [[ $VERSION_ARG =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    # Specific version provided
    NEW_VERSION="${VERSION_ARG#v}"  # Remove 'v' prefix if present
    echo -e "${YELLOW}📝 Setting specific version: ${NEW_VERSION}${NC}"
elif [[ $VERSION_ARG =~ ^(major|minor|patch)$ ]]; then
    # Increment type provided
    NEW_VERSION=$(increment_version "$CURRENT_VERSION" "$VERSION_ARG")
    echo -e "${YELLOW}📝 Incrementing ${VERSION_ARG} version: ${CURRENT_VERSION} → ${NEW_VERSION}${NC}"
else
    # Invalid argument
    echo -e "${RED}❌ Invalid version argument: $VERSION_ARG${NC}"
    echo ""
    show_usage
    exit 1
fi

# Add 'v' prefix for tag
TAG_NAME="v${NEW_VERSION}"

# Check if tag already exists
if git tag -l "$TAG_NAME" | grep -q "$TAG_NAME"; then
    echo -e "${RED}❌ Error: Tag $TAG_NAME already exists${NC}"
    echo "Please choose a different version or delete the existing tag"
    exit 1
fi

echo ""
echo -e "${GREEN}📋 Release Plan:${NC}"
echo "  Version: $CURRENT_VERSION → $NEW_VERSION"
echo "  Tag: $TAG_NAME"

# Stage all changes
echo ""
echo -e "${YELLOW}📂 Staging all changes...${NC}"
git add -A

# Check if there are changes to commit
if [ -z "$(git diff --cached --name-only)" ]; then
    echo -e "${YELLOW}⚠️  No changes to commit${NC}"
    
    # Ask if user wants to create tag anyway
    if [ "$AUTO_YES" = false ]; then
        read -p "Do you want to create tag $TAG_NAME anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}❌ Release cancelled${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠️  Auto-confirmed: Creating tag anyway${NC}"
    fi
    
    SKIP_COMMIT=true
else
    SKIP_COMMIT=false
    
    # Generate or use provided commit message
    if [ -z "$COMMIT_MESSAGE" ]; then
        COMMIT_MESSAGE=$(generate_commit_message)
    fi
    
    echo "  Commit: $COMMIT_MESSAGE"
fi

echo ""
if [ "$AUTO_YES" = false ]; then
    read -p "Do you want to proceed with the release? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Release cancelled${NC}"
        # Unstage changes
        git reset HEAD
        exit 1
    fi
else
    echo -e "${GREEN}✅ Auto-confirmed: Proceeding with release${NC}"
fi

# Perform release steps
echo ""
echo -e "${GREEN}🔧 Executing release...${NC}"

# Commit changes if any
if [ "$SKIP_COMMIT" = false ]; then
    echo -e "${BLUE}→ Committing changes...${NC}"
    
    # Build detailed commit message
    FULL_COMMIT_MESSAGE="chore: $COMMIT_MESSAGE - v$NEW_VERSION"
    
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would commit: $FULL_COMMIT_MESSAGE${NC}"
    else
        git commit -m "$FULL_COMMIT_MESSAGE"
        echo -e "${GREEN}✅ Changes committed${NC}"
    fi
fi

# Push commits to main
echo -e "${BLUE}→ Pushing commits to main...${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[DRY RUN] Would push commits to origin/main${NC}"
else
    if git push origin main; then
        echo -e "${GREEN}✅ Commits pushed${NC}"
    else
        echo -e "${RED}❌ Failed to push commits${NC}"
        echo -e "${YELLOW}ℹ️  The remote may have been updated during the release process${NC}"
        echo "Try pulling the latest changes and resolving any conflicts:"
        echo "  git pull --rebase origin main"
        echo "  git push origin main"
        echo "  git push origin $TAG_NAME"
        exit 1
    fi
fi

# Create and push tag
echo -e "${BLUE}→ Creating tag $TAG_NAME...${NC}"

# Generate tag message
TAG_MESSAGE="Release $TAG_NAME

Version: $NEW_VERSION"

# Add summary of changes since last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
    TAG_MESSAGE="$TAG_MESSAGE

Changes since $LAST_TAG:"
    
    # Get commit count
    COMMIT_COUNT=$(git rev-list --count "$LAST_TAG"..HEAD)
    TAG_MESSAGE="$TAG_MESSAGE
- $COMMIT_COUNT commits"
    
    # Get brief commit list
    COMMITS=$(git log --pretty=format:"- %s" "$LAST_TAG"..HEAD | head -10)
    if [ -n "$COMMITS" ]; then
        TAG_MESSAGE="$TAG_MESSAGE

Recent commits:
$COMMITS"
    fi
fi

# Create annotated tag
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[DRY RUN] Would create tag: $TAG_NAME${NC}"
    echo -e "${YELLOW}[DRY RUN] Tag message:${NC}"
    echo "$TAG_MESSAGE" | sed 's/^/  /'
else
    git tag -a "$TAG_NAME" -m "$TAG_MESSAGE"
    echo -e "${GREEN}✅ Tag created${NC}"
fi

# Push tag
echo -e "${BLUE}→ Pushing tag $TAG_NAME...${NC}"
if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[DRY RUN] Would push tag to origin${NC}"
else
    if git push origin "$TAG_NAME"; then
        echo -e "${GREEN}✅ Tag pushed${NC}"
    else
        echo -e "${RED}❌ Failed to push tag${NC}"
        echo -e "${YELLOW}ℹ️  Tag may already exist on remote or push failed${NC}"
        echo "You can manually push the tag with:"
        echo "  git push origin $TAG_NAME"
        exit 1
    fi
fi

# Success message
echo ""
echo -e "${GREEN}🎉 Release $TAG_NAME completed successfully!${NC}"
echo ""
echo -e "${CYAN}📋 Summary:${NC}"
echo "  • Version updated: $CURRENT_VERSION → $NEW_VERSION"
echo "  • Tag created: $TAG_NAME"
echo "  • GitHub workflow triggered"
echo ""
echo -e "${CYAN}🔗 Links:${NC}"
echo "  • Release: https://github.com/pdiegmann/ha-petkit-ble/releases/tag/$TAG_NAME"
echo "  • Actions: https://github.com/pdiegmann/ha-petkit-ble/actions"
echo ""
echo -e "${YELLOW}ℹ️  Note: The GitHub workflow will automatically update manifest.json${NC}"
echo -e "${YELLOW}    No manual version updates needed!${NC}"