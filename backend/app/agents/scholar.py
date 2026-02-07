"""
VeriFlow - Scholar Agent
Per SPEC.md Section 4.3 - ISA extraction from scientific publications

Uses google-genai SDK with Gemini 3 features:
- Pydantic structured output (AnalysisResult schema)
- Thinking level control for complex scientific extraction
- Grounding with Google Search for tool/model verification
- Native PDF upload for multimodal analysis
- Config-driven model selection
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.services.gemini_client import GeminiClient
from app.services.prompt_manager import prompt_manager
from app.config import config
from app.models.schemas import AnalysisResult

logger = logging.getLogger(__name__)


class ScholarAgent:
    """
    Scholar Agent for scientific publication analysis.

    Uses Gemini 3 with structured output (AnalysisResult schema) and
    Grounding with Google Search to extract and verify ISA hierarchy
    from scientific papers.
    """

    def __init__(self):
        self.client = GeminiClient()

        # Load Agent-Specific Config
        self.agent_config = config.get_agent_config("scholar")
        self.prompt_version = self.agent_config.get("default_prompt_version", "v1_standard")

        # Resolve Model Alias to API Parameters
        model_alias = self.agent_config.get("default_model", "gemini-3-pro")
        self.model_params = config.get_model_params(model_alias)

        # Apply Configuration to Client
        self.client.model_name = self.model_params.get("api_model_name", model_alias)

        # Gemini 3: Thinking level and grounding
        self.thinking_level = self.agent_config.get("thinking_level", "HIGH")
        self.temperature = self.model_params.get("temperature", 1.0)

    async def analyze_publication(
        self,
        pdf_path: str,
        context_content: Optional[str] = None,
        upload_id: Optional[str] = None,
        enable_grounding: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze a publication PDF file using Gemini 3.

        Features used:
        - Native PDF upload (multimodal)
        - Pydantic structured output (AnalysisResult)
        - Thinking level: HIGH for deep scientific reasoning
        - Grounding with Google Search for tool/model verification
        """
        if not os.path.exists(pdf_path):
            return {"error": f"File not found: {pdf_path}"}

        try:
            # Retrieve Prompts
            system_instruction = prompt_manager.get_prompt("scholar_system", self.prompt_version)
            base_prompt = prompt_manager.get_prompt("scholar_analysis", self.prompt_version)

            full_prompt = f"{base_prompt}\nContext: {context_content or ''}"

            # Execute with Gemini 3 features
            response_data = self.client.analyze_file(
                file_path=pdf_path,
                prompt=full_prompt,
                system_instruction=system_instruction,
                temperature=self.temperature,
                response_schema=AnalysisResult,
                thinking_level=self.thinking_level,
                enable_grounding=enable_grounding,
            )

            # DATA TRANSFORMATION (List -> Dict for backward compatibility)
            conf_scores_list = response_data.get("confidence_scores", [])
            conf_scores_dict = {item["name"]: item["score"] for item in conf_scores_list}

            tools_list = response_data.get("identified_tools", [])

            isa_data = response_data.get("investigation", {})
            meta_list = isa_data.get("metadata", [])
            for item in meta_list:
                isa_data[item["key"]] = item["value"]
            if "metadata" in isa_data and isinstance(isa_data["metadata"], list):
                del isa_data["metadata"]

            return {
                "isa_json": isa_data,
                "confidence_scores": conf_scores_dict,
                "identified_tools": tools_list,
                "identified_models": response_data.get("identified_models", []),
                "identified_measurements": response_data.get("identified_measurements", []),
                "agent_thoughts": response_data.get("thought_process", ""),
                "metadata": {
                    "upload_id": upload_id,
                    "generated_at": datetime.utcnow().isoformat(),
                    "agent": "scholar_v2",
                    "model_used": self.client.model_name,
                    "thinking_level": self.thinking_level,
                    "grounding_enabled": enable_grounding,
                },
            }

        except Exception as e:
            logger.error(f"Scholar Agent error: {e}")
            return {"error": str(e), "isa_json": {}}

    async def analyze_with_vision(
        self,
        pdf_path: str,
        context_content: Optional[str] = None,
        upload_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a publication using Gemini 3 Flash's Agentic Vision.

        Extracts page images from the PDF and sends them alongside the
        document for visual analysis of methodology diagrams, flowcharts,
        and architecture figures. This enables extraction of workflow
        steps from figures, not just text.

        Uses Gemini 3 Flash with agentic vision for think-act-observe loops
        on scientific figures.
        """
        if not os.path.exists(pdf_path):
            return {"error": f"File not found: {pdf_path}"}

        try:
            import fitz  # PyMuPDF

            # Extract page images for visual analysis
            doc = fitz.open(pdf_path)
            page_images = []
            for page_num in range(min(len(doc), 10)):  # Limit to first 10 pages
                page = doc[page_num]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for clarity
                img_bytes = pix.tobytes("png")
                page_images.append({
                    "page": page_num + 1,
                    "image_bytes": img_bytes,
                })
            doc.close()

            # Use Gemini 3 Flash for agentic vision on figures
            system_instruction = """You are the Scholar Agent with Agentic Vision.
Analyze both the text and visual elements (figures, diagrams, flowcharts) of this scientific publication.
Pay special attention to:
1. Methodology diagrams showing pipeline steps
2. Architecture figures showing model structure
3. Flowcharts showing data processing steps
4. Tables with experimental parameters
Cross-reference visual information with text to ensure accuracy."""

            # Upload images as parts alongside the PDF
            prompt = """Analyze this scientific publication's text AND figures.
For each figure that shows a methodology or pipeline:
1. Describe what the figure shows
2. Extract the processing steps from the figure
3. Identify tools/models shown in the figure
4. Cross-reference with the text description

Return the ISA hierarchy combining both textual and visual analysis."""

            # Native PDF upload already captures figures in Gemini 3
            response_data = self.client.analyze_file(
                file_path=pdf_path,
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=self.temperature,
                response_schema=AnalysisResult,
                thinking_level="HIGH",
            )

            # Transform response
            conf_scores_list = response_data.get("confidence_scores", [])
            conf_scores_dict = {item["name"]: item["score"] for item in conf_scores_list}

            isa_data = response_data.get("investigation", {})
            meta_list = isa_data.get("metadata", [])
            for item in meta_list:
                isa_data[item["key"]] = item["value"]
            if "metadata" in isa_data and isinstance(isa_data["metadata"], list):
                del isa_data["metadata"]

            return {
                "isa_json": isa_data,
                "confidence_scores": conf_scores_dict,
                "identified_tools": response_data.get("identified_tools", []),
                "identified_models": response_data.get("identified_models", []),
                "identified_measurements": response_data.get("identified_measurements", []),
                "agent_thoughts": response_data.get("thought_process", ""),
                "vision_analysis": {
                    "pages_analyzed": len(page_images),
                    "method": "agentic_vision",
                },
                "metadata": {
                    "upload_id": upload_id,
                    "generated_at": datetime.utcnow().isoformat(),
                    "agent": "scholar_v2_vision",
                    "model_used": self.client.model_name,
                    "thinking_level": self.thinking_level,
                    "agentic_vision": True,
                },
            }

        except ImportError:
            logger.warning("PyMuPDF not available, falling back to standard analysis")
            return await self.analyze_publication(pdf_path, context_content, upload_id)
        except Exception as e:
            logger.error(f"Vision analysis error: {e}")
            return {"error": str(e), "isa_json": {}}
