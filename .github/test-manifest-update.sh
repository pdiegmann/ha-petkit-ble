#!/bin/bash

# Simple test script for manifest version update (no act required)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing Manifest Version Update${NC}"
echo "================================================"

# Test version
TEST_VERSION="${1:-0.1.99}"

# Remove 'v' prefix if present
if [[ $TEST_VERSION == v* ]]; then
    VERSION_WITHOUT_V="${TEST_VERSION:1}"
else
    VERSION_WITHOUT_V="$TEST_VERSION"
fi

echo -e "${YELLOW}📋 Test Configuration:${NC}"
echo "  Test Version: $TEST_VERSION"
echo "  Clean Version: $VERSION_WITHOUT_V"
echo ""

# Check if manifest exists
MANIFEST_PATH="custom_components/petkit_ble/manifest.json"
if [ ! -f "$MANIFEST_PATH" ]; then
    echo -e "${RED}❌ Error: manifest.json not found at $MANIFEST_PATH${NC}"
    exit 1
fi

# Backup manifest
cp "$MANIFEST_PATH" "$MANIFEST_PATH.backup"
echo -e "${GREEN}✅ Created backup of manifest.json${NC}"

# Function to cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    
    # Restore manifest
    if [ -f "$MANIFEST_PATH.backup" ]; then
        mv "$MANIFEST_PATH.backup" "$MANIFEST_PATH"
        echo -e "${GREEN}✅ Restored original manifest.json${NC}"
    fi
}

# Set trap to cleanup on exit
trap cleanup EXIT

# Get current version
CURRENT_VERSION=$(python3 -c "import json; print(json.load(open('$MANIFEST_PATH'))['version'])")
echo -e "${BLUE}📦 Current version in manifest: $CURRENT_VERSION${NC}"

# Test 1: Update to new version
echo ""
echo -e "${YELLOW}Test 1: Update to new version${NC}"
python3 .github/update-manifest-version.py "$VERSION_WITHOUT_V"

# Verify update
NEW_VERSION=$(python3 -c "import json; print(json.load(open('$MANIFEST_PATH'))['version'])")
if [ "$NEW_VERSION" == "$VERSION_WITHOUT_V" ]; then
    echo -e "${GREEN}✅ Version updated successfully to $NEW_VERSION${NC}"
else
    echo -e "${RED}❌ Version update failed. Expected $VERSION_WITHOUT_V, got $NEW_VERSION${NC}"
    exit 1
fi

# Test 2: Update with same version (should be idempotent)
echo ""
echo -e "${YELLOW}Test 2: Update with same version (idempotent test)${NC}"
python3 .github/update-manifest-version.py "$VERSION_WITHOUT_V"
echo -e "${GREEN}✅ Idempotent test passed${NC}"

# Test 3: Update with 'v' prefix
echo ""
echo -e "${YELLOW}Test 3: Update with 'v' prefix${NC}"
python3 .github/update-manifest-version.py "v$VERSION_WITHOUT_V"

# Verify it strips the 'v'
FINAL_VERSION=$(python3 -c "import json; print(json.load(open('$MANIFEST_PATH'))['version'])")
if [ "$FINAL_VERSION" == "$VERSION_WITHOUT_V" ]; then
    echo -e "${GREEN}✅ 'v' prefix correctly stripped${NC}"
else
    echo -e "${RED}❌ 'v' prefix not stripped. Expected $VERSION_WITHOUT_V, got $FINAL_VERSION${NC}"
    exit 1
fi

# Test 4: Verify JSON formatting is preserved
echo ""
echo -e "${YELLOW}Test 4: Verify JSON formatting${NC}"
python3 -c "import json; json.load(open('$MANIFEST_PATH'))" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ JSON format is valid${NC}"
else
    echo -e "${RED}❌ JSON format is invalid${NC}"
    exit 1
fi

# Show the final manifest content
echo ""
echo -e "${BLUE}📄 Final manifest.json content:${NC}"
cat "$MANIFEST_PATH" | python3 -m json.tool | head -10

echo ""
echo -e "${GREEN}🎉 All tests passed successfully!${NC}"
echo ""
echo "The workflow will:"
echo "1. Extract version from Git tag"
echo "2. Update manifest.json with the new version"
echo "3. Commit the change (if needed)"
echo "4. Force-push the updated tag"
echo "5. Create the GitHub release"