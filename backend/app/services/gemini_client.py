import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# NEW SDK IMPORT
from google import genai
from google.genai import types

from app.config import config
from app.models.schemas import AnalysisResult 

logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Gemini Client using Pydantic Structured Outputs.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found.")
        
        # Initialize the new Client
        self.client = genai.Client(api_key=self.api_key)
        
        self.cache_enabled = config.is_cache_enabled()
        self.cache_file = Path("genai_cache.json")
        self.model_name = "gemini-2.0-flash" # Default, can be overridden

    def _calculate_file_hash(self, file_path: str) -> str:
        """MD5 hash for local caching key generation."""
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def analyze_file(self, file_path: str, prompt: str, system_instruction: str = None, temperature: float = 1.0) -> Dict[str, Any]:
        # 1. Local Cache Check (If enabled in Config)
        if self.cache_enabled:
            file_hash = self._calculate_file_hash(file_path)
            cache_key = f"{self.model_name}|{file_hash}|{hashlib.md5(prompt.encode()).hexdigest()}"
            
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                    if cache_key in cache:
                        print(f"  [Cache] Hit for {os.path.basename(file_path)}")
                        return cache[cache_key]
        
        print(f"  [API] Uploading {os.path.basename(file_path)}...")

        # 2. Upload File (New SDK Syntax)
        # The new SDK automatically handles waiting for PROCESSING state if you use the right helpers,
        # but explicit uploading is safer for large PDFs.
        with open(file_path, "rb") as f:
            file_ref = self.client.files.upload(
                file=f,
                config=types.UploadFileConfig(mime_type="application/pdf")
            )
        
        # 3. Generate Content with Structured Output (The "Gemini 3" Way)
        print(f"  [API] Generating analysis with Schema...")
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[file_ref, prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature, # Use the passed temperature
                response_mime_type="application/json",
                response_schema=AnalysisResult
            )
        )

        # 4. Parse Response
        # The new SDK returns a parsed object if response_schema was used
        if response.parsed:
            result_dict = response.parsed.model_dump()
        else:
            # Fallback if parsing failed (rare with new SDK)
            result_dict = json.loads(response.text)

        # 5. Save to Local Cache (If enabled)
        if self.cache_enabled:
            current_cache = {}
            if self.cache_file.exists():
                try:
                    with open(self.cache_file, 'r') as f: current_cache = json.load(f)
                except: pass
            
            current_cache[cache_key] = result_dict
            with open(self.cache_file, 'w') as f:
                json.dump(current_cache, f, indent=2)

        return result_dict