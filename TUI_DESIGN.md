# HermitClaw Model Selection TUI Design

## Visual Concept
A beautiful, terminal-based interface that feels like the HermitClaw aesthetic - cozy, intelligent, and slightly magical.

## Key Libraries
- **rich** - For beautiful layouts, panels, syntax highlighting
- **textual** - For interactive TUI components
- **httpx** - For API calls to detect providers

## Layout Design

```
┌─────────────────────────────────────────────────────────────────────┐
│ 🦀 HermitClaw Setup                                                 │
│ Creating your AI companion                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🔍 Detecting AI providers...                                       │
│  ✅ Ollama found at http://localhost:11434                          │
│  📦 5 compatible models available                                   │
│  ❌ No OpenAI API key detected                                      │
│  ❌ No OpenRouter API key detected                                  │
│                                                                     │
│  ┌─ Select Your AI Provider ─────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  [🔥 Ollama (Local)     ] 5 models ready to use                │ │
│  │  [☁️ OpenAI              ] API key required                     │ │
│  │  [🌐 OpenRouter          ] API key required                     │ │
│  │  [⚙️ Custom URL          ] Advanced setup                       │ │
│  │                                                                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌─ Available Models ────────────────────────────────────────────┐ │
│  │                                                                 │ │
│  │  🎯 glm-5        (4.7GB)  Recommended for coding/reasoning     │ │
│  │  ⭐ glm-4.7       (4.1GB)  Fast, reliable performance          │ │
│  │  🐧 llama2        (3.8GB)  Stable and well-tested              │ │
│  │  🔧 codellama     (3.8GB)  Specialized for code                 │ │
│  │  🌊 mistral       (4.1GB)  Quick responses                       │ │
│  │                                                                 │ │
│  └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  [Test Connection] [Save & Start] [Advanced Mode] [Exit]           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Color Scheme & Theming
- **Primary**: Warm coral (#FF7F50) - matches the HermitClaw aesthetic
- **Secondary**: Soft teal (#40E0D0) - for success states
- **Accent**: Gold (#FFD700) - for recommendations
- **Background**: Deep navy (#1a1a2e) - comfortable for extended use
- **Text**: Light cream (#F5F5DC) - easy on the eyes

## Interaction Flow

### 1. Auto-Detection Phase
- Animated spinner while checking for providers
- Sequential checking: Ollama → OpenAI → OpenRouter → Custom
- Real-time status updates with emojis

### 2. Provider Selection
- Highlighted default (Ollama if available)
- Show model count for each provider
- Smooth transitions between states

### 3. Model Selection
- Rich model cards with metadata
- Size warnings for RAM constraints
- Recommendation badges
- Filter/search capability for many models

### 4. Configuration
- API key input with show/hide toggle
- Real-time connection testing
- Validation feedback
- Progressive disclosure for advanced options

## Component Design

### ProviderCard
```python
class ProviderCard(Widget):
    def __init__(self, provider_type: str, status: str, model_count: int = 0):
        self.icon = self._get_icon(provider_type)
        self.name = self._get_display_name(provider_type)
        self.status = status
        self.model_count = model_count
        self.selected = False
    
    def render(self) -> RichContent:
        # Animated selection state
        # Status indicators
        # Model count badges
```

### ModelCard
```python
class ModelCard(Widget):
    def __init__(self, name: str, size: str, tags: List[str], recommended: bool = False):
        self.name = name
        self.size = size
        self.tags = tags
        self.recommended = recommended
    
    def render(self) -> RichContent:
        # Rich layout with icons and metadata
        # Recommendation star if applicable
        # Size warnings for larger models
```

### ConnectionTester
```python
class ConnectionTester(Widget):
    async def test_connection(self, provider: Provider, model: str) -> TestResult:
        # Animated testing sequence
        # Detailed error reporting
        # Success confirmation
```

## Animation Details

### Detection Animation
```
🔍 Scanning for Ollama...    [⚪⚪⚪]
✅ Ollama found!              [⚫⚪⚪]
🔍 Checking OpenAI...          [⚫⚫⚪]
❌ No API key found            [⚫⚫⚫]
```

### Selection Animation
- Smooth highlight transitions
- Subtle pulse on hover
- Confetti-like burst on successful connection

## Error Handling UX

### Connection Errors
```
❌ Connection Failed
├─ Provider: Ollama
├─ Model: glm-5
├─ Error: Connection refused
└─ Suggestion: Check if Ollama is running on localhost:11434

[🔄 Retry] [⚙️ Manual Config] [❌ Cancel]
```

### Model Compatibility
```
⚠️ Model Warning
Model "stable-diffusion" detected but may not support:
- Function calling (required for tools)
- Long context windows

Use anyway? [Yes] [No] [Learn More]
```

## Advanced Mode
Progressive disclosure for power users:
```python
class AdvancedConfig(Widget):
    def __init__(self):
        self.custom_url = InputField("Custom Base URL")
        self.api_key = SecureInputField("API Key")
        self.custom_headers = KeyValueEditor("Custom Headers")
        self.timeout = Slider("Timeout (seconds)", 30, 300)
```

## Accessibility
- High contrast mode toggle
- Keyboard navigation fully supported
- Screen reader friendly labels
- Adjustable text size

## Performance Optimizations
- Lazy loading of model lists
- Caching provider status
- Debounced connection testing
- Efficient redraw cycles

## Integration Points
- Falls back to existing config.yaml editing
- Can be invoked with --setup flag
- Graceful degradation if rich/textual unavailable

This design creates a beautiful, intuitive experience that makes setting up HermitClaw feel magical rather than technical. 🦀