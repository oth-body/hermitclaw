#!/usr/bin/env python3
"""Interactive model selection launcher for first-time setup."""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Common models by provider
OPENAI_MODELS = [
    ("gpt-4.1", "GPT-4.1 - Latest, best for complex tasks"),
    ("gpt-4.1-mini", "GPT-4.1 Mini - Faster, cheaper"),
    ("gpt-4.1-nano", "GPT-4.1 Nano - Fastest, cheapest"),
    ("gpt-4o", "GPT-4o - Previous generation"),
    ("gpt-4o-mini", "GPT-4o Mini - Budget option"),
]

OPENROUTER_MODELS = [
    ("google/gemini-2.0-flash-001", "Gemini 2.0 Flash - Fast, capable"),
    ("anthropic/claude-3.5-sonnet", "Claude 3.5 Sonnet - Great for coding"),
    ("meta-llama/llama-3.2-90b-vision-instruct", "Llama 3.2 90B - Open source"),
    ("mistralai/mistral-large", "Mistral Large - European LLM"),
    ("deepseek/deepseek-chat", "DeepSeek Chat - Budget friendly"),
]

BEDROCK_MODELS = [
    ("anthropic.claude-3-sonnet-20240229-v1:0", "Claude 3 Sonnet"),
    ("anthropic.claude-3-haiku-20240307-v1:0", "Claude 3 Haiku - Fast"),
    ("meta.llama3-1-70b-instruct-v1:0", "Llama 3.1 70B"),
    ("mistral.mistral-large-2402-v1:0", "Mistral Large"),
]

ZAI_MODELS = [
    ("glm-z1-airx", "GLM Z1 AirX - Fastest, most economical"),
    ("glm-z1-air", "GLM Z1 Air - Fast and efficient"),
    ("glm-z1-flash", "GLM Z1 Flash - Balanced speed and quality"),
    ("glm-z1-flashx", "GLM Z1 FlashX - Enhanced flash model"),
    ("glm-4.5", "GLM 4.5 - Latest flagship model"),
    ("glm-4-plus", "GLM 4 Plus - Enhanced capabilities"),
    ("glm-4-air", "GLM 4 Air - Efficient standard model"),
    ("glm-4-flash", "GLM 4 Flash - Fast responses"),
    ("glm-4-long", "GLM 4 Long - Extended context"),
]

ZAI_REGIONS = [
    ("us", "US Region - api.z.ai"),
    ("cn", "China Region - open.bigmodel.cn"),
]

ZAI_PLAN_TYPES = [
    ("general", "General - Standard API access"),
    ("coding", "Coding - Optimized for code tasks"),
]


def detect_ollama():
    """Check if Ollama is running locally."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode())
            return data.get("models", [])
    except:
        return None


def select_from_list(options, prompt="Select an option"):
    """Display a numbered list and get user selection."""
    print(f"\n{prompt}:\n")
    for i, (value, desc) in enumerate(options, 1):
        print(f"  {i}. {desc}")
    print(f"  0. Back / Cancel")
    
    while True:
        try:
            choice = input("\n> ").strip()
            if choice == "0":
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx][0]
            print("Invalid selection. Try again.")
        except ValueError:
            print("Enter a number.")
        except KeyboardInterrupt:
            print("\nCancelled.")
            sys.exit(0)


def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_path = Path(__file__).parent.parent / ".env"
    env_vars = {}
    
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
    
    return env_vars, env_path


def get_api_key(provider):
    """Prompt for API key if not already set."""
    env_vars, env_path = load_env_file()
    
    env_var_map = {
        "openai": "OPENAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "zai": "Z_AI_API_KEY",
    }
    
    env_var = env_var_map.get(provider)
    
    # Check environment first, then .env file
    existing_key = os.environ.get(env_var) or env_vars.get(env_var)
    
    if existing_key:
        # Mask the key for display
        masked = existing_key[:8] + "•" * 12 + existing_key[-4:] if len(existing_key) > 16 else "•" * 8
        print(f"\n✓ Found existing {env_var}: {masked}")
        
        choice = input("  Keep existing key? (Y/n) > ").strip().lower()
        if choice != "n":
            return None  # Use existing
        
        print(f"\nEnter new {provider} API key:")
    else:
        if provider == "openai":
            print("\nEnter your OpenAI API key (or press Enter to set via environment):")
            print("  Get one at: https://platform.openai.com/api-keys")
        elif provider == "openrouter":
            print("\nEnter your OpenRouter API key (or press Enter to set via environment):")
            print("  Get one at: https://openrouter.ai/keys")
        elif provider == "zai":
            print("\nEnter your z.ai API key:")
            print("  Get one at: https://api.z.ai or https://open.bigmodel.cn")
        else:
            return None
    
    key = input("> ").strip()
    return key if key else None


def save_to_env(key_name, key_value):
    """Save API key to .env file."""
    env_vars, env_path = load_env_file()
    
    # Update or add the key
    env_vars[key_name] = key_value
    
    # Write back to .env
    with open(env_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f'{key}="{value}"\n')
    
    print(f"✓ Saved {key_name} to {env_path}")


def write_config(provider, model, api_key=None, base_url=None, ollama_url=None):
    """Write configuration to config.yaml and optionally save API key to .env."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    
    # Save API key to .env if provided
    if api_key:
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "openrouter": "OPENROUTER_API_KEY", 
            "zai": "Z_AI_API_KEY",
        }
        env_var = env_var_map.get(provider)
        if env_var:
            save_to_env(env_var, api_key)
    
    # Read existing config
    if config_path.exists():
        with open(config_path, "r") as f:
            lines = f.readlines()
    else:
        lines = []
    
    # Update provider/model lines
    new_lines = []
    provider_set = False
    model_set = False
    base_url_set = False
    api_key_set = False
    ollama_url_set = False
    
    for line in lines:
        if line.strip().startswith("provider:"):
            new_lines.append(f'provider: "{provider}"\n')
            provider_set = True
        elif line.strip().startswith("model:"):
            new_lines.append(f'model: "{model}"\n')
            model_set = True
        elif line.strip().startswith("base_url:") and base_url:
            new_lines.append(f'base_url: "{base_url}"\n')
            base_url_set = True
        elif line.strip().startswith("api_key:") and api_key:
            new_lines.append(f'api_key: "{api_key}"\n')
            api_key_set = True
        elif line.strip().startswith("ollama_url:") and ollama_url:
            new_lines.append(f'ollama_url: "{ollama_url}"\n')
            ollama_url_set = True
        else:
            new_lines.append(line)
    
    # Add missing config lines after header comments
    if not provider_set:
        insert_pos = 0
        for i, line in enumerate(new_lines):
            if not line.strip().startswith("#") and line.strip():
                insert_pos = i
                break
        new_lines.insert(insert_pos, f'provider: "{provider}"\n')
    
    if not model_set:
        for i, line in enumerate(new_lines):
            if "provider:" in line:
                new_lines.insert(i + 1, f'model: "{model}"\n')
                break
    
    # Write updated config
    with open(config_path, "w") as f:
        f.writelines(new_lines)
    
    print(f"\n✓ Configuration saved to {config_path}")


