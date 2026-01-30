"""
VeriFlow - Scholar Agent
Per SPEC.md Section 4.3 - PDF parsing, ISA extraction, metadata population

The Scholar Agent is responsible for:
1. Parsing scientific publications (PDF text, figures, diagrams)
2. Extracting the ISA hierarchy (Investigation → Study → Assay)
3. Identifying data objects (Measurements, Tools, Models)
4. Generating confidence scores (0-100%)
5. Outputting in ISA-JSON format
"""

import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import fitz  # PyMuPDF

from app.services.gemini_client import get_gemini_client
from app.services.minio_client import minio_service


# System prompt per SPEC.md Section 4.3
SCHOLAR_SYSTEM_PROMPT = """You are the Scholar Agent for VeriFlow, a Research Reliability Engineer system.

Your role is to:

1. Parse scientific publications (PDF text, figures, diagrams)
2. Extract the ISA hierarchy:
   - Investigation: Overall research context (title, description, publications, contacts)
   - Study: Experimental design (subjects, factors, protocols)
   - Assay: Specific measurement process (measurement type, technology, samples)
3. Identify data objects:
   - Measurements (input data - e.g., MRI scans, genomic data)
   - Tools (processing software - e.g., preprocessing scripts, analysis tools)
   - Models (pre-trained weights - e.g., neural network models)
4. Generate confidence scores (0-100%) for each extracted property based on:
   - Explicit mention in text: 90-100%
   - Strongly implied: 70-89%
   - Weakly implied or inferred: 50-69%
   - Uncertain or assumed: Below 50%
5. Output in strict ISA-JSON format

When a Context File is provided, use it to supplement ambiguous information and increase confidence scores for properties it clarifies.

IMPORTANT: Your response must be valid JSON following the exact schema provided in the prompt."""


