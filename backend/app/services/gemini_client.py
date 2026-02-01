"""
VeriFlow - Gemini API Client Wrapper
Per SPEC.md Section 4.2 - Direct Gemini API calls with session state,
logging, and rate limit handling.
"""

import os
import time
import json
import uuid
import random
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core import exceptions as google_exceptions

# Configure standard logger
logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Wrapper for Gemini API with session support, automatic retries for rate limits,
    and comprehensive file logging for debugging.
    """
    
    # Model configuration
    PREFERRED_MODELS = [
        "gemini-3-flash-preview", 
        "gemini-pro-latest",
        "gemini-2.0-flash",
    ]
    
    # Safety settings - permissive for scientific content
    SAFETY_SETTINGS = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    }

    def __init__(self, api_key: Optional[str] = None, enable_logging: bool = True):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Optional API key. Falls back to GEMINI_API_KEY env var.
            enable_logging: If True, saves detailed request/response logs to 'logs/'
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Please set the environment variable or pass api_key."
            )
        
        self.enable_logging = enable_logging
        self.log_dir = Path("logs")
        if self.enable_logging:
            self.log_dir.mkdir(exist_ok=True)
            
        genai.configure(api_key=self.api_key)
        self.model_name = self._select_model()
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings=self.SAFETY_SETTINGS,
        )

    def _select_model(self) -> str:
        """Select the best available model from the preferred list."""
        try:
            # Note: List models can be slow, sometimes better to just force set if known
            available_models = [m.name for m in genai.list_models()]
            for preferred in self.PREFERRED_MODELS:
                full_name = f"models/{preferred}"
                if full_name in available_models:
                    return preferred
            return self.PREFERRED_MODELS[0]
        except Exception:
            return self.PREFERRED_MODELS[0]

    def _log_interaction(self, method: str, prompt: str, system_instr: str, response: str, error: str = None):
        """Saves interaction details to a JSON file for analysis."""
        if not self.enable_logging:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = self.log_dir / f"{timestamp}_{method}_{unique_id}.json"

        log_data = {
            "timestamp": datetime.now().isoformat(),
            "model": self.model_name,
            "method": method,
            "system_instruction": system_instr,
            "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
            "full_prompt": prompt,
            "response": response,
            "error": str(error) if error else None
        }

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2)
            # print(f"  [Log] Saved interaction to {filename}") # Uncomment for verbose stdout
        except Exception as e:
            print(f"Warning: Failed to write log file: {e}")

    def _retry_request(self, func, *args, **kwargs):
        """
        Executes a function with exponential backoff for Rate Limit (429) errors.
        """
        max_retries = 5
        base_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            
            except google_exceptions.ResourceExhausted as e:
                # 429 Error - Rate Limit Exceeded
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"  [Rate Limit] 429 encountered. Retrying in {delay:.2f}s (Attempt {attempt + 1}/{max_retries})...")
                time.sleep(delay)
                
            except google_exceptions.InternalServerError:
                # 500 Error - Gemini Internal Server Error (sometimes transient)
                delay = 2.0
                print(f"  [API Error] 500 encountered. Retrying in {delay}s...")
                time.sleep(delay)
                
            except Exception as e:
                # Other errors (Auth, Invalid Argument) fail immediately
                raise e
                
        raise TimeoutError(f"Max retries exceeded for Gemini API call after {max_retries} attempts.")

    def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 8192,
    ) -> str:
        """Generate content with retry logic and logging."""
        
        # Configure the specific model instance for this call
        # (Needed because system_instruction is set at init time for GenerativeModel)
        active_model = self.model
        if system_instruction:
            active_model = genai.GenerativeModel(
                model_name=self.model_name,
                safety_settings=self.SAFETY_SETTINGS,
                system_instruction=system_instruction,
            )
        
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

        def _call_api():
            return active_model.generate_content(
                prompt,
                generation_config=generation_config,
            )

        try:
            response = self._retry_request(_call_api)
            self._log_interaction("generate_content", prompt, system_instruction, response.text)
            return response.text
        except Exception as e:
            self._log_interaction("generate_content", prompt, system_instruction, None, error=e)
            raise e

    def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """Generate structured JSON output with retry logic and logging."""
        
        json_prompt = f"{prompt}\n\nRespond ONLY with valid JSON. No markdown, no explanation, just the JSON object."
        
        try:
            # We reuse generate_content's internal logic but call it directly to control logging better
            # or just call generate_content and let it log, but we want to log the PARSED json result status
            
            response_text = self.generate_content(
                prompt=json_prompt,
                system_instruction=system_instruction,
                max_output_tokens=8192, # Ensure enough tokens for JSON
                temperature=temperature,
            )
            
            # Clean response
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            try:
                parsed = json.loads(cleaned)
                return parsed
            except json.JSONDecodeError as e:
                # Log the failure specifically
                self._log_interaction("json_parse_error", json_prompt, system_instruction, response_text, error=e)
                raise ValueError(f"Failed to parse Gemini response as JSON: {e}")

        except Exception as e:
            # Error already logged in generate_content or caught here
            raise e

# Global client instance
_gemini_client: Optional[GeminiClient] = None

def get_gemini_client() -> GeminiClient:
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client