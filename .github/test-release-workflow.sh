#!/bin/bash

# Script to test the release workflow locally using act
# Requires: act (https://nektosact.com)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧪 Testing Release Workflow with act${NC}"
echo "================================================"

# Check if act is installed
if ! command -v act &> /dev/null; then
    echo -e "${RED}❌ Error: 'act' is not installed${NC}"
    echo ""
    echo "Please install act first:"
    echo "  macOS:    brew install act"
    echo "  Linux:    curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash"
    echo "  Windows:  choco install act-cli"
    echo ""
    echo "Or visit: https://github.com/nektos/act#installation"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not running${NC}"
    echo "Please start Docker Desktop or the Docker daemon"
    exit 1
fi

# Parse arguments
TEST_VERSION="${1:-v0.1.99}"
DRY_RUN="${2:-false}"

echo -e "${YELLOW}📋 Test Configuration:${NC}"
echo "  Test Version: $TEST_VERSION"
echo "  Dry Run: $DRY_RUN"
echo ""

# Create a temporary secrets file for testing
SECRETS_FILE=".secrets.test"
cat > "$SECRETS_FILE" << EOF
GITHUB_TOKEN=test-token-12345
OPENAI_API_KEY=
APP_ID=
APP_PRIVATE_KEY=
EOF

echo -e "${GREEN}✅ Created test secrets file${NC}"

# Create test event payload for push tag
EVENT_FILE=".github/test-event.json"
cat > "$EVENT_FILE" << EOF
{
  "ref": "refs/tags/$TEST_VERSION",
  "before": "0000000000000000000000000000000000000000",
  "after": "1234567890abcdef1234567890abcdef12345678",
  "repository": {
    "name": "ha-petkit-ble",
    "full_name": "pdiegmann/ha-petkit-ble",
    "owner": {
      "name": "pdiegmann",
      "email": "test@example.com"
    }
  },
  "pusher": {
    "name": "test-user",
    "email": "test@example.com"
  },
  "head_commit": {
    "id": "1234567890abcdef1234567890abcdef12345678",
    "message": "Release $TEST_VERSION",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "author": {
      "name": "test-user",
      "email": "test@example.com"
    }
  }
}
EOF

echo -e "${GREEN}✅ Created test event payload${NC}"

# Backup current manifest.json
if [ -f "custom_components/petkit_ble/manifest.json" ]; then
    cp custom_components/petkit_ble/manifest.json custom_components/petkit_ble/manifest.json.backup
    echo -e "${GREEN}✅ Backed up manifest.json${NC}"
fi

# Function to cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    
    # Restore manifest.json if backup exists
    if [ -f "custom_components/petkit_ble/manifest.json.backup" ]; then
        mv custom_components/petkit_ble/manifest.json.backup custom_components/petkit_ble/manifest.json
        echo -e "${GREEN}✅ Restored manifest.json${NC}"
    fi
    
    # Remove test files
    rm -f "$SECRETS_FILE" "$EVENT_FILE"
    echo -e "${GREEN}✅ Removed test files${NC}"
}

# Set trap to cleanup on exit
trap cleanup EXIT

echo ""
echo -e "${YELLOW}🚀 Running workflow test...${NC}"
echo "================================================"

# Test command arguments
ACT_ARGS=(
    "push"
    "--eventpath" "$EVENT_FILE"
    "--secret-file" "$SECRETS_FILE"
    "--artifact-server-path" "/tmp/act-artifacts"
    "-W" ".github/workflows/release.yml"
    "--verbose"
)

# Add dry-run flag if requested
if [ "$DRY_RUN" == "true" ]; then
    ACT_ARGS+=("--dryrun")
    echo -e "${YELLOW}⚠️  Running in DRY RUN mode - no actual changes will be made${NC}"
fi

# Run act with the workflow
echo ""
echo "Running: act ${ACT_ARGS[*]}"
echo ""

if act "${ACT_ARGS[@]}"; then
    echo ""
    echo -e "${GREEN}✅ Workflow test completed successfully!${NC}"
    
    # Check if manifest was updated (in non-dry-run mode)
    if [ "$DRY_RUN" != "true" ] && [ -f "custom_components/petkit_ble/manifest.json" ]; then
        echo ""
        echo -e "${YELLOW}📋 Manifest.json content after test:${NC}"
        grep -E '"version"' custom_components/petkit_ble/manifest.json || true
    fi
else
    echo ""
    echo -e "${RED}❌ Workflow test failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Test completed!${NC}"
echo ""
echo "To test with a different version:"
echo "  $0 v1.2.3"
echo ""
echo "To run in dry-run mode (no changes):"
echo "  $0 v1.2.3 true"