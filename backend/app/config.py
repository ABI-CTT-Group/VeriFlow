import yaml
import os
from typing import Dict, Any, Optional

class AppConfig:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance.load_config()
        return cls._instance

    def load_config(self, path: str = "config.yaml"):
        """Loads the YAML configuration file."""
        if os.path.exists(path):
            with open(path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            # Fallback/Empty if file missing
            self._config = {}
        
        # Ensure default caching policy exists
        if "caching" not in self._config:
            self._config["caching"] = {"enabled": True}

    def is_cache_enabled(self) -> bool:
        return self._config.get("caching", {}).get("enabled", False)

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Retrieves configuration for a specific agent (e.g., 'scholar')."""
        return self._config.get("agents", {}).get(agent_name, {})

    def get_model_params(self, model_alias: str) -> Dict[str, Any]:
        """
        Resolves a model alias (e.g., 'gemini-2.5-pro') to its full configuration 
        (api_name, temperature, etc.).
        """
        models_cfg = self._config.get("models", {})
        return models_cfg.get(model_alias, {})

# Singleton accessor
config = AppConfig()