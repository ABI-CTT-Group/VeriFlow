"""
VeriFlow - Gemini API Client Wrapper
Per SPEC.md Section 4.2 - Direct Gemini API calls with session state
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold


class GeminiClient:
    """
    Wrapper for Gemini API with session support.
    
    Provides methods for generating content with conversation history,
    handling structured outputs, and managing API configuration.
    """
    
    # Model configuration - fallback chain per implementation plan
    PREFERRED_MODELS = [
        "gemini-3-pro-preview",        
        "gemini-3-flash-preview"
    ]
    
    # Safety settings - permissive for scientific content
    SAFETY_SETTINGS = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.
        
        Args:
            api_key: Optional API key. Falls back to GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. Please set the environment variable or pass api_key."
            )
        
        genai.configure(api_key=self.api_key)
        self.model_name = self._select_model()
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings=self.SAFETY_SETTINGS,
        )
    
    def _select_model(self) -> str:
        """Select the best available model from the preferred list."""
        try:
            available_models = [m.name for m in genai.list_models()]
            for preferred in self.PREFERRED_MODELS:
                # Model names are like "models/gemini-3-pro"
                full_name = f"models/{preferred}"
                if full_name in available_models:
                    return preferred
            # Fallback to first preferred
            return self.PREFERRED_MODELS[0]
        except Exception:
            # If listing fails, use first preferred
            return self.PREFERRED_MODELS[0]
    
    def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 8192,
    ) -> str:
        """
        Generate content from a single prompt.
        
        Args:
            prompt: The user prompt
            system_instruction: Optional system instruction for the model
            temperature: Sampling temperature (0.0-1.0)
            max_output_tokens: Maximum tokens in response
            
        Returns:
            Generated text response
        """
        model = self.model
        if system_instruction:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                safety_settings=self.SAFETY_SETTINGS,
                system_instruction=system_instruction,
            )
        
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
        )
        
        return response.text
    
    def generate_content_with_history(
        self,
        prompt: str,
        history: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 8192,
    ) -> str:
        """
        Generate content with conversation history (multi-turn).
        
        Args:
            prompt: The current user prompt
            history: List of previous messages [{"role": "user"|"model", "content": "..."}]
            system_instruction: Optional system instruction
            temperature: Sampling temperature
            max_output_tokens: Maximum tokens in response
            
        Returns:
            Generated text response
        """
        model = self.model
        if system_instruction:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                safety_settings=self.SAFETY_SETTINGS,
                system_instruction=system_instruction,
            )
        
        # Convert history to Gemini format
        gemini_history = []
        for msg in history:
            role = "model" if msg.get("role") == "assistant" else msg.get("role", "user")
            gemini_history.append({
                "role": role,
                "parts": [{"text": msg.get("content", "")}],
            })
        
        # Start chat with history
        chat = model.start_chat(history=gemini_history)
        
        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        
        response = chat.send_message(
            prompt,
            generation_config=generation_config,
        )
        
        return response.text
    
    def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output.
        
        Uses lower temperature for more consistent JSON output.
        
        Args:
            prompt: Prompt requesting JSON output
            system_instruction: Optional system instruction
            temperature: Lower default for structured output
            
        Returns:
            Parsed JSON as dictionary
            
        Raises:
            ValueError: If response cannot be parsed as JSON
        """
        # Add JSON instruction to prompt
        json_prompt = f"{prompt}\n\nRespond ONLY with valid JSON. No markdown, no explanation, just the JSON object."
        
        response_text = self.generate_content(
            prompt=json_prompt,
            system_instruction=system_instruction,
            temperature=temperature,
        )
        
        # Clean response - remove markdown code blocks if present
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse Gemini response as JSON: {e}\nResponse: {response_text[:500]}")


# Global client instance (lazy initialization)
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create the global Gemini client instance."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
