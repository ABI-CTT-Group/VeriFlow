import os
import time
import json
import uuid
import hashlib
import logging
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core import exceptions as google_exceptions

logger = logging.getLogger(__name__)

# --- RATE LIMITER ---
class RateLimiter:
    """Enforces requests per minute (RPM) limits."""
    def __init__(self, rpm: int = 15):
        self.rpm = rpm
        self.delay = 60.0 / self.rpm
        self.last_call = 0

    def wait(self):
        """Blocks execution to ensure RPM limit is respected."""
        now = time.time()
        elapsed = now - self.last_call
        if elapsed < self.delay:
            sleep_time = self.delay - elapsed
            if sleep_time > 0.1:
                print(f"  [RateLimiter] Sleeping {sleep_time:.2f}s...")
            time.sleep(sleep_time)
        self.last_call = time.time()


class MultiModalGeminiClient:
    """
    V2 Client: Supports smart caching (Option B), rate limiting, and native PDF uploads.
    """
    
    PREFERRED_MODELS = [
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-2.5-flash"
    ]
    
    SAFETY_SETTINGS = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    }

    def __init__(self, api_key: Optional[str] = None, enable_logging: bool = True, cache_file: str = "genai_cache.json"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found.")
        
        # Setup Paths
        self.enable_logging = enable_logging
        self.log_dir = Path("logs")
        self.cache_file = Path(cache_file)
        
        if self.enable_logging:
            self.log_dir.mkdir(exist_ok=True)

        # Rate Limiter (Default 15 RPM for free tier safety)
        self.rate_limiter = RateLimiter(rpm=15)

        genai.configure(api_key=self.api_key)
        self.model_name = self._select_valid_model()
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings=self.SAFETY_SETTINGS,
        )

    # --- HELPER: ROBUST FILE HASHING ---
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        Calculates MD5 hash of a file.
        Uses chunked reading to safely handle large files (20MB+) without memory issues.
        """
        # FUTURE: Switch to hashlib.sha256() if collision resistance becomes critical.
        # For caching prompt results, MD5 is faster and sufficient.
        hasher = hashlib.md5() 
        chunk_size = 8192  # 8KB chunks

        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            # Fallback or re-raise depending on strictness
            print(f"  [Hash Error] Could not read {file_path}: {e}")
            raise e

    # --- CACHE UTILS ---
    def _load_cache(self) -> Dict[str, Any]:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"  [Cache] Corrupt file, starting fresh: {e}")
        return {}

    def _save_cache(self, cache: Dict[str, Any]):
        try:
            temp = self.cache_file.with_suffix('.tmp')
            with open(temp, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2)
            os.replace(temp, self.cache_file)
        except Exception as e:
            print(f"  [Cache] Save failed: {e}")

    def _get_cache_key(self, prompt: str, system_instr: Optional[str], file_hash: Optional[str]) -> str:
        """Constructs a deterministic cache key."""
        components = [f"MODEL:{self.model_name}"]
        
        if system_instr:
            components.append(f"SYS:{hashlib.md5(system_instr.encode()).hexdigest()}")
        
        # Clean prompt to avoid misses on whitespace
        clean_prompt = re.sub(r'\s+', ' ', prompt.strip().lower())
        components.append(f"TXT:{hashlib.md5(clean_prompt.encode()).hexdigest()}")
        
        if file_hash:
            components.append(f"FILE_HASH:{file_hash}")
            
        return "|".join(components)

    # --- CORE METHODS ---
    def _select_valid_model(self) -> str:
        try:
            # Quick check against preferred list
            available = [m.name for m in genai.list_models()]
            for pref in self.PREFERRED_MODELS:
                if f"models/{pref}" in available:
                    return pref
            return self.PREFERRED_MODELS[0]
        except:
            return self.PREFERRED_MODELS[0]

    def _log_interaction(self, method: str, contents: Any, response: Any, cached: bool, error: str = None):
        if not self.enable_logging: return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        status = "CACHE_HIT" if cached else ("ERROR" if error else "API_CALL")
        unique_id = str(uuid.uuid4())[:8]
        filename = self.log_dir / f"{timestamp}_{status}_{method}_{unique_id}.json"
        
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "model": self.model_name,
            "contents": str(contents)[:500] + "...",
            "response": response,
            "error": str(error)
        }
        
        try:
            with open(filename, "w") as f: json.dump(log_data, f, indent=2)
        except: pass

    # --- MAIN ENTRY POINT (OPTION B IMPLEMENTATION) ---
    def analyze_file(
        self, 
        file_path: str, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Smart Analysis: Checks cache using local file hash BEFORE uploading.
        Saves bandwidth and tokens.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # 1. Calculate Local Hash (MD5)
        # This handles small and large files (20MB+) safely via chunking
        file_hash = self._calculate_file_hash(file_path)
        
        # 2. Check Cache
        cache_key = self._get_cache_key(prompt, system_instruction, file_hash)
        cache = self._load_cache()
        
        if cache_key in cache:
            print(f"  [Cache] HIT! Skipping upload & generation for {os.path.basename(file_path)}")
            self._log_interaction("analyze_file", prompt, cache[cache_key], cached=True)
            return cache[cache_key]

        # 3. Cache Miss - Proceed to Upload
        print(f"  [Cache] MISS. Uploading {os.path.basename(file_path)}...")
        
        # Enforce rate limit before upload/generate sequence
        self.rate_limiter.wait()
        
        try:
            # A. Upload
            file_ref = genai.upload_file(file_path, mime_type="application/pdf")
            while file_ref.state.name == "PROCESSING":
                time.sleep(1)
                file_ref = genai.get_file(file_ref.name)
            
            if file_ref.state.name == "FAILED":
                raise ValueError(f"Upload failed: {file_ref.state.name}")

            # B. Generate
            active_model = genai.GenerativeModel(
                model_name=self.model_name,
                safety_settings=self.SAFETY_SETTINGS,
                system_instruction=system_instruction
            )
            
            final_prompt = [file_ref, prompt + "\n\nReturn strict JSON."]
            
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=8192,
                response_mime_type="application/json"
            )
            
            print(f"  [API] Generating analysis...")
            response = active_model.generate_content(final_prompt, generation_config=generation_config)
            
            # C. Parse
            text = response.text.strip()
            if text.startswith("```json"): text = text[7:]
            if text.startswith("```"): text = text[3:]
            if text.endswith("```"): text = text[:-3]
            
            parsed_json = json.loads(text.strip())
            
            # D. Save to Cache
            cache[cache_key] = parsed_json
            self._save_cache(cache)
            
            self._log_interaction("analyze_file", prompt, parsed_json, cached=False)
            return parsed_json

        except Exception as e:
            self._log_interaction("analyze_file", prompt, None, cached=False, error=str(e))
            raise e