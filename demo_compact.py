"""Demo the compact TUI with mock Ollama data."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from setup_compact import ModelSetup


class MockModelSetup(ModelSetup):
    """Mock setup with Ollama data."""
    
    async def _check_ollama(self):
        return {
            "available": True,
            "models": [
                {"name": "glm-5:latest", "size_gb": 4.7, "tags": ["Chinese", "Multilingual"], "recommended": True},
                {"name": "glm-4.7:latest", "size_gb": 4.1, "tags": ["Chinese", "Multilingual", "Fast"], "recommended": False},
                {"name": "llama2:latest", "size_gb": 3.8, "tags": ["Popular", "Stable"], "recommended": False},
                {"name": "codellama:latest", "size_gb": 3.8, "tags": ["Coding"], "recommended": False},
                {"name": "mistral:latest", "size_gb": 4.1, "tags": ["Fast", "Popular"], "recommended": False},
            ]
        }


async def demo():
    setup = MockModelSetup()
    await setup.detect()
    
    selected_model = setup.show_interface()
    if selected_model:
        print(f"✅ Would write config: custom + {selected_model}")
    else:
        print("❌ No model selected.")


if __name__ == "__main__":
    asyncio.run(demo())