def main():
    """Run the interactive launcher."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                    🦀 HermitClaw Setup                        ║
║                                                               ║
║  Let's configure your AI model. This will update config.yaml ║
╚═══════════════════════════════════════════════════════════════╝
""")
    
    # Detect Ollama
    ollama_models = detect_ollama()
    
    # Build provider menu
    providers = [
        ("ollama", "Ollama (Local) - Free, private, runs on your machine"),
        ("zai", "z.ai / Zhipu AI - GLM models (US & China)"),
        ("openai", "OpenAI - GPT-4, GPT-4o"),
        ("openrouter", "OpenRouter - Access to many models"),
        ("bedrock", "AWS Bedrock - Claude, Llama via AWS"),
        ("custom", "Custom - Any OpenAI-compatible endpoint"),
    ]
    
    if ollama_models:
        print(f"✓ Detected Ollama with {len(ollama_models)} models installed")
    
    # Select provider
    provider = select_from_list(providers, "Select your AI provider")
    if not provider:
        print("Setup cancelled.")
        return
    
    # Handle each provider
    if provider == "ollama":
        if not ollama_models:
            print("\n⚠ Ollama not detected. Make sure it's running:")
            print("  ollama serve")
            print("\nYou can also install models with: ollama pull <model>")
            return
        
        # Select from detected models
        model_options = [(m["name"], f"{m['name']} ({m.get('size', 'unknown size')})") for m in ollama_models]
        model = select_from_list(model_options, "Select an Ollama model")
        if not model:
            return
        
        write_config("custom", model, base_url="http://localhost:11434/v1")
        print(f"\n✓ Configured to use Ollama: {model}")
        print("  Run 'python -m hermitclaw.main' to start!")
    
    elif provider == "openai":
        model = select_from_list(OPENAI_MODELS, "Select an OpenAI model")
        if not model:
            return
        api_key = get_api_key("openai")
        write_config("openai", model, api_key=api_key)
        print(f"\n✓ Configured to use OpenAI: {model}")
        print("  Run 'python -m hermitclaw.main' to start!")
    
    elif provider == "zai":
        # Select region
        region = select_from_list(ZAI_REGIONS, "Select your region")
        if not region:
            return
        
        # Select plan type
        plan_type = select_from_list(ZAI_PLAN_TYPES, "Select your plan type")
        if not plan_type:
            return
        
        # Select model
        model = select_from_list(ZAI_MODELS, "Select a GLM model")
        if not model:
            return
        
        # Build base URL based on region and plan
        if region == "us":
            if plan_type == "coding":
                base_url = "https://api.z.ai/api/coding/paas/v4"
            else:
                base_url = "https://api.z.ai/api/paas/v4"
        else:  # cn
            if plan_type == "coding":
                base_url = "https://open.bigmodel.cn/api/coding/paas/v4"
            else:
                base_url = "https://open.bigmodel.cn/api/paas/v4"
        
        # Get API key (checks existing, prompts if needed)
        api_key = get_api_key("zai")
        
        # Save to .env if new key provided
        if api_key:
            save_to_env("Z_AI_API_KEY", api_key)
        
        write_config("custom", model, api_key=api_key, base_url=base_url)
        print(f"\n✓ Configured to use z.ai ({region.upper()}, {plan_type}): {model}")
        print(f"  Endpoint: {base_url}")
        print("  Run 'python -m hermitclaw.main' to start!")
    
    elif provider == "openrouter":
        model = select_from_list(OPENROUTER_MODELS, "Select an OpenRouter model")
        if not model:
            return
        api_key = get_api_key("openrouter")
        write_config("openrouter", model, api_key=api_key, base_url="https://openrouter.ai/api/v1")
        print(f"\n✓ Configured to use OpenRouter: {model}")
        print("  Run 'python -m hermitclaw.main' to start!")
    
    elif provider == "bedrock":
        model = select_from_list(BEDROCK_MODELS, "Select a Bedrock model")
        if not model:
            return
        print("\n✓ Bedrock uses AWS credentials from:")
        print("  - AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env vars")
        print("  - ~/.aws/credentials file")
        print("  - IAM role (if on EC2)")
        write_config("bedrock", model)
        print(f"\n✓ Configured to use Bedrock: {model}")
        print("  Run 'python -m hermitclaw.main' to start!")
    
    elif provider == "custom":
        print("\nEnter the base URL for your OpenAI-compatible endpoint:")
        print("  Example: http://localhost:1234/v1 (LM Studio)")
        print("  Example: http://localhost:8080/v1 (LocalAI)")
        base_url = input("> ").strip()
        if not base_url:
            print("Cancelled.")
            return
        
        print("\nEnter the model name:")
        model = input("> ").strip()
        if not model:
            print("Cancelled.")
            return
        
        write_config("custom", model, base_url=base_url)
        print(f"\n✓ Configured custom endpoint: {base_url}")
        print("  Run 'python -m hermitclaw.main' to start!")
    
    # Configure web search
    configure_web_search()


