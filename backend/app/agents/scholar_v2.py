import os
from typing import Dict, Any, Optional
from datetime import datetime

from app.services.multimodal_client import MultiModalGeminiClient
from app.services.prompt_manager import prompt_manager
from app.config import config

class ScholarAgentV2:
    def __init__(self):
        self.client = MultiModalGeminiClient()
        
        # 1. Load Agent-Specific Config (e.g., which model alias to use)
        self.agent_config = config.get_agent_config("scholar")
        self.prompt_version = self.agent_config.get("default_prompt_version", "v2_multimodal")
        
        # 2. Resolve Model Alias to Actual API Parameters
        # config.yaml: agents.scholar.default_model -> "gemini-3.0-pro"
        model_alias = self.agent_config.get("default_model", "gemini-2.0-flash")
        
        # config.yaml: models["gemini-3.0-pro"] -> {api_model_name: ..., temperature: ...}
        self.model_params = config.get_model_params(model_alias)
        
        # 3. Apply Configuration to Client
        # Fallback to the alias itself if no mapping exists
        self.client.model_name = self.model_params.get("api_model_name", model_alias)
        
        # Store other params (like temperature) for use during generation
        self.temperature = self.model_params.get("temperature", 1.0)

    async def analyze_publication(
            self,
            pdf_path: str,
            context_content: Optional[str] = None,
            upload_id: Optional[str] = None,
        ) -> Dict[str, Any]:
        """
        Analyze a publication PDF file using configured model and parameters.
        """
        if not os.path.exists(pdf_path):
             return {"error": f"File not found: {pdf_path}"}

        try:
            # Retrieve Prompts
            system_instruction = prompt_manager.get_prompt("scholar_system", self.prompt_version)
            base_prompt = prompt_manager.get_prompt("scholar_analysis", self.prompt_version)
            
            full_prompt = f"{base_prompt}\nContext: {context_content or ''}"
            
            # Execute Client with Configured Parameters
            # We assume MultiModalGeminiClient.analyze_file accepts **kwargs or explicit params
            # If not, you might need to update the client to accept 'generation_config' overrides
            response_data = self.client.analyze_file(
                file_path=pdf_path,
                prompt=full_prompt,
                system_instruction=system_instruction
                # Note: If your client accepts temperature, pass it here:
                # temperature=self.temperature 
            )
            
            # --- DATA TRANSFORMATION (List -> Dict) ---
            # Convert 'confidence_scores' List[Metric] -> Dict[str, float]
            conf_scores_list = response_data.get("confidence_scores", [])
            conf_scores_dict = {item['name']: item['score'] for item in conf_scores_list}

            tools_list = response_data.get("identified_tools", [])
            
            isa_data = response_data.get("investigation", {})
            meta_list = isa_data.get("metadata", [])
            for item in meta_list:
                isa_data[item['key']] = item['value']
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
                    "model_used": self.client.model_name 
                }
            }

        except Exception as e:
            return {"error": str(e), "isa_json": {}}