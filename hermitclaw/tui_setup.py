#!/usr/bin/env python3
"""HermitClaw Model Selection TUI - Beautiful Rich Version.

This module provides an interactive terminal interface for selecting and configuring
AI models in HermitClaw. It automatically detects available providers (Ollama, OpenAI,
OpenRouter) and guides users through model selection with a beautiful interface.

Usage:
    python -m hermitclaw.tui_setup    # Run the TUI setup wizard
    python -m hermitclaw.tui_setup --demo  # Run with mock data for testing
"""

import asyncio
import json
import os
import sys
import time
import subprocess
from typing import Dict, List, Optional, Tuple

# Rich imports for beautiful terminal UI
try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.align import Align
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    from rich.prompt import Prompt, Confirm
    from rich.live import Live
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# HTTP client for API calls
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class ProviderDetector:
    """Detects available AI providers and their models with rich feedback."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    async def detect_providers(self, show_progress: bool = True) -> Dict[str, any]:
        """Auto-detect all available providers with progress animation."""
        if show_progress and RICH_AVAILABLE:
            return await self._detect_with_progress()
        else:
            # Simple detection without progress
            results = {}
            results["ollama"] = await self._check_ollama()
            results["openai"] = await self._check_openai()
            results["openrouter"] = await self._check_openrouter()
            results["zai"] = await self._check_zai()
            return results
    
    async def _detect_with_progress(self) -> Dict[str, any]:
        """Run detection with Rich progress animation."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            
            task = progress.add_task("🔍 Detecting AI providers...", total=5)
            
            results = {}
            
            # Check Ollama
            progress.update(task, description="🔍 Checking Ollama...")
            results["ollama"] = await self._check_ollama()
            progress.advance(task)
            
            # Check OpenAI
            progress.update(task, description="🔍 Checking OpenAI...")
            results["openai"] = await self._check_openai()
            progress.advance(task)
            
            # Check OpenRouter
            progress.update(task, description="🔍 Checking OpenRouter...")
            results["openrouter"] = await self._check_openrouter()
            progress.advance(task)
            
            # Check z.ai
            progress.update(task, description="🔍 Checking z.ai...")
            results["zai"] = await self._check_zai()
            progress.advance(task)
            
            progress.update(task, description="✅ Detection complete!", completed=5)
            
        return results
    
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
                                    "tags": self._get_model_tags(name),
                                    "recommended": self._is_recommended(name)
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
            # Fallback to curl
            return self._check_ollama_curl()
    
    def _check_ollama_curl(self) -> Dict:
        """Check Ollama using curl (fallback when httpx not available)."""
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
                            "tags": self._get_model_tags(name),
                            "recommended": self._is_recommended(name)
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
        
        # Check exclusions first
        for pattern in exclude_patterns:
            if pattern in model_lower:
                return False
        
        # Check for chat patterns
        for pattern in chat_patterns:
            if pattern in model_lower:
                return True
        
        return True
    
    def _is_recommended(self, model_name: str) -> bool:
        """Check if model is recommended for HermitClaw."""
        name_lower = model_name.lower()
        
        # Highly recommended models
        if "glm-5" in name_lower or "glm5" in name_lower:
            return True
        if "glm-4.7" in name_lower or "glm4" in name_lower:
            return True
        if "llama-3.1" in name_lower or "llama3" in name_lower:
            return True
        
        return False
    
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
        
        # Common OpenAI models
        models = [
            {"name": "gpt-4o", "display_name": "GPT-4o", "tag": "Latest", "recommended": True},
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
            {"name": "anthropic/claude-3.5-sonnet", "display_name": "Claude 3.5 Sonnet", "tag": "Premium", "recommended": True},
            {"name": "openai/gpt-4o", "display_name": "GPT-4o", "tag": "Latest"},
            {"name": "google/gemini-pro", "display_name": "Gemini Pro", "tag": "Google"},
            {"name": "meta-llama/llama-3.1-70b-instruct", "display_name": "Llama 3.1 70B", "tag": "Open Source"},
        ]
        
        return {
            "available": True,
            "models": models,
            "error": None
        }
    
    async def _check_zai(self) -> Dict:
        """Check z.ai / Zhipu AI API key."""
        api_key = os.environ.get("Z_AI_API_KEY")
        if not api_key:
            return {
                "available": False,
                "models": [],
                "error": "No Z_AI_API_KEY found in environment"
            }
        
        # GLM models available on z.ai
        models = [
            {"name": "glm-z1-airx", "display_name": "GLM Z1 AirX", "tag": "Fastest", "recommended": True},
            {"name": "glm-z1-air", "display_name": "GLM Z1 Air", "tag": "Fast"},
            {"name": "glm-z1-flash", "display_name": "GLM Z1 Flash", "tag": "Balanced"},
            {"name": "glm-4.5", "display_name": "GLM 4.5", "tag": "Flagship"},
            {"name": "glm-4-plus", "display_name": "GLM 4 Plus", "tag": "Enhanced"},
            {"name": "glm-4-flash", "display_name": "GLM 4 Flash", "tag": "Quick"},
        ]
        
        return {
            "available": True,
            "models": models,
            "error": None
        }


