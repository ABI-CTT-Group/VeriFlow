import os
import time
import json
import uuid
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

class MultiModalGeminiClient:
    """
    V2 Client: Supports native file uploads (PDF, Video, Images) and 
    multimodal prompting with FULL LOGGING.
    """
    
    PREFERRED_MODELS = [
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-3-flash-preview",
        "gemini-2.5-flash"
    ]
    
    SAFETY_SETTINGS = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    }

    def __init__(self, api_key: Optional[str] = None, enable_logging: bool = True):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found.")
        
        # Setup Logging
        self.enable_logging = enable_logging
        self.log_dir = Path("logs")
        if self.enable_logging:
            self.log_dir.mkdir(exist_ok=True)

        genai.configure(api_key=self.api_key)
        self.model_name = self._select_valid_model()
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings=self.SAFETY_SETTINGS,
        )

    def _select_valid_model(self) -> str:
        """Selects the first available model from the preference list."""
        try:
            available_models = [m.name for m in genai.list_models()]
            for preferred in self.PREFERRED_MODELS:
                if f"models/{preferred}" in available_models:
                    return preferred
            return self.PREFERRED_MODELS[0]
        except Exception:
            return self.PREFERRED_MODELS[0]

    def _log_interaction(self, method: str, contents: Any, system_instr: str, response: Any, error: str = None):
        """Saves interaction details to a JSON file."""
        if not self.enable_logging:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = self.log_dir / f"{timestamp}_{method}_{unique_id}.json"

        # Create a preview of the contents (handle file objects)
        content_preview = str(contents)[:500] + "..." if len(str(contents)) > 500 else str(contents)

        log_data = {
            "timestamp": datetime.now().isoformat(),
            "model": self.model_name,
            "method": method,
            "system_instruction": system_instr,
            "contents_preview": content_preview,
            "response": response,
            "error": str(error) if error else None
        }

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to write log file: {e}")

    def upload_file(self, file_path: str, mime_type: str = None) -> Any:
        """Uploads a file to Gemini's File API."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        print(f"  [MultiModalClient] Uploading {os.path.basename(file_path)}...")
        file_ref = genai.upload_file(file_path, mime_type=mime_type)
        
        while file_ref.state.name == "PROCESSING":
            time.sleep(2)
            file_ref = genai.get_file(file_ref.name)
            
        if file_ref.state.name == "FAILED":
            raise ValueError(f"File upload failed: {file_ref.state.name}")
            
        print(f"  [MultiModalClient] Ready: {file_ref.name}")
        return file_ref

    def generate_json(
        self,
        contents: Union[str, List[Any]], 
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Generates structured JSON from multimodal input.
        """
        active_model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings=self.SAFETY_SETTINGS,
            system_instruction=system_instruction,
        )

        prompt_suffix = "\n\nReturn the result strictly as valid JSON."
        
        if isinstance(contents, str):
            contents = contents + prompt_suffix
        elif isinstance(contents, list):
            contents.append(prompt_suffix)

        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=8192,
            response_mime_type="application/json"
        )

        try:
            response = active_model.generate_content(
                contents,
                generation_config=generation_config,
            )
            
            # Clean response text
            text = response.text.strip()
            if text.startswith("```json"): text = text[7:]
            if text.startswith("```"): text = text[3:]
            if text.endswith("```"): text = text[:-3]
            
            parsed_json = json.loads(text.strip())
            
            # SUCCESS LOG
            self._log_interaction("generate_json", contents, system_instruction, parsed_json)
            
            return parsed_json
            
        except Exception as e:
            # ERROR LOG
            self._log_interaction("generate_json_error", contents, system_instruction, None, error=e)
            raise e