# 🤖 Automated Release System Documentation

This repository uses **AI-powered automated release generation** that triggers when version tags are pushed to the repository.

## 🚀 How It Works

### 1. **Tag-Triggered Releases**
- Push any version tag (e.g., `v1.0.0`, `v0.1.19`, `v2.0.0-beta.1`)
- Multiple AI-powered workflows automatically generate professional release notes
- Creates GitHub releases with comprehensive changelogs

### 2. **AI-Generated Release Notes**
The system uses multiple approaches to ensure reliable release generation:

- **Primary**: Microsoft AI Inference with GPT-4o-mini
- **Fallback**: ReleasePilot AI-powered automation  
- **Backup**: Release-Please conventional commit parsing
- **Emergency**: Manual template with commit analysis

## 📋 Workflow Files

### `release.yml` - Primary AI Release Generator
- **Trigger**: Version tags (`v*.*.*`)
- **AI Model**: GPT-4o-mini via Microsoft AI Inference
- **Features**:
  - Comprehensive commit analysis
  - Professional release note generation
  - Automatic pre-release detection
  - Fallback to manual templates

### `release-pilot.yml` - ReleasePilot AI Automation  
- **Trigger**: Version tags (`v*`)
- **AI Provider**: OpenAI GPT-4o-mini
- **Features**:
  - Specialized for technical projects
  - Repository context awareness
  - Automatic draft/prerelease detection
  - Change detection and diff analysis

### `release-helper.yml` - Conventional Commits Backup
- **Trigger**: Version tags (including pre-releases)
- **Features**:
  - Conventional commit categorization
  - Release-Please integration
  - File change analysis
  - Multiple fallback mechanisms

## 🏷️ Creating Releases

### Manual Release Creation
```bash
# 1. Commit your changes
git add .
git commit -m "feat: add new awesome feature"
git push origin main

# 2. Create and push version tag
git tag -a v0.1.19 -m "Release v0.1.19"
git push origin v0.1.19

# 3. AI workflows automatically create the release!
```

### Automated via Script
```bash
# Create release script (save as create-release.sh)
#!/bin/bash
VERSION=$1
if [ -z "$VERSION" ]; then
  echo "Usage: ./create-release.sh v0.1.19"
  exit 1
fi

git tag -a "$VERSION" -m "Release $VERSION"  
git push origin "$VERSION"
echo "🚀 Release $VERSION will be created automatically by AI workflows!"
```

## 📊 Version Formats

### Stable Releases
- `v1.0.0`, `v0.1.19`, `v2.5.3`
- Creates standard releases
- AI generates comprehensive changelogs

### Pre-Releases  
- `v1.0.0-alpha.1`, `v0.2.0-beta.2`, `v1.0.0-rc.1`
- Marked as pre-releases
- Specialized release notes for testing versions

## 🎯 AI Prompt Engineering

The AI models are prompted with:

### Context
- **Project**: PetKit W5 BLE MQTT Integration  
- **Audience**: Home Assistant users, IoT enthusiasts
- **Focus**: BLE connectivity, device reliability, pet automation

### Release Note Structure
1. **🚀 Release Highlights** - Key improvements summary
2. **✨ New Features** - New capabilities and enhancements  
3. **🐛 Bug Fixes** - Issues resolved and stability improvements
4. **⚡ Performance & Reliability** - Optimizations and reliability enhancements
5. **🔧 Technical Changes** - Developer-focused improvements
6. **📚 Documentation** - Documentation updates and maintenance
7. **📋 Installation & Upgrade** - User guidance
8. **🔗 Links** - Changelog, documentation, issues

## 🔧 Configuration Files

### `release-please-config.json`
- Conventional commit type mapping
- Changelog section configuration
- Version bumping rules

### `.release-please-manifest.json`  
- Current version tracking
- Release-Please state management

## 🛡️ Reliability Features

### Multiple Fallbacks
1. **Primary AI fails** → ReleasePilot takes over
2. **Both AI systems fail** → Conventional commit parsing
3. **All automated systems fail** → Manual template with commit list

### Error Handling
- Graceful degradation to simpler release notes
- Always creates a release (never fails completely)  
- Comprehensive logging and workflow summaries

### Permissions
- `contents: write` - Create releases and tags
- `pull-requests: read` - Analyze PR context
- Uses `GITHUB_TOKEN` (no additional secrets required)

## 📈 Benefits

### For Developers
- **Zero Manual Work**: Just push a tag, AI handles the rest
- **Consistent Quality**: Professional release notes every time
- **Time Savings**: No more writing changelogs manually
- **Context Awareness**: AI understands the project and audience

### For Users  
- **Professional Documentation**: Clear, well-structured release notes
- **Technical Accuracy**: AI understands BLE, Home Assistant, and IoT concepts
- **User-Focused**: Benefits and improvements clearly explained
- **Reliable Information**: Multiple validation layers ensure accuracy

## 🔍 Monitoring & Debugging

### Workflow Status
- Check the **Actions** tab for workflow execution status
- Each workflow provides detailed step summaries
- Failed workflows still attempt to create releases with available data

### Release Quality
- Review AI-generated content for accuracy
- Edit releases manually if needed (releases support editing)
- Provide feedback for future AI prompt improvements

## 🎨 Customization

### Modifying AI Prompts
Edit the `prompt:` sections in workflow files to:
- Adjust release note structure
- Change focus areas
- Modify technical depth  
- Update audience targeting

### Adding New Workflows
- Create new `.yml` files in `.github/workflows/`
- Follow existing patterns for tag triggers
- Add appropriate fallback mechanisms

---

**Result**: Push a version tag → Receive professional AI-generated release notes automatically! 🎉