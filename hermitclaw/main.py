"""Entry point — multi-crab discovery + onboarding + starts the server."""

import glob
import json
import logging
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import uvicorn
from hermitclaw.brain import Brain
from hermitclaw.config import config
from hermitclaw.identity import load_identity_from, create_identity
from hermitclaw.server import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))


def _crab_id_from_box(box_path: str) -> str:
    """Derive crab ID from box directory name: coral_box -> coral."""
    dirname = os.path.basename(box_path)
    if dirname.endswith("_box"):
        return dirname[:-4]
    return dirname


def _discover_crabs() -> dict[str, Brain]:
    """Discover all *_box/ dirs, migrate legacy environment/, return brains dict."""
    brains: dict[str, Brain] = {}

    # Migrate legacy environment/ if found
    legacy = os.path.join(PROJECT_ROOT, "environment")
    legacy_identity = os.path.join(legacy, "identity.json")
    if os.path.isfile(legacy_identity):
        with open(legacy_identity, "r") as f:
            identity = json.load(f)
        name = identity.get("name", "crab").lower()
        new_path = os.path.join(PROJECT_ROOT, f"{name}_box")
        print(f"\n  Migrating environment/ -> {name}_box/...")
        shutil.move(legacy, new_path)

    # Scan for *_box/ directories
    pattern = os.path.join(PROJECT_ROOT, "*_box")
    boxes = sorted(p for p in glob.glob(pattern) if os.path.isdir(p))

    for box_path in boxes:
        identity = load_identity_from(box_path)
        if not identity:
            continue
        crab_id = _crab_id_from_box(box_path)
        brain = Brain(identity, box_path)
        brains[crab_id] = brain

    return brains


def _check_config_and_setup():
    """Check if config exists and run setup if needed."""
    config_path = os.path.join(PROJECT_ROOT, "config.yaml")
    
    # Check if config exists and is valid
    if os.path.isfile(config_path):
        try:
            with open(config_path, "r") as f:
                import yaml
                config_data = yaml.safe_load(f)
                if config_data.get("provider") and config_data.get("model"):
                    return True  # Config is good
        except Exception:
            pass  # Will fall through to setup
    
    # Run setup
    print("\n  🔧 No valid configuration found. Running setup...")
    try:
        from .tui_setup import HermitClawTUI
        import asyncio
        
        async def run_setup():
            tui = HermitClawTUI()
            await tui.run()
            return True
        
        asyncio.run(run_setup())
        return True
    except ImportError:
        print("  ❌ Rich library not available. Using simple setup...")
        print("  To get the beautiful TUI, install: pip install rich httpx")
        
        # Fallback to basic prompts
        print("\n  Basic Configuration:")
        provider = input("  Provider (openai/ollama/openrouter/custom) > ").strip().lower()
        model = input("  Model name > ").strip()
        base_url = None
        api_key = None
        
        if provider == "ollama":
            base_url = "http://localhost:11434/v1"
        elif provider == "custom":
            base_url = input("  Base URL > ").strip()
        
        if provider not in ["ollama"]:
            api_key = input("  API key (leave blank to set via env) > ").strip() or None
        
        # Write basic config
        config = {
            "provider": provider,
            "model": model,
            "api_key": api_key,
        }
        if base_url:
            config["base_url"] = base_url
        
        import yaml
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        
        print("  ✅ Configuration saved!")
        return True
    except KeyboardInterrupt:
        print("\n  ❌ Setup cancelled.")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="HermitClaw - AI creatures that live on your computer")
    parser.add_argument("--setup", action="store_true", help="Run model setup wizard")
    parser.add_argument("--skip-setup", action="store_true", help="Skip model setup even if no config exists")
    args = parser.parse_args()
    
    # Handle setup flag
    if args.setup:
        try:
            from .tui_setup import HermitClawTUI
            import asyncio
            
            asyncio.run(HermitClawTUI().run())
        except ImportError:
            print("❌ Rich library not available. Install with: pip install rich httpx")
        sys.exit(0)
    
    # Check configuration unless explicitly skipped
    if not args.skip_setup:
        if not _check_config_and_setup():
            sys.exit(1)
    
    # Discover existing crabs
    brains = _discover_crabs()

    if brains:
        names = [b.identity["name"] for b in brains.values()]
        print(f"\n  Found {len(brains)} crab(s): {', '.join(names)}")
        answer = input("  Create a new one? (y/N) > ").strip().lower()
        if answer == "y":
            identity = create_identity()
            crab_id = identity["name"].lower()
            box_path = os.path.join(PROJECT_ROOT, f"{crab_id}_box")
            brain = Brain(identity, box_path)
            brains[crab_id] = brain
    else:
        print("\n  No crabs found. Let's create one!")
        identity = create_identity()
        crab_id = identity["name"].lower()
        box_path = os.path.join(PROJECT_ROOT, f"{crab_id}_box")
        brain = Brain(identity, box_path)
        brains[crab_id] = brain

    # Initialize the app with all brains
    app = create_app(brains)

    names = [b.identity["name"] for b in brains.values()]
    print(f"\n  Starting {len(brains)} crab(s): {', '.join(names)}")
    print(f"  Open http://localhost:8000 to watch them think\n")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
