import yaml
import os
from typing import Dict, Any

class AppConfig:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance.load_config()
        return cls._instance

    def load_config(self, path: str = "config.yaml"):
        if os.path.exists(path):
            with open(path, 'r') as f:
                self._config = yaml.safe_load(f)
        else:
            # Fallback defaults if file missing
            self._config = {
                "models": {
                    "gemini-2.5-pro": {"api_model_name": "gemini-2.5-pro"}
                },
                "agents": {
                    "scholar": {"default_model": "gemini-2.5-pro", "default_prompt_version": "v1_standard"}
                }
            }

    def get_model_config(self, model_alias: str) -> Dict[str, Any]:
        return self._config.get("models", {}).get(model_alias, {})

    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        return self._config.get("agents", {}).get(agent_name, {})

# Singleton accessor
config = AppConfig()