class HermitClawTUI:
    """Beautiful TUI for HermitClaw model selection."""
    
    def __init__(self):
        if not RICH_AVAILABLE:
            raise ImportError("Rich library is required. Install with: pip install rich")
        
        self.console = Console()
        self.detector = ProviderDetector(self.console)
        self.providers = {}
        self.selected_provider = None
        self.selected_model = None
    
    def _create_header(self) -> Panel:
        """Create the beautiful header panel."""
        title = Text("🦀 HermitClaw Setup", style="bold coral1")
        subtitle = Text("Creating your AI companion", style="dim")
        
        content = Align.center(title + "\n" + subtitle)
        return Panel(content, box=box.ROUNDED, border_style="bright_blue")
    
    def _create_detection_status(self) -> Panel:
        """Create provider detection status panel."""
        table = Table(show_header=False, box=None, padding=0)
        table.add_column("Status", style="bold", width=4)
        table.add_column("Message", style="white")
        
        # Ollama status
        ollama = self.providers.get("ollama") or {}
        if ollama.get("available"):
            table.add_row("✅", f"Ollama found at {ollama.get('url', 'localhost:11434')}")
            if ollama.get("models"):
                table.add_row("📦", f"{len(ollama['models'])} compatible models available")
                # Show recommended models
                recommended = [m for m in ollama['models'] if m.get('recommended')]
                if recommended:
                    model_names = [m['name'] for m in recommended[:2]]
                    table.add_row("⭐", f"Recommended: {', '.join(model_names)}")
        else:
            table.add_row("❌", "Ollama not detected")
            if ollama.get("error"):
                error_msg = ollama['error'][:40] + "..." if len(ollama['error']) > 40 else ollama['error']
                table.add_row("", f"  └─ {error_msg}")
        
        # OpenAI status
        openai = self.providers.get("openai") or {}
        if openai.get("available"):
            table.add_row("✅", f"OpenAI API ready ({len(openai['models'])} models)")
        else:
            table.add_row("❌", "OpenAI: No API key")
        
        # OpenRouter status
        openrouter = self.providers.get("openrouter") or {}
        if openrouter.get("available"):
            table.add_row("✅", f"OpenRouter ready ({len(openrouter['models'])} models)")
        else:
            table.add_row("❌", "OpenRouter: No API key")
        
        # z.ai status
        zai = self.providers.get("zai") or {}
        if zai.get("available"):
            table.add_row("✅", f"z.ai ready ({len(zai['models'])} models)")
        else:
            table.add_row("❌", "z.ai: No API key")
        
        return Panel(table, title="🔍 Detection Results", box=box.ROUNDED, border_style="cyan")
    
    def _create_provider_selection(self) -> Panel:
        """Create provider selection panel."""
        table = Table(show_header=True, box=box.ROUNDED, title_style="bold")
        table.add_column("Provider", style="bold", width=20)
        table.add_column("Status", style="cyan", width=12)
        table.add_column("Models", style="green", width=15)
        table.add_column("Action", style="yellow", width=10)
        
        # Ollama
        ollama = self.providers.get("ollama") or {}
        ollama_status = "✅ Ready" if ollama.get("available") else "❌ Not found"
        ollama_models = f"{len(ollama.get('models', []))} available" if ollama.get("available") else "N/A"
        ollama_action = "RECOMMENDED" if ollama.get("available") else "Install"
        table.add_row("🔥 Ollama (Local)", ollama_status, ollama_models, ollama_action)
        
        # OpenAI
        openai = self.providers.get("openai") or {}
        openai_status = "✅ Ready" if openai.get("available") else "🔑 Key needed"
        openai_models = f"{len(openai.get('models', []))} available" if openai.get("available") else "N/A"
        openai_action = "Configure" if openai.get("available") else "Set API key"
        table.add_row("☁️ OpenAI", openai_status, openai_models, openai_action)
        
        # OpenRouter
        openrouter = self.providers.get("openrouter") or {}
        openrouter_status = "✅ Ready" if openrouter.get("available") else "🔑 Key needed"
        openrouter_models = f"{len(openrouter.get('models', []))} available" if openrouter.get("available") else "N/A"
        openrouter_action = "Configure" if openrouter.get("available") else "Set API key"
        table.add_row("🌐 OpenRouter", openrouter_status, openrouter_models, openrouter_action)
        
        # z.ai / Zhipu AI
        zai = self.providers.get("zai") or {}
        zai_status = "✅ Ready" if zai.get("available") else "🔑 Key needed"
        zai_models = f"{len(zai.get('models', []))} available" if zai.get("available") else "N/A"
        zai_action = "Configure" if zai.get("available") else "Set API key"
        table.add_row("🤖 z.ai (Zhipu)", zai_status, zai_models, zai_action)
        
        table.add_row("⚙️ Custom URL", "💪 Advanced", "Manual setup", "Configure")
        
        return Panel(table, title="Select Your AI Provider", box=box.ROUNDED, border_style="green")
    
    def _create_model_selection(self, provider: str) -> Panel:
        """Create model selection panel for a provider."""
        provider_data = self.providers.get(provider) or {}
        models = provider_data.get("models", [])
        
        if not models:
            return Panel(
                Text("No models available for this provider", style="red"),
                title=f"📦 Models - {provider.title()}",
                box=box.ROUNDED,
                border_style="red"
            )
        
        table = Table(show_header=True, box=box.ROUNDED, title_style="bold")
        table.add_column("Model", style="bold", width=25)
        table.add_column("Size", style="cyan", width=8)
        table.add_column("Tags", style="green", width=20)
        table.add_column("Rating", style="yellow", width=10)
        
        # Sort models: recommended first, then by name
        def sort_key(model):
            is_rec = model.get('recommended', False)
            name = model.get('name', '')
            return (not is_rec, name.lower())
        
        sorted_models = sorted(models, key=sort_key)
        
        for model in sorted_models[:10]:  # Show first 10 models
            name = model["name"]
            
            if provider == "ollama":
                size = f"{model.get('size_gb', '?')}GB"
                tags = ", ".join(model.get("tags", []))
                
                # Add rating/star for recommended models
                if model.get("recommended"):
                    if "glm-5" in name:
                        rating = "⭐⭐⭐"
                        name = f"🎯 {name}"
                    elif "glm-4.7" in name:
                        rating = "⭐⭐"
                        name = f"⭐ {name}"
                    else:
                        rating = "⭐"
                        name = f"✓ {name}"
                else:
                    rating = ""
                    
            elif provider in ["openai", "openrouter"]:
                size = model.get("tag", "Cloud")
                tags = model.get("tag", "")
                display_name = model.get("display_name", name)
                name = display_name
                
                if model.get("recommended"):
                    rating = "⭐⭐⭐"
                    name = f"🎯 {name}"
                else:
                    rating = ""
            else:
                size = "Unknown"
                tags = ""
                rating = ""
            
            table.add_row(name, size, tags, rating)
        
        return Panel(table, title=f"📦 Available Models - {provider.title()}", box=box.ROUNDED, border_style="magenta")
    
    def _create_action_panel(self) -> Panel:
        """Create action button panel."""
        actions = [
            "[bold green]1.[/bold green] Test Connection",
            "[bold blue]2.[/bold blue] Save & Start",
            "[bold yellow]3.[/bold yellow] Advanced Config",
            "[bold red]4.[/bold red] Exit"
        ]
        
        content = "  ".join(actions)
        return Panel(
            Align.center(content),
            box=box.ROUNDED,
            border_style="white"
        )
    
    def _create_config_preview(self) -> Panel:
        """Show what the config will look like."""
        if not self.selected_provider or not self.selected_model:
            return Panel(
                Text("Select a provider and model first", style="dim"),
                title="📝 Config Preview",
                box=box.ROUNDED,
                border_style="gray"
            )
        
        if self.selected_provider == "ollama":
            config_text = f"""provider: 'custom'
model: '{self.selected_model}'
base_url: 'http://localhost:11434/v1'
api_key: null
# embedding_model: 'nomic-embed-text'  # Recommended for local use"""
        elif self.selected_provider == "openai":
            config_text = f"""provider: 'openai'
model: '{self.selected_model}'
api_key: 'sk-•••••••••••••••••'  # Set via OPENAI_API_KEY
# base_url: null"""
        elif self.selected_provider == "openrouter":
            config_text = f"""provider: 'openrouter'
model: '{self.selected_model}'
api_key: 'sk-or-•••••••••••••••••'  # Set via OPENROUTER_API_KEY
# base_url: null"""
        elif self.selected_provider == "zai":
            config_text = f"""provider: 'custom'
model: '{self.selected_model}'
base_url: 'https://api.z.ai/api/paas/v4'  # or /api/coding/paas/v4
api_key: '••••••••••••••••••••'  # Set via Z_AI_API_KEY
# embedding_model: 'embedding-3'"""
        else:
            config_text = "# Custom configuration - fill in your details"
        
        return Panel(
            Text(config_text, style="cyan"),
            title="📝 Config Preview",
            box=box.ROUNDED,
            border_style="cyan"
        )
    
    async def run(self) -> Dict:
        """Run the complete TUI experience."""
        # Run detection
        self.providers = await self.detector.detect_providers()
        
        # Create the main layout
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=5),
            Layout(name="body"),
            Layout(name="footer", size=7)
        )
        
        layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=2)
        )
        
        layout["right"].split_column(
            Layout(name="provider", size=12),
            Layout(name="models"),
            Layout(name="actions", size=5)
        )
        
        # Add content to panels
        layout["header"].update(self._create_header())
        layout["left"].update(self._create_detection_status())
        layout["right"]["provider"].update(self._create_provider_selection())
        layout["right"]["actions"].update(self._create_action_panel())
        
        # Show models for the best available provider
        best_provider = self._get_best_provider()
        if best_provider:
            layout["right"]["models"].update(self._create_model_selection(best_provider))
            self.selected_provider = best_provider
            # Auto-select the best model
            best_model = self._get_best_model(best_provider)
            if best_model:
                self.selected_model = best_model
        else:
            layout["right"]["models"].update(Panel(
                Text("❌ No providers available. Please install/configure a provider.", style="red"),
                title="No Models Available",
                box=box.ROUNDED,
                border_style="red"
            ))
        
        # Add config preview to footer
        layout["footer"].split_row(
            Layout(name="config"),
            Layout(name="help", size=25)
        )
        layout["footer"]["config"].update(self._create_config_preview())
        
        # Help panel
        help_text = """[bold]Tips:[/bold]
• Ollama: Local & private
• GLM-5: Best for coding
• Configure API keys in .env"""
        layout["footer"]["help"].update(Panel(
            Text(help_text, style="dim"),
            title="💡 Help",
            box=box.ROUNDED,
            border_style="gray"
        ))
        
        # Display the interface
        self.console.print("\n")
        self.console.print(layout)
        
        return self.providers
    
    def _get_best_provider(self) -> Optional[str]:
        """Choose the best available provider."""
        # Priority: Ollama > OpenAI > OpenRouter > z.ai
        for provider in ["ollama", "openai", "openrouter", "zai"]:
            if self.providers.get(provider, {}).get("available"):
                return provider
        return None
    
    def _get_best_model(self, provider: str) -> Optional[str]:
        """Choose the best model for a provider."""
        models = self.providers.get(provider, {}).get("models", [])
        if not models:
            return None
        
        # Prioritize recommended models
        recommended = [m for m in models if m.get("recommended")]
        if recommended:
            # Prefer GLM-5 if available
            for model in recommended:
                if "glm-5" in model.get("name", "").lower():
                    return model["name"]
            return recommended[0]["name"]
        
        return models[0]["name"]


async def main():
    """Main entry point for the TUI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="HermitClaw Model Selection TUI")
    parser.add_argument("--demo", action="store_true", help="Run with mock data for testing")
    args = parser.parse_args()
    
    try:
        if not RICH_AVAILABLE:
            print("❌ Rich library is required. Install with:")
            print("   pip install rich")
            print("   pip install httpx")
            return
        
        if args.demo:
            # Run with mock data
            from demo_tui import MockProviderDetector
            detector = MockProviderDetector()
            providers = await detector.detect_providers()
        else:
            # Run real detection
            tui = HermitClawTUI()
            providers = await tui.run()
        
        available_count = sum(1 for p in (providers or {}).values() if (p or {}).get('available'))
        print(f"\n🎉 Detection complete! Found {available_count} available providers.")
        
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())