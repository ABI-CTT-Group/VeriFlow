"""
VeriFlow - Docker Builder Service
Manages Docker image generation and storage for workflow tools.
Per SPEC.md Section 7.2 and 8.1
"""

import os
import logging
from typing import Optional, Dict, List, Any
from pathlib import Path
from datetime import datetime

from app.models.cwl import (
    CWLCommandLineTool,
    DockerRequirement,
)
from app.services.minio_client import minio_service

logger = logging.getLogger(__name__)


class DockerBuilder:
    """
    Manages Docker image generation and storage for CWL tools.
    
    For MVP:
    - Generates Dockerfiles from tool CWL specifications
    - Stores Dockerfiles in MinIO workflow-tool bucket
    - Returns placeholder image names (actual builds are stretch goal)
    
    Responsibilities:
    - Parse DockerRequirement from CWL tools
    - Generate Dockerfiles with proper base images
    - Store tool artifacts in MinIO
    """
    
    # Default base images for different tool types
    DEFAULT_BASE_IMAGES = {
        "python": "python:3.11-slim",
        "r": "r-base:4.3.0",
        "conda": "continuumio/miniconda3:latest",
        "ubuntu": "ubuntu:22.04",
        "default": "python:3.11-slim",
    }
    
    # Placeholder image for MVP execution
    PLACEHOLDER_IMAGE = "python:3.11-slim"
    
    def __init__(self):
        """Initialize Docker builder."""
        self.generated_dockerfiles: Dict[str, str] = {}
    
    def generate_dockerfile(
        self,
        tool: CWLCommandLineTool,
        tool_id: str,
        requirements_txt: Optional[str] = None,
    ) -> str:
        """
        Generate a Dockerfile for a CWL tool.
        
        Args:
            tool: Parsed CWL CommandLineTool
            tool_id: Unique identifier for the tool
            requirements_txt: Optional Python requirements
            
        Returns:
            Generated Dockerfile content
        """
        # Check for existing DockerRequirement
        docker_req = self._get_docker_requirement(tool)
        
        if docker_req and docker_req.docker_file:
            # Use provided Dockerfile content
            return docker_req.docker_file
        
        # Determine base image
        base_image = self._determine_base_image(tool, docker_req)
        
        # Build Dockerfile
        dockerfile = self._build_dockerfile(
            base_image=base_image,
            tool=tool,
            tool_id=tool_id,
            requirements_txt=requirements_txt,
        )
        
        # Store for later reference
        self.generated_dockerfiles[tool_id] = dockerfile
        
        return dockerfile
    
    def _get_docker_requirement(self, tool: CWLCommandLineTool) -> Optional[DockerRequirement]:
        """Extract DockerRequirement from tool hints/requirements."""
        for req_list in [tool.requirements or [], tool.hints or []]:
            for req in req_list:
                if isinstance(req, dict) and req.get("class") == "DockerRequirement":
                    return DockerRequirement(**req)
        return None
    
    def _determine_base_image(
        self,
        tool: CWLCommandLineTool,
        docker_req: Optional[DockerRequirement],
    ) -> str:
        """Determine the appropriate base image for a tool."""
        # Use specified image if available
        if docker_req:
            if docker_req.docker_pull:
                return docker_req.docker_pull
            if docker_req.docker_image_id:
                return docker_req.docker_image_id
        
        # Infer from base command
        base_cmd = tool.base_command
        if isinstance(base_cmd, list):
            base_cmd = base_cmd[0] if base_cmd else ""
        base_cmd = str(base_cmd).lower()
        
        if "python" in base_cmd:
            return self.DEFAULT_BASE_IMAGES["python"]
        elif "r" in base_cmd or "rscript" in base_cmd:
            return self.DEFAULT_BASE_IMAGES["r"]
        elif "conda" in base_cmd:
            return self.DEFAULT_BASE_IMAGES["conda"]
        
        return self.DEFAULT_BASE_IMAGES["default"]
    
    def _build_dockerfile(
        self,
        base_image: str,
        tool: CWLCommandLineTool,
        tool_id: str,
        requirements_txt: Optional[str],
    ) -> str:
        """Build Dockerfile content."""
        lines = [
            f"# Auto-generated Dockerfile for VeriFlow tool: {tool_id}",
            f"# Generated: {datetime.utcnow().isoformat()}",
            f"# CWL Tool: {tool.label or tool.id or 'Unknown'}",
            "",
            f"FROM {base_image}",
            "",
            "# Set working directory",
            "WORKDIR /app",
            "",
            "# Install system dependencies",
            "RUN apt-get update && apt-get install -y --no-install-recommends \\",
            "    curl \\",
            "    && rm -rf /var/lib/apt/lists/*",
            "",
        ]
        
        # Add Python requirements if provided
        if requirements_txt:
            lines.extend([
                "# Install Python dependencies",
                "COPY requirements.txt .",
                "RUN pip install --no-cache-dir -r requirements.txt",
                "",
            ])
        
        # Add tool-specific labels
        lines.extend([
            "# Tool metadata",
            f'LABEL veriflow.tool.id="{tool_id}"',
            f'LABEL veriflow.tool.label="{tool.label or tool_id}"',
            "",
        ])
        
        # Add entry point based on base command
        base_cmd = tool.base_command
        if base_cmd:
            if isinstance(base_cmd, list):
                entrypoint = ", ".join(f'"{c}"' for c in base_cmd)
                lines.append(f"ENTRYPOINT [{entrypoint}]")
            else:
                lines.append(f'ENTRYPOINT ["{base_cmd}"]')
        else:
            lines.append('ENTRYPOINT ["python"]')
        
        lines.append("")
        lines.append("# Default command (can be overridden)")
        lines.append('CMD ["--help"]')
        lines.append("")
        
        return "\n".join(lines)
    
    async def store_dockerfile(
        self,
        tool_id: str,
        dockerfile: str,
        additional_files: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Store Dockerfile and related files in MinIO.
        
        Args:
            tool_id: Tool identifier
            dockerfile: Dockerfile content
            additional_files: Optional dict of filename -> content
            
        Returns:
            MinIO path to stored Dockerfile
        """
        try:
            # Store Dockerfile
            dockerfile_path = f"{tool_id}/Dockerfile"
            await minio_service.upload_text(
                bucket=minio_service.WORKFLOW_TOOL_BUCKET,
                object_name=dockerfile_path,
                content=dockerfile,
            )
            
            # Store additional files
            if additional_files:
                for filename, content in additional_files.items():
                    file_path = f"{tool_id}/{filename}"
                    await minio_service.upload_text(
                        bucket=minio_service.WORKFLOW_TOOL_BUCKET,
                        object_name=file_path,
                        content=content,
                    )
            
            logger.info(f"Stored Dockerfile for tool {tool_id}")
            return dockerfile_path
            
        except Exception as e:
            logger.error(f"Failed to store Dockerfile: {e}")
            raise
    
    def get_image_name(
        self,
        tool: CWLCommandLineTool,
        tool_id: str,
        use_placeholder: bool = True,
    ) -> str:
        """
        Get the Docker image name for a tool.
        
        Args:
            tool: CWL tool definition
            tool_id: Tool identifier
            use_placeholder: If True, return placeholder for MVP
            
        Returns:
            Docker image name
        """
        if use_placeholder:
            return self.PLACEHOLDER_IMAGE
        
        # Check for explicit image in DockerRequirement
        docker_req = self._get_docker_requirement(tool)
        if docker_req:
            if docker_req.docker_pull:
                return docker_req.docker_pull
            if docker_req.docker_image_id:
                return docker_req.docker_image_id
        
        # Generate local image name
        clean_id = "".join(c if c.isalnum() else "_" for c in tool_id).lower()
        return f"veriflow/{clean_id}:latest"
    
    def generate_build_script(
        self,
        tool_id: str,
        dockerfile_path: str,
        context_path: str,
    ) -> str:
        """
        Generate a build script for Docker image.
        
        Args:
            tool_id: Tool identifier
            dockerfile_path: Path to Dockerfile
            context_path: Build context path
            
        Returns:
            Shell script content
        """
        clean_id = "".join(c if c.isalnum() else "_" for c in tool_id).lower()
        image_name = f"veriflow/{clean_id}:latest"
        
        script = f'''#!/bin/bash
# Build script for VeriFlow tool: {tool_id}
# Generated: {datetime.utcnow().isoformat()}

set -e

DOCKERFILE="{dockerfile_path}"
CONTEXT="{context_path}"
IMAGE="{image_name}"

echo "Building Docker image: $IMAGE"
docker build -t "$IMAGE" -f "$DOCKERFILE" "$CONTEXT"

echo "Image built successfully: $IMAGE"
docker images | grep veriflow/{clean_id}
'''
        return script


# Singleton instance
docker_builder = DockerBuilder()
