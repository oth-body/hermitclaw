"""Beautiful TUI for HermitClaw model selection and configuration."""

import asyncio
import json
import os
import sys
import time
from typing import Dict, List, Optional, Tuple

import httpx
from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich.align import Align


class ProviderDetector:
    """Detects available AI providers and their models."""
    
    def __init__(self):
        self.console = Console()
    
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
    
    async def _check_ollama(self) -> Dict:
        """Check if Ollama is running and list models."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                # Check if Ollama is running
                response = await client.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    
                    # Filter for chat-compatible models
                    chat_models = []
                    for model in models:
                        name = model["name"]
                        size = model.get("size", 0) / (1024**3)  # Convert to GB
                        
                        # Filter models that support chat/function calling
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
    
    def _is_chat_compatible(self, model_name: str) -> bool:
        """Check if model is likely to support chat/function calling."""
        # Common chat model patterns
        chat_patterns = [
            "llama", "mistral", "glm", "qwen", "codellama", 
            "gemma", "phi", "mixtral", "yi", "deepseek"
        ]
        
        # Exclude obvious non-chat models
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
        
        # Default to True for unknown models (let user try)
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
        """Check OpenAI API key and list available models."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return {
                "available": False,
                "models": [],
                "error": "No OPENAI_API_KEY found in environment"
            }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    
                    # Common OpenAI models
                    model_list = [
                        {"id": "gpt-4o", "name": "GPT-4o", "tag": "Latest"},
                        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "tag": "Fast"},
                        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "tag": "Powerful"},
                        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "tag": "Classic"},
                    ]
                    
                    for model_info in model_list:
                        if any(m["id"] == model_info["id"] for m in data.get("data", [])):
                            models.append({
                                "name": model_info["id"],
                                "display_name": model_info["name"],
                                "tag": model_info["tag"],
                                "provider": "openai"
                            })
                    
                    return {
                        "available": True,
                        "models": models,
                        "error": None
                    }
        except Exception as e:
            return {
                "available": False,
                "models": [],
                "error": f"API error: {str(e)}"
            }
    
    async def _check_openrouter(self) -> Dict:
        """Check OpenRouter API key and list models."""
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            return {
                "available": False,
                "models": [],
                "error": "No OPENROUTER_API_KEY found in environment"
            }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    
                    # Get top models for display
                    top_models = data.get("data", [])[:10]  # Show first 10
                    for model in top_models:
                        models.append({
                            "name": model["id"],
                            "display_name": model["name"],
                            "pricing": model.get("pricing", {}),
                            "provider": "openrouter"
                        })
                    
                    return {
                        "available": True,
                        "models": models,
                        "error": None
                    }
        except Exception as e:
            return {
                "available": False,
                "models": [],
                "error": f"API error: {str(e)}"
            }


