import pytest
from app.services.docker_builder import DockerBuilder
from app.models.cwl import CWLCommandLineTool, CWLInput, CWLOutput


class TestDockerBuilder:

    @pytest.fixture
    def builder(self):
        return DockerBuilder()

    @pytest.fixture
    def basic_tool(self):
        """A basic CWL CommandLineTool without DockerRequirement."""
        return CWLCommandLineTool(
            cwlVersion="v1.3",
            **{"class": "CommandLineTool"},
            id="basic-tool",
            label="Basic Tool",
            baseCommand=["python", "run.py"],
            inputs={"input_file": CWLInput(type="File")},
            outputs={"output_file": CWLOutput(type="File")},
        )

    @pytest.fixture
    def docker_tool(self):
        """A CWL CommandLineTool with DockerRequirement."""
        return CWLCommandLineTool(
            cwlVersion="v1.3",
            **{"class": "CommandLineTool"},
            id="docker-tool",
            label="Docker Tool",
            baseCommand=["python", "process.py"],
            inputs={"input_file": CWLInput(type="File")},
            outputs={"output_file": CWLOutput(type="File")},
            hints=[{"class": "DockerRequirement", "dockerPull": "myimage:1.0"}],
        )

    def test_generate_dockerfile_default(self, builder, basic_tool):
        """Test Dockerfile generation with default base image."""
        dockerfile = builder.generate_dockerfile(basic_tool, "basic-tool")

        assert "FROM python:3.11-slim" in dockerfile
        assert "WORKDIR /app" in dockerfile
        assert 'LABEL veriflow.tool.id="basic-tool"' in dockerfile
        assert 'ENTRYPOINT ["python", "run.py"]' in dockerfile

    def test_generate_dockerfile_with_docker_pull(self, builder, docker_tool):
        """Test Dockerfile uses dockerPull image when DockerRequirement has dockerFile=None."""
        dockerfile = builder.generate_dockerfile(docker_tool, "docker-tool")

        # When docker_req exists but docker_file is None, we generate from base
        assert "FROM myimage:1.0" in dockerfile

    def test_determine_base_image_python(self, builder):
        """Test base image inference for Python tools."""
        tool = CWLCommandLineTool(
            cwlVersion="v1.3", **{"class": "CommandLineTool"},
            baseCommand="python", inputs={}, outputs={},
        )
        image = builder._determine_base_image(tool, None)
        assert image == "python:3.11-slim"

    def test_determine_base_image_r(self, builder):
        """Test base image inference for R tools."""
        tool = CWLCommandLineTool(
            cwlVersion="v1.3", **{"class": "CommandLineTool"},
            baseCommand="Rscript", inputs={}, outputs={},
        )
        image = builder._determine_base_image(tool, None)
        assert image == "r-base:4.3.0"

    def test_determine_base_image_conda(self, builder):
        """Test base image inference for conda tools."""
        tool = CWLCommandLineTool(
            cwlVersion="v1.3", **{"class": "CommandLineTool"},
            baseCommand="conda", inputs={}, outputs={},
        )
        image = builder._determine_base_image(tool, None)
        assert image == "continuumio/miniconda3:latest"

    def test_determine_base_image_default(self, builder):
        """Test default base image for unknown tool types."""
        tool = CWLCommandLineTool(
            cwlVersion="v1.3", **{"class": "CommandLineTool"},
            baseCommand="unknown_cmd", inputs={}, outputs={},
        )
        image = builder._determine_base_image(tool, None)
        assert image == "python:3.11-slim"

    def test_get_image_name_placeholder(self, builder, basic_tool):
        """Test get_image_name returns placeholder when use_placeholder=True."""
        name = builder.get_image_name(basic_tool, "basic-tool", use_placeholder=True)
        assert name == "python:3.11-slim"

    def test_get_image_name_from_docker_req(self, builder, docker_tool):
        """Test get_image_name returns dockerPull image when use_placeholder=False."""
        name = builder.get_image_name(docker_tool, "docker-tool", use_placeholder=False)
        assert name == "myimage:1.0"

    def test_generate_build_script(self, builder):
        """Test build script generation."""
        script = builder.generate_build_script(
            tool_id="my-tool",
            dockerfile_path="/path/to/Dockerfile",
            context_path="/path/to/context",
        )

        assert "#!/bin/bash" in script
        assert "docker build" in script
        assert "veriflow/my_tool:latest" in script
        assert "/path/to/Dockerfile" in script
