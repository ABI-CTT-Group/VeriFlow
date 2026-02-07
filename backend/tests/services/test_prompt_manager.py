import pytest
import yaml
from app.services.prompt_manager import PromptManager


class TestPromptManager:

    def test_load_prompts_valid(self, reset_prompt_manager_singleton, tmp_path):
        """Test loading a valid prompts.yaml."""
        prompts_data = {
            "scholar_system": {"v1_standard": "You are the Scholar Agent."},
            "scholar_analysis": {"v1_standard": "Analyze this publication."},
        }
        prompts_file = tmp_path / "prompts.yaml"
        prompts_file.write_text(yaml.dump(prompts_data))

        pm = PromptManager.__new__(PromptManager)
        pm.load_prompts(str(prompts_file))

        assert "scholar_system" in pm._prompts
        assert pm._prompts["scholar_system"]["v1_standard"] == "You are the Scholar Agent."

    def test_load_prompts_missing_file(self, reset_prompt_manager_singleton, capsys):
        """Test warning on missing prompt file."""
        pm = PromptManager.__new__(PromptManager)
        pm._prompts = {}
        pm.load_prompts("/nonexistent/prompts.yaml")

        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_get_prompt_success(self, reset_prompt_manager_singleton, tmp_path):
        """Test getting a prompt by agent and version."""
        prompts_data = {
            "scholar_system": {"v1_standard": "System prompt text."},
        }
        prompts_file = tmp_path / "prompts.yaml"
        prompts_file.write_text(yaml.dump(prompts_data))

        pm = PromptManager.__new__(PromptManager)
        pm.load_prompts(str(prompts_file))

        result = pm.get_prompt("scholar_system", "v1_standard")
        assert result == "System prompt text."

    def test_get_prompt_unknown_agent(self, reset_prompt_manager_singleton, tmp_path):
        """Test ValueError on unknown agent name."""
        prompts_file = tmp_path / "prompts.yaml"
        prompts_file.write_text(yaml.dump({"scholar_system": {"v1": "text"}}))

        pm = PromptManager.__new__(PromptManager)
        pm.load_prompts(str(prompts_file))

        with pytest.raises(ValueError, match="No prompts found for agent"):
            pm.get_prompt("nonexistent_agent", "v1")

    def test_get_prompt_unknown_version(self, reset_prompt_manager_singleton, tmp_path):
        """Test ValueError on unknown version."""
        prompts_file = tmp_path / "prompts.yaml"
        prompts_file.write_text(yaml.dump({"scholar_system": {"v1": "text"}}))

        pm = PromptManager.__new__(PromptManager)
        pm.load_prompts(str(prompts_file))

        with pytest.raises(ValueError, match="Version"):
            pm.get_prompt("scholar_system", "v99_nonexistent")

    def test_singleton_pattern(self, reset_prompt_manager_singleton):
        """Test that PromptManager is a singleton."""
        a = PromptManager()
        b = PromptManager()
        assert a is b

    def test_reload_prompts(self, reset_prompt_manager_singleton, tmp_path):
        """Test reloading prompts overwrites previous data."""
        file1 = tmp_path / "prompts1.yaml"
        file1.write_text(yaml.dump({"agent_a": {"v1": "old"}}))

        file2 = tmp_path / "prompts2.yaml"
        file2.write_text(yaml.dump({"agent_b": {"v2": "new"}}))

        pm = PromptManager.__new__(PromptManager)
        pm.load_prompts(str(file1))
        assert "agent_a" in pm._prompts

        pm.load_prompts(str(file2))
        assert "agent_b" in pm._prompts
        assert "agent_a" not in pm._prompts
