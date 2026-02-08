import os
import json
import hashlib
import logging
import json_repair
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

from google import genai
from google.genai import types

from app.config import config

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Gemini Client using the google-genai SDK.
    
    Features:
    - Robust JSON Parsing: Uses json_repair to handle Markdown backticks and malformed JSON.
    - Chain of Thought Extraction: Captures reasoning traces from Gemini models.
    - Local Caching: Hashes inputs to cache results during development.
    - Config Integration: Loads API keys and model settings from app config.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables.")

        # Initialize the Google GenAI Client
        self.client = genai.Client(api_key=self.api_key)

        # Caching Setup
        # Safely retrieve cache setting from config, defaulting to False if method missing
        self.cache_enabled = getattr(config, "is_cache_enabled", lambda: False)()
        self.cache_file = Path("genai_cache.json")
        
        # Default fallback
        self.model_name = "gemini-3.0-flash" 

    # --- Caching Logic ---

    def _calculate_hash(self, *args) -> str:
        """Generates a consistent MD5 hash from input arguments for cache keys."""
        hasher = hashlib.md5()
        for arg in args:
            hasher.update(str(arg).encode("utf-8"))
        return hasher.hexdigest()

    def _calculate_file_hash(self, file_path: str) -> str:
        """Generates MD5 hash for a file content to detect changes."""
        hasher = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
        except FileNotFoundError:
            return "file_not_found"
        return hasher.hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieves result from local JSON cache if enabled."""
        if not self.cache_enabled or not self.cache_file.exists():
            return None
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
            return cache.get(cache_key)
        except Exception:
            return None

    def _save_to_cache(self, cache_key: str, data: Dict[str, Any]):
        """Saves result to local JSON cache if enabled."""
        if not self.cache_enabled:
            return
        try:
            cache = {}
            if self.cache_file.exists():
                try:
                    with open(self.cache_file, "r", encoding="utf-8") as f:
                        cache = json.load(f)
                except json.JSONDecodeError:
                    pass
            cache[cache_key] = data
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write to cache: {e}")

    # --- Robust Parsing & Extraction ---

    def _extract_thoughts(self, response: Any) -> List[str]:
        """Extracts 'Thought' content from the Gemini response candidates."""
        thoughts = []
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content:
                    for part in candidate.content.parts:
                        # 1. Check for explicit 'thought' attribute (Gemini 2.0/3.0)
                        if hasattr(part, 'thought') and part.thought:
                            thoughts.append(part.text)
        return thoughts

    def _robust_parse_json(self, text: str) -> Dict[str, Any]:
        """
        Robustly parses JSON using json_repair.
        Handles Markdown code blocks and malformed syntax.
        """
        try:
            clean_text = text.strip()
            # Strip Markdown Code Blocks
            if clean_text.startswith("```"):
                # Remove first line (e.g., ```json)
                newline_index = clean_text.find("\n")
                if newline_index != -1:
                    clean_text = clean_text[newline_index+1:]
                # Remove trailing ```
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
            
            # Use json_repair
            parsed = json_repair.loads(clean_text)
            
            if isinstance(parsed, (dict, list)):
                return parsed
            else:
                return {"raw_parsed": parsed}
                
        except Exception as e:
            logger.error(f"JSON Parsing failed: {e}")
            return {"error": "Parsing failed", "raw": text}

    # --- Public API Methods ---

    async def generate_content(
        self, 
        prompt: str, 
        model: str = None,
        response_schema: Any = None
    ) -> Dict[str, Any]:
        """
        Generates content from a text prompt.
        """
        target_model = model or self.model_name
        
        # Check Cache
        if self.cache_enabled:
            cache_key = self._calculate_hash(prompt, target_model, str(response_schema))
            cached = self._get_from_cache(cache_key)
            if cached:
                logger.info(f"generate_content Cache hit")
                return cached

        # Config
        gen_config = types.GenerateContentConfig(
            response_mime_type="application/json" if response_schema else "text/plain",
            response_schema=response_schema
        )

        try:
            contents = [types.Content(parts=[types.Part.from_text(text=prompt)])]
            
            response = self.client.models.generate_content(
                model=target_model,
                contents=contents,
                config=gen_config
            )

            # Process
            thoughts = self._extract_thoughts(response)
            
            # Parsing Logic
            result = None
            if response.parsed:
                if hasattr(response.parsed, 'model_dump'):
                    result = response.parsed.model_dump()
                else:
                    result = response.parsed
            
            # Fallback if parsed is None (schema failure) or no schema requested
            if result is None:
                if response.text:
                    result = self._robust_parse_json(response.text)
                else:
                    result = {"error": "Empty response text"}

            output = result
            
            if self.cache_enabled:
                self._save_to_cache(cache_key, output)
            return output

        except Exception as e:
            logger.error(f"Gemini generate_content error: {e}")
            return {"error": str(e)}

    async def analyze_file(
        self, 
        file_path: str, 
        prompt: str, 
        model: str = None
    ) -> Dict[str, Any]:
        """
        Analyzes a local file (Multimodal).
        """
        target_model = model or self.model_name
        if self.cache_enabled: #This should be configurable
            file_hash = self._calculate_file_hash(file_path)
            cache_key = self._calculate_hash(file_hash, prompt, target_model)
            cached = self._get_from_cache(cache_key)
            if cached:
                logger.info(f"Analyse file Cache hit")
                return cached

        try:
            with open(file_path, "rb") as f:
                file_data = f.read()

            mime_type = "application/pdf"
            if file_path.endswith(".txt"): mime_type = "text/plain"
            
            file_part = types.Part.from_bytes(data=file_data, mime_type=mime_type)
            text_part = types.Part.from_text(text=prompt)
            
            # Force JSON for analysis results
            gen_config = types.GenerateContentConfig(
                response_mime_type="application/json"
            )

            response = self.client.models.generate_content(
                model=target_model,
                contents=[types.Content(parts=[file_part, text_part])],
                config=gen_config
            )

            thoughts = self._extract_thoughts(response)
            
            # Robust Parse
            result = self._robust_parse_json(response.text)

            output = result
            if self.cache_enabled:
                self._save_to_cache(cache_key, output)
            return output

        except Exception as e:
            logger.error(f"Gemini analyze_file error: {e}")
            return {"error": str(e)}