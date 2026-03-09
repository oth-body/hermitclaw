"""Beautiful TUI for HermitClaw model selection - minimal dependencies version."""

import asyncio
import json
import os
import sys
import time
import subprocess
from typing import Dict, List, Optional, Tuple

# Use only standard library + dependencies already in HermitClaw
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.align import Align
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ProviderDetector:
    """Detects available AI providers and their models."""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
    
    async def detect_providers(self) -> Dict[str, any]:
        """Auto-detect all available providers."""
        results = {}
        
        # Check Ollama
        results["ollama"] = await self._check_ollama()
        
        # Check OpenAI
        results["openai"] = await self._check_openai()
        
        # Check OpenRouter
        results["openrouter"] = await self._check_openrouter()
        
        return results
    
    def _check_ollama_simple(self) -> Dict:
        """Check Ollama using curl (fallback)."""
        try:
            result = subprocess.run(
                ["curl", "-s", "http://localhost:11434/api/tags"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                models = data.get("models", [])
                
                chat_models = []
                for model in models:
                    name = model["name"]
                    size = model.get("size", 0) / (1024**3)
                    
                    if self._is_chat_compatible(name):
                        chat_models.append({
                            "name": name,
                            "size_gb": round(size, 1),
                            "digest": model.get("digest", "")[:12],
                            "tags": self._get_model_tags(name)
                        })
                
                return {
                    "available": True,
                    "models": chat_models,
                    "url": "http://localhost:11434",
                    "error": None
                }
        except Exception as e:
            return {
                "available": False,
                "models": [],
                "url": "http://localhost:11434",
                "error": str(e)
            }
    
    async def _check_ollama(self) -> Dict:
        """Check if Ollama is running and list models."""
        if HTTPX_AVAILABLE:
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get("http://localhost:11434/api/tags")
                    if response.status_code == 200:
                        data = response.json()
                        models = data.get("models", [])
                        
                        chat_models = []
                        for model in models:
                            name = model["name"]
                            size = model.get("size", 0) / (1024**3)
                            
                            if self._is_chat_compatible(name):
                                chat_models.append({
                                    "name": name,
                                    "size_gb": round(size, 1),
                                    "digest": model.get("digest", "")[:12],
                                    "tags": self._get_model_tags(name)
                                })
                        
                        return {
                            "available": True,
                            "models": chat_models,
                            "url": "http://localhost:11434",
                            "error": None
                        }
            except Exception as e:
                return {
                    "available": False,
                    "models": [],
                    "url": "http://localhost:11434",
                    "error": str(e)
                }
        else:
            return self._check_ollama_simple()
    
    def _is_chat_compatible(self, model_name: str) -> bool:
        """Check if model is likely to support chat/function calling."""
        chat_patterns = [
            "llama", "mistral", "glm", "qwen", "codellama", 
            "gemma", "phi", "mixtral", "yi", "deepseek"
        ]
        
        exclude_patterns = [
            "embed", "diffusion", "stable", "clip", "whisper"
        ]
        
        model_lower = model_name.lower()
        
        for pattern in exclude_patterns:
            if pattern in model_lower:
                return False
        
        for pattern in chat_patterns:
            if pattern in model_lower:
                return True
        
        return True
    
    def _get_model_tags(self, model_name: str) -> List[str]:
        """Get descriptive tags for a model."""
        tags = []
        name_lower = model_name.lower()
        
        if "glm" in name_lower:
            tags.append("Chinese")
            tags.append("Multilingual")
        if "code" in name_lower or "codellama" in name_lower:
            tags.append("Coding")
        if "llama" in name_lower:
            tags.append("Popular")
        if "mistral" in name_lower:
            tags.append("Fast")
        if "tiny" in name_lower or "small" in name_lower:
            tags.append("Lightweight")
        if "large" in name_lower or "70b" in name_lower:
            tags.append("Large")
        
        return tags
    
    async def _check_openai(self) -> Dict:
        """Check OpenAI API key."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return {
                "available": False,
                "models": [],
                "error": "No OPENAI_API_KEY found in environment"
            }
        
        # Common OpenAI models (list without API call for simplicity)
        models = [
            {"name": "gpt-4o", "display_name": "GPT-4o", "tag": "Latest"},
            {"name": "gpt-4o-mini", "display_name": "GPT-4o Mini", "tag": "Fast"},
            {"name": "gpt-4-turbo", "display_name": "GPT-4 Turbo", "tag": "Powerful"},
            {"name": "gpt-3.5-turbo", "display_name": "GPT-3.5 Turbo", "tag": "Classic"},
        ]
        
        return {
            "available": True,
            "models": models,
            "error": None
        }
    
    async def _check_openrouter(self) -> Dict:
        """Check OpenRouter API key."""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            return {
                "available": False,
                "models": [],
                "error": "No OPENROUTER_API_KEY found in environment"
            }
        
        # Common OpenRouter models
        models = [
            {"name": "anthropic/claude-3.5-sonnet", "display_name": "Claude 3.5 Sonnet", "tag": "Premium"},
            {"name": "openai/gpt-4o", "display_name": "GPT-4o", "tag": "Latest"},
            {"name": "google/gemini-pro", "display_name": "Gemini Pro", "tag": "Google"},
            {"name": "meta-llama/llama-3.1-70b-instruct", "display_name": "Llama 3.1 70B", "tag": "Open Source"},
        ]
        
        return {
            "available": True,
            "models": models,
            "error": None
        }


def print_simple_header():
    """Print a simple header without Rich."""
    print("\n" + "="*60)
    print("🦀 HermitClaw Setup")
    print("Creating your AI companion")
    print("="*60)


def print_simple_detection(providers: Dict):
    """Print detection results without Rich."""
    print("\n🔍 Detection Results:")
    print("-" * 40)
    
    # Ollama
    ollama = providers.get("ollama") or {}
    if ollama.get("available"):
        print(f"✅ Ollama found at {ollama.get('url', 'localhost:11434')}")
        if ollama.get("models"):
            print(f"📦 {len(ollama['models'])} compatible models available")
    else:
        print("❌ Ollama not detected")
    
    # OpenAI
    openai = providers.get("openai") or {}
    if openai.get("available"):
        print(f"✅ OpenAI API ready ({len(openai['models'])} models)")
    else:
        print("❌ OpenAI: No API key")
    
    # OpenRouter
    openrouter = providers.get("openrouter") or {}
    if openrouter.get("available"):
        print(f"✅ OpenRouter ready ({len(openrouter['models'])} models)")
    else:
        print("❌ OpenRouter: No API key")


def print_simple_provider_selection():
    """Print provider selection without Rich."""
    print("\nSelect Your AI Provider:")
    print("-" * 40)
    print("1. 🔥 Ollama (Local)     - Models on your machine")
    print("2. ☁️ OpenAI              - OpenAI's models")
    print("3. 🌐 OpenRouter          - Many models in one place")
    print("4. ⚙️ Custom URL          - Manual setup")


def print_simple_models(provider: str, providers: Dict):
    """Print models for a provider without Rich."""
    provider_data = providers.get(provider) or {}
    models = provider_data.get("models", [])
    
    if not models:
        print(f"\n❌ No models available for {provider}")
        return
    
    print(f"\n📦 Available Models - {provider.title()}:")
    print("-" * 50)
    
    for i, model in enumerate(models[:10], 1):
        name = model["name"]
        
        if provider == "ollama":
            size = f"{model.get('size_gb', '?')}GB"
            tags = ", ".join(model.get("tags", []))
            
            if "glm-5" in name:
                name = f"🎯 {name}"
            elif "glm-4.7" in name:
                name = f"⭐ {name}"
                
        elif provider in ["openai", "openrouter"]:
            size = model.get("tag", "Cloud")
            tags = model.get("tag", "")
            display_name = model.get("display_name", name)
            name = display_name
        else:
            size = "Unknown"
            tags = ""
        
        print(f"{i:2d}. {name:<25} {size:<8} {tags}")


async def run_simple_tui():
    """Run a simple TUI without external dependencies."""
    print_simple_header()
    
    print("🔍 Detecting AI providers...")
    
    detector = ProviderDetector()
    providers = await detector.detect_providers()
    
    print_simple_detection(providers)
    print_simple_provider_selection()
    
    # Show models for the best available provider
    ollama = providers.get("ollama") or {}
    openai = providers.get("openai") or {}
    openrouter = providers.get("openrouter") or {}
    
    if ollama.get("available"):
        print_simple_models("ollama", providers)
    elif openai.get("available"):
        print_simple_models("openai", providers)
    elif openrouter.get("available"):
        print_simple_models("openrouter", providers)
    else:
        print("\n❌ No providers available. Please install/configure a provider.")
        print("\nSuggestions:")
        print("  - Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh")
        print("  - Set OPENAI_API_KEY=your_key")
        print("  - Set OPENROUTER_API_KEY=your_key")
    
    print("\nOptions:")
    print("[Test Connection] [Save & Start] [Advanced] [Exit]")
    
    return providers


if RICH_AVAILABLE and HTTPX_AVAILABLE:
    # Use the full Rich version if available
    class HermitClawTUI:
        """Beautiful TUI for HermitClaw model selection."""
        
        def __init__(self):
            self.console = Console()
            self.detector = ProviderDetector()
            self.providers = {}
        
        def _create_header(self) -> Panel:
            """Create the header panel."""
            title = Text("🦀 HermitClaw Setup", style="bold coral1")
            subtitle = Text("Creating your AI companion", style="dim")
            
            content = Align.center(title + "\n" + subtitle)
            return Panel(content, box=box.ROUNDED, style="navy_blue")
        
        def _create_detection_status(self) -> Panel:
            """Create provider detection status panel."""
            table = Table(show_header=False, box=None, padding=0)
            table.add_column("Status", style="bold")
            table.add_column("Message", style="white")
            
            ollama = self.providers.get("ollama", {})
            if ollama.get("available"):
                table.add_row("✅", f"Ollama found at {ollama['url']}")
                if ollama.get("models"):
                    table.add_row("📦", f"{len(ollama['models'])} compatible models available")
            else:
                table.add_row("❌", "Ollama not detected")
            
            openai = self.providers.get("openai", {})
            if openai.get("available"):
                table.add_row("✅", f"OpenAI API ready ({len(openai['models'])} models)")
            else:
                table.add_row("❌", "OpenAI: No API key")
            
            openrouter = self.providers.get("openrouter", {})
            if openrouter.get("available"):
                table.add_row("✅", f"OpenRouter ready ({len(openrouter['models'])} models)")
            else:
                table.add_row("❌", "OpenRouter: No API key")
            
            return Panel(table, title="🔍 Detection Results", box=box.ROUNDED)
        
        def _create_provider_selection(self) -> Panel:
            """Create provider selection panel."""
            table = Table(show_header=True, box=box.ROUNDED)
            table.add_column("Provider", style="bold")
            table.add_column("Status", style="cyan")
            table.add_column("Models", style="green")
            
            ollama = self.providers.get("ollama", {})
            ollama_status = "✅ Ready" if ollama.get("available") else "❌ Not found"
            ollama_models = f"{len(ollama.get('models', []))} available" if ollama.get("available") else "N/A"
            table.add_row("🔥 Ollama (Local)", ollama_status, ollama_models)
            
            openai = self.providers.get("openai", {})
            openai_status = "✅ Ready" if openai.get("available") else "🔑 Key needed"
            openai_models = f"{len(openai.get('models', []))} available" if openai.get("available") else "N/A"
            table.add_row("☁️ OpenAI", openai_status, openai_models)
            
            openrouter = self.providers.get("openrouter", {})
            openrouter_status = "✅ Ready" if openrouter.get("available") else "🔑 Key needed"
            openrouter_models = f"{len(openrouter.get('models', []))} available" if openrouter.get("available") else "N/A"
            table.add_row("🌐 OpenRouter", openrouter_status, openrouter_models)
            
            table.add_row("⚙️ Custom URL", "💪 Advanced", "Manual setup")
            
            return Panel(table, title="Select Your AI Provider", box=box.ROUNDED)
        
        async def run(self):
            """Run the complete TUI experience."""
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                
                task = progress.add_task("🔍 Detecting AI providers...", total=4)
                
                self.providers = {}
                
                progress.update(task, description="🔍 Checking Ollama...")
                ollama_result = await self.detector._check_ollama()
                self.providers["ollama"] = ollama_result
                progress.advance(task)
                
                progress.update(task, description="🔍 Checking OpenAI...")
                openai_result = self.detector._check_openai()
                self.providers["openai"] = openai_result
                progress.advance(task)
                
                progress.update(task, description="🔍 Checking OpenRouter...")
                openrouter_result = self.detector._check_openrouter()
                self.providers["openrouter"] = openrouter_result
                progress.advance(task)
                
                progress.update(task, description="✅ Detection complete!")
                progress.advance(task)
            
            # Create the interface
            header = self._create_header()
            detection = self._create_detection_status()
            selection = self._create_provider_selection()
            
            self.console.print()
            self.console.print(header)
            self.console.print()
            self.console.print(detection)
            self.console.print()
            self.console.print(selection)
            
            return self.providers


async def main():
    """Main entry point for the TUI."""
    try:
        if RICH_AVAILABLE and HTTPX_AVAILABLE:
            # Use full Rich version
            tui = HermitClawTUI()
            providers = await tui.run()
        else:
            # Use simple version
            providers = await run_simple_tui()
        
        print(f"\n🎉 Detection complete!")
        available_count = sum(1 for p in (providers or {}).values() if (p or {}).get('available'))
        print(f"Found {available_count} available providers")
        
        # Show a sample of what the config would look like
        ollama = providers.get("ollama") or {}
        if ollama.get("available") and ollama.get("models"):
            best_model = ollama["models"][0]["name"]
            print(f"\n📝 Sample config for Ollama:")
            print(f"provider: 'custom'")
            print(f"model: '{best_model}'")
            print(f"base_url: 'http://localhost:11434/v1'")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())