class HermitClawTUI:
    """Beautiful TUI for HermitClaw model selection."""
    
    def __init__(self):
        self.console = Console()
        self.detector = ProviderDetector()
        self.providers = {}
        self.selected_provider = None
        self.selected_model = None
    
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
        
        # Ollama status
        ollama = self.providers.get("ollama", {})
        if ollama.get("available"):
            table.add_row(
                "✅", 
                f"Ollama found at {ollama['url']}"
            )
            if ollama.get("models"):
                table.add_row(
                    "📦", 
                    f"{len(ollama['models'])} compatible models available"
                )
        else:
            table.add_row("❌", "Ollama not detected")
            if ollama.get("error"):
                table.add_row("", f"  └─ {ollama['error'][:50]}...")
        
        # OpenAI status
        openai = self.providers.get("openai", {})
        if openai.get("available"):
            table.add_row("✅", f"OpenAI API ready ({len(openai['models'])} models)")
        else:
            table.add_row("❌", "OpenAI: No API key")
        
        # OpenRouter status
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
        
        # Ollama
        ollama = self.providers.get("ollama", {})
        ollama_status = "✅ Ready" if ollama.get("available") else "❌ Not found"
        ollama_models = f"{len(ollama.get('models', []))} available" if ollama.get("available") else "N/A"
        table.add_row("🔥 Ollama (Local)", ollama_status, ollama_models)
        
        # OpenAI
        openai = self.providers.get("openai", {})
        openai_status = "✅ Ready" if openai.get("available") else "🔑 Key needed"
        openai_models = f"{len(openai.get('models', []))} available" if openai.get("available") else "N/A"
        table.add_row("☁️ OpenAI", openai_status, openai_models)
        
        # OpenRouter
        openrouter = self.providers.get("openrouter", {})
        openrouter_status = "✅ Ready" if openrouter.get("available") else "🔑 Key needed"
        openrouter_models = f"{len(openrouter.get('models', []))} available" if openrouter.get("available") else "N/A"
        table.add_row("🌐 OpenRouter", openrouter_status, openrouter_models)
        
        table.add_row("⚙️ Custom URL", "💪 Advanced", "Manual setup")
        
        return Panel(table, title="Select Your AI Provider", box=box.ROUNDED)
    
    def _create_model_selection(self, provider: str) -> Panel:
        """Create model selection panel for a provider."""
        provider_data = self.providers.get(provider, {})
        models = provider_data.get("models", [])
        
        if not models:
            return Panel(
                Text("No models available for this provider", style="red"),
                title=f"📦 Models - {provider.title()}",
                box=box.ROUNDED
            )
        
        table = Table(show_header=True, box=box.ROUNDED)
        table.add_column("Model", style="bold")
        table.add_column("Size", style="cyan")
        table.add_column("Tags", style="green")
        
        for model in models[:10]:  # Show first 10 models
            name = model["name"]
            
            if provider == "ollama":
                size = f"{model.get('size_gb', '?')}GB"
                tags = ", ".join(model.get("tags", []))
                
                # Add recommendation for GLM models
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
            
            table.add_row(name, size, tags)
        
        return Panel(table, title=f"📦 Available Models - {provider.title()}", box=box.ROUNDED)
    
    def _create_layout(self) -> Layout:
        """Create the main TUI layout."""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=5),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["header"].update(self._create_header())
        layout["footer"].update(Panel(
            Text("[Test Connection] [Save & Start] [Advanced] [Exit]", style="bold"),
            box=box.ROUNDED
        ))
        
        return layout
    
    async def run_detection(self) -> Dict:
        """Run provider detection with progress animation."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            
            task = progress.add_task("🔍 Detecting AI providers...", total=4)
            
            self.providers = {}
            
            # Check Ollama
            progress.update(task, description="🔍 Checking Ollama...")
            ollama_result = await self.detector._check_ollama()
            self.providers["ollama"] = ollama_result
            progress.advance(task)
            
            # Check OpenAI
            progress.update(task, description="🔍 Checking OpenAI...")
            openai_result = await self.detector._check_openai()
            self.providers["openai"] = openai_result
            progress.advance(task)
            
            # Check OpenRouter
            progress.update(task, description="🔍 Checking OpenRouter...")
            openrouter_result = await self.detector._check_openrouter()
            self.providers["openrouter"] = openrouter_result
            progress.advance(task)
            
            progress.update(task, description="✅ Detection complete!")
            progress.advance(task)
        
        return self.providers
    
    async def run(self):
        """Run the complete TUI experience."""
        # Run detection first
        await self.run_detection()
        
        # Create and display the main interface
        layout = self._create_layout()
        
        layout["left"].update(self._create_detection_status())
        layout["right"].split_column(
            Layout(name="provider", size=12),
            Layout(name="models")
        )
        layout["right"]["provider"].update(self._create_provider_selection())
        
        # Show models for the best available provider
        if self.providers.get("ollama", {}).get("available"):
            layout["right"]["models"].update(self._create_model_selection("ollama"))
        elif self.providers.get("openai", {}).get("available"):
            layout["right"]["models"].update(self._create_model_selection("openai"))
        elif self.providers.get("openrouter", {}).get("available"):
            layout["right"]["models"].update(self._create_model_selection("openrouter"))
        else:
            layout["right"]["models"].update(Panel(
                Text("No providers available. Please install/configure a provider.", style="red"),
                title="❌ No Models Available",
                box=box.ROUNDED
            ))
        
        # Display the interface
        self.console.print(layout)
        
        return self.providers


async def main():
    """Main entry point for the TUI."""
    try:
        # Check if we have the required dependencies
        import rich
        import httpx
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("Please install with: pip install rich httpx")
        return
    
    # Run the TUI
    tui = HermitClawTUI()
    providers = await tui.run()
    
    # For now, just show the results
    print(f"\n🎉 Detection complete!")
    print(f"Found {sum(1 for p in providers.values() if p.get('available'))} available providers")


if __name__ == "__main__":
    asyncio.run(main())