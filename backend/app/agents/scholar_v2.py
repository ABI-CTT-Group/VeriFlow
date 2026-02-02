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
    Delegates caching and uploading logic to the smart client.
    """
    
    def __init__(self):
        self.client = MultiModalGeminiClient()
        self.agent_config = config.get_agent_config("scholar")
        self.prompt_version = "v2_multimodal" 
        
        # Apply config overrides if present
        cfg_model = self.agent_config.get("default_model")
        if cfg_model:
            # Note: Client will still validate if this model exists
            self.client.model_name = cfg_model

    async def analyze_publication(
        self,
        pdf_path: str,
        context_content: Optional[str] = None,
        upload_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a publication PDF file directly using smart caching.
        """
        if not os.path.exists(pdf_path):
             return {"error": f"File not found: {pdf_path}", "isa_json": None}

        try:
            # 1. Retrieve Prompts
            system_instruction = prompt_manager.get_prompt("scholar_system", self.prompt_version)
            analysis_prompt_tmpl = prompt_manager.get_prompt("scholar_analysis", self.prompt_version)
            
            # 2. Format the Text Prompt
            task_text = analysis_prompt_tmpl.format(
                context_section=f"Context Notes: {context_content}" if context_content else ""
            )
            
            # 3. Call Smart Client (Handles Hash -> Cache -> Upload -> Generate)
            # This implements Option B: It won't upload if the hash matches a cache entry.
            response_json = self.client.analyze_file(
                file_path=pdf_path,
                prompt=task_text,
                system_instruction=system_instruction,
                temperature=0.2
            )
            
            # 4. Format Output
            return self._format_output(response_json, upload_id)

        except Exception as e:
            # Fallback structure
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
                "mode": "multimodal_cached"
            }
        }