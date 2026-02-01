import yaml
import os
from typing import Dict, Optional

class PromptManager:
    _instance = None
    _prompts: Dict[str, Dict[str, str]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PromptManager, cls).__new__(cls)
            cls._instance.load_prompts()
        return cls._instance

    def load_prompts(self, path: str = "prompts.yaml"):
        """Loads prompts from a YAML file."""
        if os.path.exists(path):
            with open(path, 'r') as f:
                self._prompts = yaml.safe_load(f) or {}
        else:
            print(f"Warning: Prompt file {path} not found.")

    def get_prompt(self, agent_name: str, version: str) -> str:
        """
        Retrieves a raw prompt string for a specific agent and version.
        Raises ValueError if not found.
        """
        agent_prompts = self._prompts.get(agent_name)
        if not agent_prompts:
            raise ValueError(f"No prompts found for agent: {agent_name}")
        
        prompt_template = agent_prompts.get(version)
        if not prompt_template:
            raise ValueError(f"Version '{version}' not found for agent '{agent_name}'. Available: {list(agent_prompts.keys())}")
            
        return prompt_template

# Singleton accessor
prompt_manager = PromptManager()