def configure_web_search():
    """Configure web search provider (SearXNG, Brave, etc.)."""
    print("\n" + "=" * 60)
    print("🔍 Web Search Configuration")
    print("=" * 60)
    print("Enable web search for real-time information lookup.\n")
    
    enable = input("Enable web search? (Y/n) > ").strip().lower()
    if enable == "n":
        write_web_search_config("none")
        print("\n✓ Web search disabled")
        return
    
    print("\nAvailable web search providers:\n")
    print("  1. SearXNG - Self-hosted, private, free")
    print("  2. Brave Search API - Fast, requires API key")
    print("  3. Ollama Cloud - For minimax models")
    print("  4. None - Disable web search")
    
    choice = input("\nSelect provider (1-4) > ").strip()
    
    provider_map = {"1": "searxng", "2": "brave", "3": "ollama", "4": "none"}
    provider = provider_map.get(choice, "none")
    
    if provider == "searxng":
        url = input("Enter SearXNG URL (default: http://localhost:8080) > ").strip()
        url = url or "http://localhost:8080"
        write_web_search_config("searxng", searxng_url=url)
        print(f"\n✓ SearXNG configured: {url}")
    
    elif provider == "brave":
        key = input("Enter Brave Search API key > ").strip()
        if key:
            save_to_env("BRAVE_API_KEY", key)
            write_web_search_config("brave")
            print("\n✓ Brave Search configured")
        else:
            print("\n⚠️  No API key provided, web search disabled")
            write_web_search_config("none")
    
    elif provider == "ollama":
        key = input("Enter Ollama API key (or press Enter to use OLLAMA_API_KEY env var) > ").strip()
        if key:
            save_to_env("OLLAMA_API_KEY", key)
        write_web_search_config("ollama")
        print("\n✓ Ollama Cloud web search configured")
    
    else:
        write_web_search_config("none")
        print("\n✓ Web search disabled")


def write_web_search_config(provider, searxng_url=None):
    """Write web search configuration to config.yaml."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    
    # Read existing config
    if config_path.exists():
        with open(config_path, "r") as f:
            content = f.read()
    else:
        content = ""
    
    # Build web_search section
    web_search_yaml = f'\nweb_search:\n  provider: "{provider}"\n'
    if searxng_url:
        web_search_yaml += f'  searxng_url: "{searxng_url}"\n'
    
    # Check if web_search section exists
    if "web_search:" in content:
        # Replace existing web_search section
        import re
        pattern = r'web_search:.*?(?=\n\w|\Z)'
        content = re.sub(pattern, web_search_yaml.strip(), content, flags=re.DOTALL)
    else:
        # Append web_search section
        content = content.rstrip() + "\n" + web_search_yaml
    
    with open(config_path, "w") as f:
        f.write(content)


if __name__ == "__main__":
    main()
