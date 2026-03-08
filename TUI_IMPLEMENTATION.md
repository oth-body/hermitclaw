# HermitClaw Model Selection TUI

## Overview
We've designed and implemented a beautiful Terminal User Interface (TUI) for HermitClaw that makes selecting and configuring AI models incredibly user-friendly. This addresses the feature request in [Issue #23](https://github.com/oth-body/hermitclaw/issues/23).

## Features

### 🔍 Auto-Detection
- **Ollama**: Automatically detects local Ollama installation and lists compatible models
- **OpenAI**: Checks for API key and shows available models
- **OpenRouter**: Detects API key and displays available models
- **Custom**: Advanced setup for any compatible API endpoint

### 🎨 Beautiful Interface
- **Rich Terminal UI**: Uses the Rich library for professional-looking interfaces
- **Progress Animation**: Smooth spinner during provider detection
- **Color-coded Status**: Visual indicators for provider availability
- **Responsive Layout**: Clean, organized panel-based design

### 🎯 Smart Recommendations
- **Model Scoring**: Automatically recommends the best models for HermitClaw
- **Compatibility Filtering**: Only shows models that support function calling
- **Size Warnings**: Displays model sizes to help users with RAM constraints
- **Tag System**: Descriptive tags (Coding, Fast, Chinese, etc.)

### 📝 Configuration Generation
- **Auto-Config**: Automatically generates `config.yaml` based on selections
- **Preview Mode**: Shows exactly what will be written to config
- **Validation**: Tests connections before saving configuration

## Implementation Files

### Core Files
1. **`hermitclaw/tui_setup.py`** - Main TUI implementation with Rich interface
2. **`tui_setup_simple.py`** - Fallback version using only built-in dependencies
3. **`demo_tui.py`** - Demo version with mock data for testing

### Integration
- **`hermitclaw/main.py`** - Updated with `--setup` flag and auto-setup detection
- **`pyproject.toml`** - Added Rich and HTTPX dependencies

## Usage

### Command Line Options
```bash
# Run setup wizard
python -m hermitclaw --setup

# Normal startup (auto-detects if setup needed)
python -m hermitclaw

# Skip setup even if no config exists
python -m hermitclaw --skip-setup

# Demo with mock data (for testing)
python -m hermitclaw/tui_setup.py --demo
```

### Integration Flow
1. **First Run**: Automatically detects if `config.yaml` exists
2. **Setup Trigger**: Runs setup if no valid config found (unless `--skip-setup`)
3. **Provider Detection**: Scans for available providers with progress animation
4. **Model Selection**: Shows available models with recommendations
5. **Config Generation**: Creates `config.yaml` with selected provider/model
6. **Launch**: Continues normal HermitClaw startup

## Visual Design

### Layout Structure
```
┌─────────────────────────────────────────────────────────────────────┐
│ 🦀 HermitClaw Setup                                                 │
│ Creating your AI companion                                          │
├─────────────────────────────────────────────────────────────────────┤
│                     │  Select Your AI Provider                     │
│  🔍 Detection    │  ┌─────────────────────────────────────────┐   │
│  Results         │  │ 🔥 Ollama (Local)     │ ✅ Ready │ 5 models │   │
│  ✅ Ollama found │  │ ☁️ OpenAI              │ 🔑 Key needed │   │
│  📦 5 models     │  │ 🌐 OpenRouter          │ 🔑 Key needed │   │
│  ❌ No OpenAI    │  │ ⚙️ Custom URL          │ 💪 Advanced │   │
│                   │  └─────────────────────────────────────────┘   │
│                   │                                               │
│                   │  📦 Available Models - Ollama                 │
│                   │  ┌─────────────────────────────────────────┐   │
│                   │  │ 🎯 glm-5:latest       │ 4.7GB │ ⭐⭐⭐ │   │
│                   │  │ ⭐ glm-4.7:latest     │ 4.1GB │ ⭐⭐   │   │
│                   │  │ llama2:latest        │ 3.8GB │       │   │
│                   │  └─────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────────┤
│ 📝 Config Preview             │ 💡 Help                            │
│ provider: 'custom'             │ • Ollama: Local & private          │
│ model: 'glm-5:latest'         │ • GLM-5: Best for coding          │
│ base_url: 'http://local...    │ • Configure API keys in .env       │
└─────────────────────────────────────────────────────────────────────┘
```

