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

    # --- suggest_fixes ---

    @pytest.mark.asyncio
    async def test_suggest_fixes_passed(self, reviewer_agent, mock_genai):
        """Test suggest_fixes returns no fixes when validation passed."""
        result = await reviewer_agent.suggest_fixes(
            validation_result={"passed": True},
            workflow_cwl="cwl",
            graph={},
        )

        assert result["fixes"] == []
        assert result["message"] == "No fixes needed"

    @pytest.mark.asyncio
    async def test_suggest_fixes_type_mismatch(self, reviewer_agent, mock_genai):
        """Test suggest_fixes returns adapter fix for type mismatch."""
        validation_result = {
            "passed": False,
            "checks": {
                "data_format": {
                    "mismatches": [
                        {
                            "source_node": "n1",
                            "target_node": "n2",
                            "suggested_adapter": "dcm2niix",
                            "message": "Type mismatch",
                        }
                    ]
                },
                "dependencies": {"missing": []},
            },
        }

        result = await reviewer_agent.suggest_fixes(
            validation_result=validation_result,
            workflow_cwl="cwl",
            graph={},
        )

        assert len(result["fixes"]) == 1
        assert result["fixes"][0]["type"] == "add_adapter"
        assert result["fixes"][0]["adapter"] == "dcm2niix"

    # --- _basic_cwl_validation ---

    def test_basic_cwl_validation_valid(self, reviewer_agent):
        """Test basic CWL validation passes for valid content."""
        cwl = "cwlVersion: v1.3\nclass: Workflow\ninputs:\n  x: File\noutputs:\n  y: File"
        result = reviewer_agent._basic_cwl_validation(cwl)

        assert result["passed"] is True
        assert len(result["errors"]) == 0

    def test_basic_cwl_validation_missing_sections(self, reviewer_agent):
        """Test basic CWL validation catches missing sections."""
        result = reviewer_agent._basic_cwl_validation("just some text")

        assert result["passed"] is False
        assert any("cwlVersion" in e for e in result["errors"])

    # --- _validate_cwl_syntax ---

    @pytest.mark.asyncio
    async def test_validate_cwl_syntax_empty(self, reviewer_agent, mock_genai):
        """Test validation of empty CWL content."""
        result = await reviewer_agent._validate_cwl_syntax("")

        assert result["passed"] is False
        assert "Empty CWL content" in result["errors"]

    @pytest.mark.asyncio
    async def test_validate_cwl_syntax_cwltool_not_found(self, reviewer_agent, mock_genai, mock_subprocess):
        """Test fallback to basic validation when cwltool not found."""
        mock_subprocess.side_effect = FileNotFoundError("cwltool not found")

        result = await reviewer_agent._validate_cwl_syntax(
            "cwlVersion: v1.3\nclass: Workflow\ninputs:\n  x: File\noutputs:\n  y: File"
        )

        # Falls back to _basic_cwl_validation which should pass
        assert result["passed"] is True

    # --- _types_compatible ---

    def test_types_compatible_same(self, reviewer_agent):
        """Test same types are compatible."""
        assert reviewer_agent._types_compatible("File", "File") is True

    def test_types_compatible_octet_wildcard(self, reviewer_agent):
        """Test octet-stream is compatible with wildcard."""
        assert reviewer_agent._types_compatible("application/octet-stream", "*") is True

    def test_types_compatible_nifti_variants(self, reviewer_agent):
        """Test NIfTI MIME type variants are compatible."""
        assert reviewer_agent._types_compatible("application/x-nifti", "application/nifti") is True
        assert reviewer_agent._types_compatible("image/nifti", "application/x-nifti") is True

    # --- _suggest_adapter ---

    def test_suggest_adapter_known_pair(self, reviewer_agent):
        """Test known adapter suggestion for DICOM to NIfTI."""
        adapter = reviewer_agent._suggest_adapter("application/dicom", "application/x-nifti")
        assert adapter == "dcm2niix"

    def test_suggest_adapter_unknown_pair(self, reviewer_agent):
        """Test custom adapter name for unknown type pair."""
        adapter = reviewer_agent._suggest_adapter("text/plain", "image/png")
        assert "custom-adapter" in adapter

    # --- _check_dependencies ---

    def test_check_dependencies_empty(self, reviewer_agent):
        """Test dependency check passes with no tools."""
        result = reviewer_agent._check_dependencies({})
        assert result["passed"] is True
        assert result["missing"] == []
