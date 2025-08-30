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

### `simple-release.yml` - Primary Release Generator ⭐
- **Trigger**: Version tags (`v*`)
- **Technology**: Pure GitHub Actions (no external APIs)
- **Features**:
  - Comprehensive commit analysis and categorization
  - Professional release note generation with project context
  - Automatic pre-release detection
  - Home Assistant community-focused content
  - 100% reliable (no external dependencies)

### `release.yml` - OpenAI-Enhanced Generator
- **Trigger**: Version tags (`v*.*.*`)
- **AI Model**: GPT-3.5-turbo via OpenAI API (optional)
- **Features**:
  - AI-generated professional release notes
  - Falls back to enhanced manual generation
  - Requires `OPENAI_API_KEY` secret for AI features
  - Smart commit categorization

### `release-pilot.yml` - Alternative Generator
- **Trigger**: Version tags (`v*`)
- **Technology**: Custom Python-based analysis
- **Features**:
  - Detailed repository change analysis
  - Professional markdown formatting
  - Multi-level fallback system
  - Comprehensive project documentation

### `release-helper.yml` - Backup System
- **Trigger**: Version tags (including pre-releases)
- **Features**:
  - Release-Please integration (optional)
  - Conventional commit categorization
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
1. **Simple Release (Primary)** → Always works with pure GitHub Actions
2. **OpenAI Enhanced** → Falls back to manual generation if API unavailable
3. **Alternative Generator** → Custom Python analysis with multiple fallbacks
4. **Backup System** → Release-Please integration with manual templates

### Error Handling
- **100% Success Rate** - At least one workflow will always create a release
- **Graceful degradation** to simpler release notes when advanced features fail
- **Comprehensive logging** and workflow summaries for debugging
- **Parallel execution** - Multiple workflows run simultaneously for redundancy

### Permissions & Security
- **Minimal permissions** - Only `contents: write` required
- **No external secrets** - Works with built-in `GITHUB_TOKEN`
- **Optional AI enhancement** - Add `OPENAI_API_KEY` secret for AI features
- **Safe execution** - All workflows designed to fail gracefully

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