class ScholarAgent:
    """
    Scholar Agent for PDF parsing and ISA extraction.
    
    Extracts methodological information from scientific publications
    and structures it as ISA-JSON with confidence scores.
    """
    
    def __init__(self):
        """Initialize Scholar Agent with Gemini client."""
        self.gemini = get_gemini_client()
    
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """
        Extract text content from PDF using PyMuPDF.
        
        Args:
            pdf_bytes: Raw PDF file content
            
        Returns:
            Extracted text content
        """
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                text_parts.append(f"[Page {page_num + 1}]\n{text}")
        
        doc.close()
        return "\n\n".join(text_parts)
    
    def extract_text_from_pdf_url(self, bucket: str, object_name: str) -> str:
        """
        Extract text from a PDF stored in MinIO.
        
        Args:
            bucket: MinIO bucket name
            object_name: Object path in bucket
            
        Returns:
            Extracted text content
        """
        pdf_bytes = minio_service.download_file(bucket, object_name)
        return self.extract_text_from_pdf(pdf_bytes)
    
    async def analyze_publication(
        self,
        pdf_text: str,
        context_content: Optional[str] = None,
        upload_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a publication and extract ISA hierarchy.
        
        Args:
            pdf_text: Extracted text from PDF
            context_content: Optional supplemental context file content
            upload_id: Optional upload ID for reference
            
        Returns:
            Dictionary with:
            - isa_json: ISA hierarchy structure
            - confidence_scores: Scores for each property
            - identified_tools: List of identified processing tools
            - identified_models: List of identified ML models
            - identified_measurements: List of identified data types
        """
        # Build the prompt
        prompt = self._build_analysis_prompt(pdf_text, context_content)
        
        # Generate response using Gemini
        try:
            response = self.gemini.generate_json(
                prompt=prompt,
                system_instruction=SCHOLAR_SYSTEM_PROMPT,
                temperature=0.3,  # Lower for consistent structured output
            )
            
            # Parse and validate the response
            result = self._parse_response(response, upload_id)
            return result
            
        except Exception as e:
            # Return error structure
            return {
                "error": str(e),
                "isa_json": None,
                "confidence_scores": {},
                "identified_tools": [],
                "identified_models": [],
                "identified_measurements": [],
            }
    
    def _build_analysis_prompt(
        self,
        pdf_text: str,
        context_content: Optional[str] = None,
    ) -> str:
        """Build the analysis prompt for Gemini."""
        
        # Truncate PDF text if too long (Gemini context limits)
        max_text_length = 100000  # ~25k tokens
        if len(pdf_text) > max_text_length:
            pdf_text = pdf_text[:max_text_length] + "\n\n[Text truncated due to length...]"
        
        context_section = ""
        if context_content:
            context_section = f"""
CONTEXT FILE (Use this to supplement ambiguous information):
---
{context_content}
---
"""
        
        prompt = f"""Analyze the following scientific publication and extract the ISA (Investigation-Study-Assay) hierarchy.

{context_section}

PUBLICATION TEXT:
---
{pdf_text}
---

Extract and return a JSON object with the following structure:

{{
  "investigation": {{
    "id": "inv_1",
    "title": "string - main title of the research",
    "description": "string - overall research description",
    "properties": [
      {{
        "id": "string - unique property id like inv-title",
        "name": "string - property name",
        "value": "string - extracted value",
        "source_page": number or null,
        "source_text": "string - quoted text from source",
        "confidence": number 0-100
      }}
    ],
    "studies": [
      {{
        "id": "study_1",
        "title": "string",
        "description": "string",
        "properties": [
          {{
            "id": "string",
            "name": "string",
            "value": "string",
            "source_page": number or null,
            "source_text": "string",
            "confidence": number 0-100
          }}
        ],
        "assays": [
          {{
            "id": "assay_1",
            "name": "string - assay name like 'Training Pipeline'",
            "description": "string",
            "measurement_type": "string - e.g., 'segmentation', 'classification'",
            "technology_type": "string - e.g., 'deep learning', 'image processing'",
            "steps": [
              {{
                "id": "step_1",
                "name": "string",
                "description": "string"
              }}
            ]
          }}
        ]
      }}
    ]
  }},
  "confidence_scores": {{
    "property_id": {{
      "value": number 0-100,
      "source_page": number or null,
      "source_text": "string"
    }}
  }},
  "identified_tools": [
    {{
      "id": "tool_1",
      "name": "string - tool name",
      "description": "string",
      "source_url": "string or null - GitHub, documentation link",
      "confidence": number 0-100
    }}
  ],
  "identified_models": [
    {{
      "id": "model_1",
      "name": "string - model name",
      "architecture": "string - e.g., U-Net, ResNet",
      "pretrained": boolean,
      "source_url": "string or null",
      "confidence": number 0-100
    }}
  ],
  "identified_measurements": [
    {{
      "id": "measurement_1",
      "name": "string - data type name",
      "data_type": "string - e.g., 'DCE-MRI', 'CT scan', 'genomic data'",
      "format": "string - e.g., 'DICOM', 'NIfTI', 'FASTQ'",
      "confidence": number 0-100
    }}
  ]
}}

Be thorough in extracting:
1. All processing steps mentioned in Methods section
2. All software tools and their versions
3. All data types and formats
4. Sample sizes and subject information
5. Model architectures and training details

Ensure all confidence scores accurately reflect how certain the information is based on the source text."""
        
        return prompt
    
    def _parse_response(
        self,
        response: Dict[str, Any],
        upload_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Parse and validate the Gemini response."""
        
        # Ensure all required fields exist
        result = {
            "isa_json": response.get("investigation", {}),
            "confidence_scores": response.get("confidence_scores", {}),
            "identified_tools": response.get("identified_tools", []),
            "identified_models": response.get("identified_models", []),
            "identified_measurements": response.get("identified_measurements", []),
        }
        
        # Add metadata
        result["metadata"] = {
            "upload_id": upload_id,
            "generated_at": datetime.utcnow().isoformat(),
            "agent": "scholar",
            "model": self.gemini.model_name,
        }
        
        return result
    
    def build_hierarchy_response(
        self,
        scholar_output: Dict[str, Any],
        upload_id: str,
    ) -> Dict[str, Any]:
        """
        Build the hierarchy response format expected by the frontend.
        
        Args:
            scholar_output: Output from analyze_publication
            upload_id: The upload ID
            
        Returns:
            Hierarchy structure matching the API response format
        """
        isa_json = scholar_output.get("isa_json", {})
        confidence_scores = scholar_output.get("confidence_scores", {})
        
        # Build the hierarchy structure expected by frontend
        hierarchy = {
            "investigation": {
                "id": isa_json.get("id", "inv_1"),
                "title": isa_json.get("title", "Unknown Investigation"),
                "description": isa_json.get("description", ""),
                "properties": isa_json.get("properties", []),
                "studies": isa_json.get("studies", []),
            }
        }
        
        # Build confidence scores in expected format
        confidence = {
            "upload_id": upload_id,
            "generated_at": datetime.utcnow().isoformat(),
            "scores": confidence_scores,
        }
        
        return {
            "hierarchy": hierarchy,
            "confidence_scores": confidence,
            "identified_tools": scholar_output.get("identified_tools", []),
            "identified_models": scholar_output.get("identified_models", []),
            "identified_measurements": scholar_output.get("identified_measurements", []),
        }


# Global agent instance
scholar_agent = ScholarAgent()
