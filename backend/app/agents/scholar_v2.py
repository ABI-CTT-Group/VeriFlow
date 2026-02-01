import os
from typing import Optional, Dict, Any
from datetime import datetime

# Import the new client and existing managers
from app.services.multimodal_client import MultiModalGeminiClient
from app.config import config
from app.services.prompt_manager import prompt_manager

class ScholarAgentV2:
    """
    Scholar Agent V2 (Multimodal).
    
    analyzes PDFs directly using Gemini's native vision capabilities
    rather than extracting text first.
    """
    
    def __init__(self):
        self.client = MultiModalGeminiClient()
        self.agent_config = config.get_agent_config("scholar")
        # Use a new default version or fallback to standard
        self.prompt_version = "v2_multimodal" 
        
        # Override client model if config specifies
        cfg_model = self.agent_config.get("default_model")
        if cfg_model:
            self.client.model_name = cfg_model

    async def analyze_publication(
        self,
        pdf_path: str,
        context_content: Optional[str] = None,
        upload_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a publication PDF file directly.
        """
        if not os.path.exists(pdf_path):
             return {"error": f"File not found: {pdf_path}", "isa_json": None}

        try:
            # 1. Upload PDF
            pdf_file = self.client.upload_file(pdf_path, mime_type="application/pdf")
            
            # 2. Get Prompts
            # Note: We use the *same* system prompt key if the instruction hasn't changed, 
            # or a new V2 key if we want specific visual instructions.
            system_instruction = prompt_manager.get_prompt("scholar_system", self.prompt_version)
            analysis_prompt_tmpl = prompt_manager.get_prompt("scholar_analysis", self.prompt_version)
            
            # 3. Format text part of the prompt
            # We no longer inject {pdf_text}, just context.
            task_text = analysis_prompt_tmpl.format(
                context_section=f"Context Notes: {context_content}" if context_content else ""
            )
            
            # 4. Construct Multimodal Payload
            # Order: [File Object, Text Instruction]
            contents = [pdf_file, task_text]
            
            # 5. Generate
            response_json = self.client.generate_json(
                contents=contents,
                system_instruction=system_instruction,
                temperature=0.2
            )
            
            # 6. Wrap result
            return self._format_output(response_json, upload_id)

        except Exception as e:
            return {
                "error": str(e),
                "isa_json": None,
                "confidence_scores": {},
                "identified_tools": [],
                "identified_models": [], 
                "identified_measurements": []
            }

    def _format_output(self, raw_json: Dict[str, Any], upload_id: str) -> Dict[str, Any]:
        """Standardizes output structure matching V1."""
        return {
            "isa_json": raw_json.get("investigation", {}),
            "confidence_scores": raw_json.get("confidence_scores", {}),
            "identified_tools": raw_json.get("identified_tools", []),
            "identified_models": raw_json.get("identified_models", []),
            "identified_measurements": raw_json.get("identified_measurements", []),
            "metadata": {
                "upload_id": upload_id,
                "generated_at": datetime.utcnow().isoformat(),
                "agent": "scholar_v2",
                "mode": "multimodal"
            }
        }