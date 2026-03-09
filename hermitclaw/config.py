"""All configuration in one place."""

import os
import yaml
from pathlib import Path

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.yaml")

# Load .env file if it exists
def _load_env():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value

_load_env()

# Known provider presets: provider_name -> default base_url
PROVIDER_PRESETS = {
    "openai": None,  # uses OpenAI default
    "openrouter": "https://openrouter.ai/api/v1",
    "bedrock": None,  # uses AWS SDK
}

# Provider-specific API key env vars (checked before OPENAI_API_KEY fallback)
PROVIDER_KEY_ENV_VARS = {
    "openrouter": "OPENROUTER_API_KEY",
    "custom": "Z_AI_API_KEY",  # z.ai and other custom endpoints
}


def load_config() -> dict:
    """Load config from config.yaml, with env var overrides."""
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)

    # Provider (default: openai)
    config["provider"] = os.environ.get("HERMITCLAW_PROVIDER") or config.get(
        "provider", "openai"
    )
    provider = config["provider"]

    # Base URL: env var > config > provider preset
    config["base_url"] = (
        os.environ.get("HERMITCLAW_BASE_URL")
        or config.get("base_url")
        or PROVIDER_PRESETS.get(provider)
    )

    # API key: provider-specific env var > OPENAI_API_KEY > config
    provider_key_var = PROVIDER_KEY_ENV_VARS.get(provider)
    config["api_key"] = (
        (os.environ.get(provider_key_var) if provider_key_var else None)
        or os.environ.get("OPENAI_API_KEY")
        or config.get("api_key")
    )

    # Model
    config["model"] = os.environ.get("HERMITCLAW_MODEL") or config.get(
        "model", "gpt-4o"
    )

    # Ollama cloud web search (for minimax-m2.5:cloud etc.)
    config["ollama_api_key"] = os.environ.get("OLLAMA_API_KEY") or config.get(
        "ollama_api_key"
    )

    # Web search provider configuration
    web_search_config = config.get("web_search", {})
    config["web_search_provider"] = os.environ.get("HERMITCLAW_WEB_SEARCH_PROVIDER") or web_search_config.get("provider", "ollama")
    config["web_search_searxng_url"] = os.environ.get("SEARXNG_URL") or web_search_config.get("searxng_url")
    config["web_search_brave_api_key"] = os.environ.get("BRAVE_API_KEY") or web_search_config.get("brave_api_key")
    config["web_search_custom_url"] = os.environ.get("HERMITCLAW_WEB_SEARCH_URL") or web_search_config.get("custom_url")
    config["web_search_custom_headers"] = web_search_config.get("custom_headers", {})

    # Defaults for numeric settings
    config.setdefault("thinking_pace_seconds", 45)
    config.setdefault("max_thoughts_in_context", 20)
    config.setdefault("environment_path", "./environment")
    config.setdefault("reflection_threshold", 50)
    config.setdefault("memory_retrieval_count", 3)
    config.setdefault("embedding_model", "text-embedding-3-small")
    config.setdefault("recency_decay_rate", 0.995)

    # Resolve environment_path relative to project root
    project_root = os.path.dirname(os.path.dirname(__file__))
    if not os.path.isabs(config["environment_path"]):
        config["environment_path"] = os.path.join(
            project_root, config["environment_path"]
        )

    # Validation
    if provider == "custom" and not config.get("base_url"):
        raise ValueError(
            "Provider 'custom' requires base_url in config.yaml or HERMITCLAW_BASE_URL env var"
        )

    return config


# Global config — loaded once, can be updated at runtime
_config = None


def get_config() -> dict:
    """Get the global config, loading it if necessary."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> dict:
    """Force reload config from disk."""
    global _config
    _config = load_config()
    return _config


# Backwards compatibility - config is a dict-like object
class ConfigProxy:
    """Proxy that behaves like a dict but always returns current config."""
    
    def __getitem__(self, key):
        return get_config()[key]
    
    def __setitem__(self, key, value):
        get_config()[key] = value
    
    def get(self, key, default=None):
        return get_config().get(key, default)
    
    def setdefault(self, key, default=None):
        return get_config().setdefault(key, default)
    
    def __contains__(self, key):
        return key in get_config()
    
    def __repr__(self):
        return repr(get_config())


config = ConfigProxy()
