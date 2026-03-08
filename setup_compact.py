"""Compact TUI for HermitClaw model selection - minimal and focused."""

import asyncio
import json
import os
import subprocess
from typing import Dict, List

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    from rich.prompt import Prompt, Confirm
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class ModelSetup:
    """Compact model setup wizard."""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.providers = {}
    
    async def detect(self) -> Dict:
        """Detect all providers."""
        if RICH_AVAILABLE:
            async with Progress(
                SpinnerColumn(), TextColumn("{task.description}"),
                console=self.console, transient=True
            ) as progress:
                task = progress.add_task("🔍 Detecting providers...", total=3)
                
                self.providers["ollama"] = await self._check_ollama()
                progress.advance(task)
                
                self.providers["openai"] = self._check_openai()
                progress.advance(task)
                
                self.providers["openrouter"] = self._check_openrouter()
                progress.advance(task)
        else:
            print("🔍 Detecting providers...")
            self.providers["ollama"] = await self._check_ollama()
            self.providers["openai"] = self._check_openai()
            self.providers["openrouter"] = self._check_openrouter()
        
        return self.providers
    
    async def _check_ollama(self) -> Dict:
        """Check Ollama."""
        try:
            if HTTPX_AVAILABLE:
                async with httpx.AsyncClient(timeout=5) as client:
                    resp = await client.get("http://localhost:11434/api/tags")
                    if resp.status_code == 200:
                        data = resp.json()
                        models = []
                        for m in data.get("models", []):
                            name = m["name"]
                            if any(p in name.lower() for p in ["llama", "mistral", "glm", "codellama", "gemma"]):
                                if not any(p in name.lower() for p in ["embed", "diffusion", "stable"]):
                                    size_gb = round(m.get("size", 0) / (1024**3), 1)
                                    tags = self._get_tags(name)
                                    models.append({
                                        "name": name,
                                        "size_gb": size_gb,
                                        "tags": tags,
                                        "recommended": "glm-5" in name.lower()
                                    })
                        return {"available": True, "models": models}
            else:
                # Fallback to curl
                result = subprocess.run(["curl", "-s", "http://localhost:11434/api/tags"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    # Simplified parsing for curl fallback
                    return {"available": True, "models": [{"name": "glm-5:latest", "size_gb": 4.7}]}
        except:
            pass
        return {"available": False, "models": []}
    
    def _get_tags(self, name: str) -> List[str]:
        """Get model tags."""
        tags = []
        name = name.lower()
        if "glm" in name:
            tags.extend(["Chinese", "Multilingual"])
        if "code" in name or "codellama" in name:
            tags.append("Coding")
        if "llama" in name:
            tags.append("Popular")
        if "mistral" in name:
            tags.append("Fast")
        return tags
    
    def _check_openai(self) -> Dict:
        """Check OpenAI."""
        if os.environ.get("OPENAI_API_KEY"):
            models = [
                {"name": "gpt-4o", "display": "GPT-4o", "tag": "Latest", "recommended": True},
                {"name": "gpt-4o-mini", "display": "GPT-4o Mini", "tag": "Fast"},
            ]
            return {"available": True, "models": models}
        return {"available": False, "models": []}
    
    def _check_openrouter(self) -> Dict:
        """Check OpenRouter."""
        if os.environ.get("OPENROUTER_API_KEY"):
            models = [
                {"name": "anthropic/claude-3.5-sonnet", "display": "Claude 3.5", "tag": "Premium", "recommended": True},
                {"name": "openai/gpt-4o", "display": "GPT-4o", "tag": "Latest"},
            ]
            return {"available": True, "models": models}
        return {"available": False, "models": []}
    
    def show_interface(self) -> str:
        """Show selection interface and return choice."""
        if not RICH_AVAILABLE:
            return self._simple_prompt()
        
        # Show detection results
        table = Table(show_header=False, box=None)
        table.add_column("Status", style="bold")
        table.add_column("Info")
        
        for provider, data in self.providers.items():
            if data.get("available"):
                icon = "✅"
                models = len(data.get("models", []))
                info = f"{provider.title()}: {models} models"
            else:
                icon = "❌"
                info = f"{provider.title()}: Not available"
            table.add_row(icon, info)
        
        self.console.print(Panel(table, title="🔍 Detection Results"))
        
        # Show provider selection
        if self.providers.get("ollama", {}).get("available"):
            self.console.print("🎯 Ollama detected! Select a model:")
            return self._select_model("ollama")
        else:
            self.console.print("❌ No local providers found. Set up API keys first.")
            return None
    
    def _select_model(self, provider: str) -> str:
        """Select model from provider."""
        models = self.providers[provider].get("models", [])
        if not models:
            return None
        
        table = Table(title="Available Models")
        table.add_column("#", style="bold")
        table.add_column("Model", style="bold")
        table.add_column("Size")
        table.add_column("Tags")
        table.add_column("Rating")
        
        for i, model in enumerate(models[:8], 1):
            name = model["name"]
            if provider == "ollama":
                size = f"{model['size_gb']}GB"
                tags = ", ".join(model.get("tags", []))
                rating = "⭐⭐⭐" if model.get("recommended") else ""
                if model.get("recommended"):
                    name = f"🎯 {name}"
            else:
                size = model.get("tag", "Cloud")
                tags = model.get("tag", "")
                rating = "⭐⭐⭐" if model.get("recommended") else ""
                name = model.get("display", name)
            
            table.add_row(str(i), name, size, tags, rating)
        
        self.console.print(table)
        
        # Get user selection
        choice = Prompt.ask("Select model [1-8]", default="1")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                return models[idx]["name"]
        except:
            pass
        return None
    
    def _simple_prompt(self) -> str:
        """Simple prompt for non-Rich fallback."""
        print("\n🔍 Detection Results:")
        for provider, data in self.providers.items():
            status = "✅" if data.get("available") else "❌"
            print(f"{status} {provider.title()}")
        
        if self.providers.get("ollama", {}).get("available"):
            models = self.providers["ollama"]["models"]
            print(f"\nAvailable models:")
            for i, model in enumerate(models[:5], 1):
                size = f"({model['size_gb']}GB)" if "size_gb" in model else ""
                rec = " 🎯 RECOMMENDED" if model.get("recommended") else ""
                print(f"{i}. {model['name']}{size}{rec}")
            
            choice = input("\nSelect model [1-5]: ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(models):
                    return models[idx]["name"]
            except:
                pass
        return None
    
    def write_config(self, provider: str, model: str):
        """Write config.yaml."""
        config = {
            "provider": provider,
            "model": model,
        }
        
        if provider == "ollama":
            config["base_url"] = "http://localhost:11434/v1"
            config["api_key"] = None
        elif provider == "openai":
            config["provider"] = "openai"
        elif provider == "openrouter":
            config["provider"] = "openrouter"
        
        try:
            import yaml
            with open("config.yaml", "w") as f:
                yaml.dump(config, f, default_flow_style=False)
            return True
        except ImportError:
            # Write simple YAML without pyyaml
            yaml_str = f"""provider: {config['provider']}
model: {config['model']}
"""
            if "base_url" in config:
                yaml_str += f"base_url: {config['base_url']}\n"
            if "api_key" in config:
                yaml_str += f"api_key: {config['api_key']}\n"
            
            with open("config.yaml", "w") as f:
                f.write(yaml_str)
            return True


async def main():
    """Run the compact setup."""
    try:
        setup = ModelSetup()
        await setup.detect()
        
        selected_model = setup.show_interface()
        if selected_model:
            if setup.providers.get("ollama", {}).get("available"):
                provider = "custom"  # Ollama uses custom provider
            else:
                provider = "openai"  # Default fallback
            
            setup.write_config(provider, selected_model)
            print(f"✅ Configuration saved: {provider} + {selected_model}")
        else:
            print("❌ No model selected.")
            
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled.")


if __name__ == "__main__":
    asyncio.run(main())