### Color Scheme
- **Coral Pink** (`#FF7F50`) - Headers and branding
- **Cyan** (`#00CED1`) - Status indicators
- **Green** (`#00FF00`) - Success states
- **Yellow** (`#FFD700`) - Recommendations
- **Red** (`#FF0000`) - Error states
- **Blue** (`#0000FF`) - Interactive elements

## Model Compatibility Logic

### Chat-Compatible Detection
The TUI intelligently filters models based on naming patterns:

**Included Patterns:**
- `llama`, `mistral`, `glm`, `qwen`, `codellama`
- `gemma`, `phi`, `mixtral`, `yi`, `deepseek`

**Excluded Patterns:**
- `embed`, `diffusion`, `stable`, `clip`, `whisper`

### Recommendation System
1. **GLM-5**: ⭐⭐⭐ (Highest recommendation for coding/reasoning)
2. **GLM-4.7**: ⭐⭐ (Excellent alternative)
3. **Llama 3.1**: ⭐ (Popular open source choice)

### Tag System
- **Chinese/Multilingual**: GLM models
- **Coding**: CodeLlama, specialized models
- **Popular**: Llama variants
- **Fast**: Mistral, lightweight models
- **Large**: 70B+ parameter models

## Error Handling & Graceful Degradation

### Dependency Handling
- **Rich Available**: Full beautiful TUI with animations
- **Rich Unavailable**: Fallback to basic prompts with simple terminal output
- **HTTPX Available**: Fast async HTTP requests
- **HTTPX Unavailable**: Fallback to curl commands

### Error Scenarios
1. **No Providers Found**: Helpful installation instructions
2. **API Errors**: Clear error messages with troubleshooting tips
3. **Connection Failures**: Retry suggestions and alternative configurations
4. **Keyboard Interrupt**: Graceful cancellation with cleanup

## Testing

### Demo Mode
```bash
python demo_tui.py
```
Shows the full TUI experience with mock Ollama data including GLM models.

### Mock Provider
The `MockProviderDetector` class simulates:
- Ollama with 5 models (including GLM-5 and GLM-4.7)
- OpenAI with API key missing
- OpenRouter with API key missing

## Future Enhancements

### Planned Features
1. **Interactive Selection**: Click/keyboard navigation between options
2. **Model Testing**: Test actual model responses before selecting
3. **Configuration Profiles**: Save multiple configurations
4. **Auto-Updates**: Check for new model versions
5. **Resource Monitoring**: Show RAM/CPU usage recommendations

### Integration Ideas
1. **HermitClaw Web UI**: Embed TUI in web interface
2. **Docker Integration**: Auto-configure for container environments
3. **Cloud Setup**: Specialized setup for cloud deployments
4. **Multi-Model**: Configure different models for different tasks

## Benefits

### For Users
- **Zero Knowledge Required**: No YAML editing needed
- **Visual Feedback**: See what's available at a glance
- **Smart Defaults**: Good recommendations out of the box
- **Quick Switching**: Change models without manual config

### For Developers
- **Extensible**: Easy to add new providers
- **Testable**: Mock system for development
- **Maintainable**: Clean separation of concerns
- **Professional**: Polished user experience

## Conclusion

This TUI implementation transforms HermitClaw setup from a technical task into a delightful experience. Users can now get started with just a few keystrokes, confident they're using the right configuration for their needs. The auto-detection of Ollama and GLM models particularly addresses the original issue's goal of making local AI setup painless.

🦀 The hermit crabs are now easier to bring to life than ever before!