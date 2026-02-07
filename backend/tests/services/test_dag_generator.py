import pytest
from pathlib import Path
from app.services.dag_generator import DAGGenerator
from app.services.cwl_parser import CWLParser


class TestDAGGenerator:

    @pytest.fixture
    def generator(self, tmp_path):
        """Create a DAGGenerator with a temporary dags path."""
        return DAGGenerator(dags_path=tmp_path)

    @pytest.fixture
    def parsed_workflow(self, sample_cwl_workflow):
        """Parse the sample CWL workflow fixture."""
        parser = CWLParser()
        result = parser.parse_workflow(sample_cwl_workflow)
        assert result.success
        return result.workflow

    def test_generate_dag_creates_file(self, generator, parsed_workflow, tmp_path):
        """Test that generate_dag creates a .py file."""
        dag_path = generator.generate_dag(
            workflow=parsed_workflow,
            execution_id="exec_abc123",
        )

        assert Path(dag_path).exists()
        assert dag_path.endswith(".py")

    def test_generate_dag_id_format(self, generator, parsed_workflow):
        """Test DAG ID format: veriflow_{workflow_id}_{execution_id}."""
        dag_id = generator._generate_dag_id(parsed_workflow, "exec_abc123")

        assert dag_id.startswith("veriflow_")
        assert "exec_abc123" in dag_id

    def test_generate_dag_id_special_chars(self, generator, parsed_workflow):
        """Test DAG ID sanitizes special characters to underscores."""
        dag_id = generator._generate_dag_id(parsed_workflow, "exec_abc123")

        # test-workflow becomes test_workflow
        assert "test_workflow" in dag_id
        assert "-" not in dag_id

    def test_generate_dag_code_contains_imports(self, generator, parsed_workflow):
        """Test generated DAG code includes Airflow imports."""
        code = generator._generate_dag_code(
            workflow=parsed_workflow,
            dag_id="veriflow_test",
            execution_id="exec_abc",
            config={},
        )

        assert "from airflow import DAG" in code
        assert "from airflow.operators.bash import BashOperator" in code

    def test_generate_dag_code_contains_dag_def(self, generator, parsed_workflow):
        """Test generated code contains DAG definition."""
        code = generator._generate_dag_code(
            workflow=parsed_workflow,
            dag_id="veriflow_test",
            execution_id="exec_abc",
            config={},
        )

        assert 'dag_id="veriflow_test"' in code
        assert "schedule_interval=None" in code

    def test_generate_dag_code_contains_tasks(self, generator, parsed_workflow):
        """Test generated code contains task definitions for steps."""
        code = generator._generate_dag_code(
            workflow=parsed_workflow,
            dag_id="veriflow_test",
            execution_id="exec_abc",
            config={},
        )

        assert "step1" in code
        assert "step2" in code
        assert 'task_id="start"' in code
        assert 'task_id="end"' in code

    def test_generate_bash_task(self, generator, parsed_workflow):
        """Test BashOperator task generation when no Docker image."""
        step = parsed_workflow.workflow.steps["step1"]
        code = generator._generate_bash_task("step1", step, "exec_abc", {})

        assert "BashOperator" in code
        assert 'task_id="step1"' in code

    def test_generate_dependencies_linear(self, generator):
        """Test dependency generation for a linear chain."""
        deps = {"step2": ["step1"]}
        code = generator._generate_dependencies(deps)

        assert "start >> step1" in code
        assert "step1 >> step2" in code
        assert "step2 >> end" in code

    def test_delete_dag_exists(self, generator, parsed_workflow, tmp_path):
        """Test deleting an existing DAG file."""
        dag_path = generator.generate_dag(parsed_workflow, "exec_del")
        dag_id = generator._generate_dag_id(parsed_workflow, "exec_del")

        assert generator.delete_dag(dag_id) is True
        assert not Path(dag_path).exists()

    def test_delete_dag_not_exists(self, generator):
        """Test deleting a non-existent DAG returns False."""
        assert generator.delete_dag("nonexistent_dag") is False

    def test_list_generated_dags_empty(self, generator):
        """Test listing DAGs in empty directory."""
        assert generator.list_generated_dags() == []
