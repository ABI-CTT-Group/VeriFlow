import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Type

# NEW SDK IMPORT
from google import genai
from google.genai import types

from app.config import config
from app.models.schemas import AnalysisResult

logger = logging.getLogger(__name__)

# Configure standard logger
logger = logging.getLogger(__name__)

class GeminiClient:
    """
    Gemini Client using the google-genai SDK with Gemini 3 features:
    - Pydantic Structured Outputs (response_schema)
    - Thinking Level control (thinking_config)
    - Grounding with Google Search
    - Native PDF upload for multimodal analysis
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found.")

        # Initialize the Client
        self.client = genai.Client(api_key=self.api_key)

        self.cache_enabled = config.is_cache_enabled()
        self.cache_file = Path("genai_cache.json")
        self.model_name = "gemini-3-flash-preview"

    def _calculate_file_hash(self, file_path: str) -> str:
        """MD5 hash for local caching key generation."""
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _build_generation_config(
        self,
        system_instruction: Optional[str] = None,
        temperature: float = 1.0,
        response_schema: Optional[Type] = None,
        thinking_level: Optional[str] = None,
        enable_grounding: bool = False,
    ) -> types.GenerateContentConfig:
        """Build a GenerateContentConfig with Gemini 3 features."""
        config_kwargs: Dict[str, Any] = {
            "temperature": temperature,
        }

        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        # Structured output via Pydantic schema
        if response_schema:
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_schema"] = response_schema

        # Gemini 3: Thinking Level control via thinkingBudget
        if thinking_level:
            budget_map = {"HIGH": 24576, "MEDIUM": 8192, "LOW": 2048, "NONE": 0}
            budget = budget_map.get(thinking_level.upper(), 8192) if isinstance(thinking_level, str) else thinking_level
            config_kwargs["thinking_config"] = types.ThinkingConfig(
                thinking_budget=budget,
                include_thoughts=True,
            )

        # Gemini 3: Grounding with Google Search
        if enable_grounding:
            config_kwargs["tools"] = [
                types.Tool(google_search=types.GoogleSearch())
            ]

        return types.GenerateContentConfig(**config_kwargs)

    def analyze_file(
        self,
        file_path: str,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 1.0,
        response_schema: Optional[Type] = None,
        thinking_level: Optional[str] = None,
        enable_grounding: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyze a file (PDF) using Gemini with native upload.

        Args:
            file_path: Path to the PDF file
            prompt: Analysis prompt
            system_instruction: System instruction for the model
            temperature: Generation temperature (default 1.0 per Gemini 3 guidance)
            response_schema: Pydantic model for structured output
            thinking_level: Gemini 3 thinking level (LOW, MEDIUM, HIGH)
            enable_grounding: Enable Grounding with Google Search

        Returns:
            Parsed response as dictionary
        """
        # Use AnalysisResult as default schema for file analysis
        if response_schema is None:
            response_schema = AnalysisResult

        # Local Cache Check
        if self.cache_enabled:
            file_hash = self._calculate_file_hash(file_path)
            cache_key = f"{self.model_name}|{file_hash}|{hashlib.md5(prompt.encode()).hexdigest()}"

            if self.cache_file.exists():
                with open(self.cache_file, "r") as f:
                    cache = json.load(f)
                    if cache_key in cache:
                        logger.info(f"[Cache] Hit for {os.path.basename(file_path)}")
                        return cache[cache_key]

        logger.info(f"[API] Uploading {os.path.basename(file_path)}...")

        # Upload File
        with open(file_path, "rb") as f:
            file_ref = self.client.files.upload(
                file=f,
                config=types.UploadFileConfig(mime_type="application/pdf"),
            )

        # Generate Content with Gemini 3 features
        logger.info("[API] Generating analysis with Gemini 3...")

        gen_config = self._build_generation_config(
            system_instruction=system_instruction,
            temperature=temperature,
            response_schema=response_schema,
            thinking_level=thinking_level,
            enable_grounding=enable_grounding,
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[file_ref, prompt],
            config=gen_config,
        )

        # Parse Response
        if response.parsed:
            result_dict = response.parsed.model_dump()
        else:
            result_dict = json.loads(response.text)

        # Save to Local Cache
        if self.cache_enabled:
            current_cache = {}
            if self.cache_file.exists():
                try:
                    with open(self.cache_file, "r") as f:
                        current_cache = json.load(f)
                except Exception:
                    pass

            current_cache[cache_key] = result_dict
            with open(self.cache_file, "w") as f:
                json.dump(current_cache, f, indent=2)

        return result_dict

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 1.0,
        response_schema: Optional[Type] = None,
        thinking_level: Optional[str] = None,
        enable_grounding: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate text/structured output without file upload.
        Used by Engineer and Reviewer agents for text-based generation.

        Args:
            prompt: The generation prompt
            system_instruction: System instruction for the model
            temperature: Generation temperature (default 1.0 per Gemini 3 guidance)
            response_schema: Pydantic model for structured output
            thinking_level: Gemini 3 thinking level (LOW, MEDIUM, HIGH)
            enable_grounding: Enable Grounding with Google Search

        Returns:
            Parsed response as dictionary (if response_schema) or raw text dict
        """
        logger.info("[API] Generating content with Gemini 3...")

        gen_config = self._build_generation_config(
            system_instruction=system_instruction,
            temperature=temperature,
            response_schema=response_schema,
            thinking_level=thinking_level,
            enable_grounding=enable_grounding,
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[prompt],
            config=gen_config,
        )

        # Parse Response
        if response_schema and response.parsed:
            return response.parsed.model_dump()
        elif response_schema:
            return json.loads(response.text)
        else:
            return {"text": response.text}

    def generate_with_history(
        self,
        messages: list,
        system_instruction: Optional[str] = None,
        temperature: float = 1.0,
        response_schema: Optional[Type] = None,
        thinking_level: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Multi-turn generation with thought signature preservation.
        Used for iterative agent loops (e.g., Reviewer validate-fix-revalidate).

        Gemini 3 requires thought signatures to be preserved across turns
        for maintaining reasoning chains in function calling and multi-turn.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                      Include 'thought_signatures' from previous responses.
            system_instruction: System instruction for the model
            temperature: Generation temperature
            response_schema: Pydantic model for structured output
            thinking_level: Gemini 3 thinking level

        Returns:
            Dict with 'result' and 'thought_signatures' for next turn
        """
        logger.info("[API] Multi-turn generation with thought signatures...")

        gen_config = self._build_generation_config(
            system_instruction=system_instruction,
            temperature=temperature,
            response_schema=response_schema,
            thinking_level=thinking_level,
        )

        # Build contents list preserving thought signatures
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Preserve thought signatures from previous model responses
            thought_sigs = msg.get("thought_signatures")
            if thought_sigs and role == "model":
                # Include thought signature parts for Gemini 3 reasoning chain
                parts = []
                for sig in thought_sigs:
                    parts.append(types.Part(thought=True, text=sig))
                parts.append(types.Part(text=content))
                contents.append(types.Content(role=role, parts=parts))
            else:
                contents.append(
                    types.Content(
                        role=role, parts=[types.Part(text=content)]
                    )
                )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=gen_config,
        )

        # Extract thought signatures from response for next turn
        thought_signatures = []
        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "thought") and part.thought:
                    thought_signatures.append(part.text)

        # Parse result
        if response_schema and response.parsed:
            result = response.parsed.model_dump()
        elif response_schema:
            result = json.loads(response.text)
        else:
            result = {"text": response.text}

        return {
            "result": result,
            "thought_signatures": thought_signatures,
        }
