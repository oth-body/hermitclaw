#!/usr/bin/env python3
"""Test the TUI with mock data to show the full experience."""

import asyncio
import sys
import os

# Add the current directory to path so we can import our TUI
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tui_setup_simple import ProviderDetector, print_simple_header, print_simple_detection, print_simple_provider_selection, print_simple_models


class MockProviderDetector(ProviderDetector):
    """Mock detector that returns fake data for testing."""
    
    async def _check_ollama(self):
        """Return mock Ollama data."""
        return {
            "available": True,
            "models": [
                {
                    "name": "glm-5:latest",
                    "size_gb": 4.7,
                    "digest": "abc123def456",
                    "tags": ["Chinese", "Multilingual", "Recommended"]
                },
                {
                    "name": "glm-4.7:latest", 
                    "size_gb": 4.1,
                    "digest": "def456abc123",
                    "tags": ["Chinese", "Multilingual", "Fast"]
                },
                {
                    "name": "llama2:latest",
                    "size_gb": 3.8,
                    "digest": "123abc456def",
                    "tags": ["Popular", "Stable"]
                },
                {
                    "name": "codellama:latest",
                    "size_gb": 3.8,
                    "digest": "456def123abc",
                    "tags": ["Coding", "Specialized"]
                },
                {
                    "name": "mistral:latest",
                    "size_gb": 4.1,
                    "digest": "abc123456def",
                    "tags": ["Fast", "Popular"]
                }
            ],
            "url": "http://localhost:11434",
            "error": None
        }
    
    async def _check_openai(self):
        """Return mock OpenAI data."""
        return {
            "available": False,
            "models": [],
            "error": "No OPENAI_API_KEY found in environment"
        }
    
    async def _check_openrouter(self):
        """Return mock OpenRouter data."""
        return {
            "available": False,
            "models": [],
            "error": "No OPENROUTER_API_KEY found in environment"
        }


async def demo_tui():
    """Run a demo of the TUI with mock data."""
    print_simple_header()
    
    print("🔍 Detecting AI providers...")
    
    detector = MockProviderDetector()
    providers = await detector.detect_providers()
    
    print_simple_detection(providers)
    print_simple_provider_selection()
    
    # Show models for Ollama since it's available
    print_simple_models("ollama", providers)
    
    print("\n🎉 Demo complete!")
    print("This is what users would see with Ollama installed and GLM models available.")
    
    # Show sample config
    ollama = providers.get("ollama") or {}
    if ollama.get("available") and ollama.get("models"):
        best_model = "glm-5:latest"  # Pick the best one
        print(f"\n📝 Recommended config for best experience:")
        print("provider: 'custom'")
        print(f"model: '{best_model}'")
        print("base_url: 'http://localhost:11434/v1'")
        print("api_key: null")
        print("\nThis would be written to config.yaml automatically!")


if __name__ == "__main__":
    asyncio.run(demo_tui())