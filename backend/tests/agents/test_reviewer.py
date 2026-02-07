import pytest
from unittest.mock import MagicMock, patch


class TestReviewerAgent:

    @pytest.fixture
    def reviewer_agent(self, mock_genai):
        """Create a ReviewerAgent instance with mocked Gemini client."""
        from app.agents.reviewer import ReviewerAgent
        return ReviewerAgent()

    @pytest.mark.asyncio
    async def test_validate_workflow_success(self, reviewer_agent, mock_subprocess, mock_genai):
        """Test successful workflow validation."""
        # Mock cwltool success
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = ""
        mock_subprocess.return_value.stderr = ""

        # Mock semantic validation response
        mock_parsed = MagicMock()
        mock_parsed.model_dump.return_value = {
            "thought_process": "Validated workflow",
            "passed": True,
            "issues": [],
            "summary": "All checks passed.",
        }
        mock_genai["response"].parsed = mock_parsed

        graph = {"nodes": [], "edges": []}

        result = await reviewer_agent.validate_workflow(
            workflow_cwl="cwlVersion: v1.3\nclass: Workflow\ninputs: []\noutputs: []",
            tool_cwls={},
            graph=graph,
        )

        assert result["passed"] is True
        assert len(result["user_action_required"]) == 0

    @pytest.mark.asyncio
    async def test_validate_workflow_cwl_fail(self, reviewer_agent, mock_subprocess, mock_genai):
        """Test validation failure due to bad CWL."""
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "Syntax Error on line 5"

        # Mock semantic validation
        mock_parsed = MagicMock()
        mock_parsed.model_dump.return_value = {
            "thought_process": "Found issues",
            "passed": False,
            "issues": [{"id": "1", "severity": "error", "category": "cwl_syntax",
                        "message": "Syntax error", "user_friendly_message": "Bad syntax",
                        "suggestion": "Fix line 5", "auto_fixable": False}],
            "summary": "CWL syntax errors found.",
        }
        mock_genai["response"].parsed = mock_parsed

        result = await reviewer_agent.validate_workflow(
            workflow_cwl="bad cwl",
            tool_cwls={},
            graph={"nodes": [], "edges": []},
        )

        assert result["passed"] is False
        assert "Syntax Error on line 5" in result["checks"]["cwl_syntax"]["errors"]

    def test_check_type_compatibility(self, reviewer_agent):
        """Test type compatibility checking."""
        graph = {
            "nodes": [
                {
                    "id": "n1",
                    "data": {"outputs": [{"id": "o1", "type": "application/dicom"}]},
                },
                {
                    "id": "n2",
                    "data": {"inputs": [{"id": "i1", "type": "application/x-nifti"}]},
                },
            ],
            "edges": [
                {
                    "source": "n1",
                    "target": "n2",
                    "sourceHandle": "o1",
                    "targetHandle": "i1",
                }
            ],
        }

        result = reviewer_agent._check_type_compatibility(graph)

        assert result["passed"] is False
        assert len(result["mismatches"]) == 1
        assert result["mismatches"][0]["suggested_adapter"] == "dcm2niix"

    @pytest.mark.asyncio
    async def test_translate_errors(self, reviewer_agent, mock_genai):
        """Test error translation via Gemini 3 structured output."""
        mock_parsed = MagicMock()
        mock_parsed.model_dump.return_value = {
            "thought_process": "Translating errors",
            "translations": [
                {
                    "original": "err",
                    "translated": "Friendly Error",
                    "suggestion": "Fix it",
                    "severity": "error",
                }
            ],
        }
        mock_genai["response"].parsed = mock_parsed

        translated = await reviewer_agent._translate_errors(["err"])

        assert len(translated) == 1
        assert translated[0]["translated"] == "Friendly Error"

    @pytest.mark.asyncio
    async def test_validate_and_fix_iterative(self, reviewer_agent, mock_genai):
        """Test iterative validation with thought signatures."""
        # First call: validation fails
        mock_response_1 = {
            "result": {
                "thought_process": "Found issues",
                "passed": False,
                "issues": [{"id": "1", "severity": "error"}],
                "summary": "Issues found",
            },
            "thought_signatures": ["thought_sig_1"],
        }

        # Second call: validation passes
        mock_response_2 = {
            "result": {
                "thought_process": "Fixed issues",
                "passed": True,
                "issues": [],
                "summary": "All fixed",
            },
            "thought_signatures": ["thought_sig_2"],
        }

        reviewer_agent.client.generate_with_history = MagicMock(
            side_effect=[mock_response_1, mock_response_2]
        )

        result = await reviewer_agent.validate_and_fix(
            workflow_cwl="cwl content",
            tool_cwls={},
            graph={"nodes": [], "edges": []},
            max_iterations=3,
        )

        assert result["final_result"]["passed"] is True
        assert result["iterations"] == 2
