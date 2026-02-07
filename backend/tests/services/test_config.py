import pytest
import os
import yaml
from unittest.mock import patch
from app.config import AppConfig


class TestAppConfig:

    def test_load_config_valid(self, reset_config_singleton, tmp_path):
        """Test loading a valid config.yaml."""
        config_data = {
            "caching": {"enabled": True},
            "agents": {"scholar": {"default_model": "gemini-3-pro"}},
            "models": {"gemini-3-pro": {"api_model_name": "gemini-3-pro-preview", "temperature": 1.0}},
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        cfg = AppConfig.__new__(AppConfig)
        cfg.load_config(str(config_file))

        assert cfg._config["caching"]["enabled"] is True
        assert cfg._config["agents"]["scholar"]["default_model"] == "gemini-3-pro"

    def test_load_config_missing_file(self, reset_config_singleton):
        """Test graceful fallback when config file is missing."""
        cfg = AppConfig.__new__(AppConfig)
        cfg.load_config("/nonexistent/config.yaml")

        assert cfg._config == {"caching": {"enabled": False}}

    def test_is_cache_enabled_true(self, reset_config_singleton, tmp_path):
        """Test is_cache_enabled returns True when configured."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump({"caching": {"enabled": True}}))

        cfg = AppConfig.__new__(AppConfig)
        cfg.load_config(str(config_file))

        assert cfg.is_cache_enabled() is True

    def test_is_cache_enabled_false(self, reset_config_singleton, tmp_path):
        """Test is_cache_enabled returns False when not configured."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump({"caching": {"enabled": False}}))

        cfg = AppConfig.__new__(AppConfig)
        cfg.load_config(str(config_file))

        assert cfg.is_cache_enabled() is False

    def test_get_agent_config_scholar(self, reset_config_singleton, tmp_path):
        """Test getting scholar agent config."""
        config_data = {
            "agents": {"scholar": {"default_model": "gemini-3-pro", "thinking_level": "HIGH"}},
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        cfg = AppConfig.__new__(AppConfig)
        cfg.load_config(str(config_file))

        agent_cfg = cfg.get_agent_config("scholar")
        assert agent_cfg["default_model"] == "gemini-3-pro"
        assert agent_cfg["thinking_level"] == "HIGH"

    def test_get_agent_config_unknown(self, reset_config_singleton, tmp_path):
        """Test getting config for unknown agent returns empty dict."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump({"agents": {}}))

        cfg = AppConfig.__new__(AppConfig)
        cfg.load_config(str(config_file))

        assert cfg.get_agent_config("nonexistent") == {}

    def test_get_model_params_known(self, reset_config_singleton, tmp_path):
        """Test getting model params for known model alias."""
        config_data = {
            "models": {"gemini-3-pro": {"api_model_name": "gemini-3-pro-preview", "temperature": 1.0}},
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        cfg = AppConfig.__new__(AppConfig)
        cfg.load_config(str(config_file))

        params = cfg.get_model_params("gemini-3-pro")
        assert params["api_model_name"] == "gemini-3-pro-preview"

    def test_get_model_params_unknown(self, reset_config_singleton, tmp_path):
        """Test getting model params for unknown alias returns empty dict."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump({"models": {}}))

        cfg = AppConfig.__new__(AppConfig)
        cfg.load_config(str(config_file))

        assert cfg.get_model_params("nonexistent") == {}

    def test_singleton_pattern(self, reset_config_singleton):
        """Test that AppConfig is a singleton."""
        a = AppConfig()
        b = AppConfig()
        assert a is b
