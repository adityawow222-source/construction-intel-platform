"""Thin, defensive wrapper around the Google GenAI SDK.

All network/model failures are converted into ``GeminiError`` so the UI layer
only ever has to handle one exception type.
"""
from __future__ import annotations

import json
import re
from typing import Any

from PIL import Image

try:
    from google import genai
    from google.genai import types

    GENAI_AVAILABLE = True
except ImportError:  # pragma: no cover - handled gracefully in the UI
    genai = None
    types = None
    GENAI_AVAILABLE = False


MODEL_OPTIONS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-3-flash-preview",
    "gemini-3-pro-preview",
]

MAX_CHAT_TURNS = 20  # messages of history sent to the model per request


class GeminiError(Exception):
    """Raised for any failure talking to, or parsing output from, Gemini."""


def extract_json(text: str | None) -> dict[str, Any]:
    """Parse a JSON object from model text, tolerating code fences and chatter."""
    if not text or not text.strip():
        raise GeminiError("The model returned an empty response.")

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise GeminiError("The model did not return valid JSON.") from None
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise GeminiError(f"Could not parse model JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise GeminiError("Expected a JSON object from the model.")
    return parsed


def _friendly(exc: Exception) -> str:
    msg = str(exc)
    low = msg.lower()
    if "api key" in low or "api_key_invalid" in low or "permission" in low or "401" in low or "403" in low:
        return "The API key was rejected. Check that it is valid and has Gemini API access."
    if "429" in low or "quota" in low or "resource_exhausted" in low:
        return "Rate limit or quota exceeded. Wait a minute and try again, or switch models."
    if "404" in low or "not found" in low:
        return "The selected model is not available for this key. Pick another model in the sidebar."
    if "safety" in low or "blocked" in low:
        return "The request was blocked by the model's safety filters. Try a different image."
    return f"Gemini request failed: {msg[:300]}"


class GeminiClient:
    """Stateless helper for the two interaction patterns the app needs."""

    def __init__(self, api_key: str, model: str) -> None:
        if not GENAI_AVAILABLE:
            raise GeminiError("The google-genai package is not installed.")
        if not api_key:
            raise GeminiError("No API key supplied.")
        try:
            self._client = genai.Client(api_key=api_key)
        except Exception as exc:  # noqa: BLE001
            raise GeminiError(_friendly(exc)) from exc
        self.model = model

    # ------------------------------------------------------------------ #
    def ping(self) -> str:
        """Cheap connectivity check: fetch model metadata."""
        try:
            info = self._client.models.get(model=self.model)
            return getattr(info, "display_name", None) or self.model
        except Exception as exc:  # noqa: BLE001
            raise GeminiError(_friendly(exc)) from exc

    def analyze_image(self, prompt: str, image: Image.Image) -> dict[str, Any]:
        """Send one image + instruction and return the parsed JSON object."""
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=[prompt, image],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
        except Exception as exc:  # noqa: BLE001
            raise GeminiError(_friendly(exc)) from exc
        return extract_json(getattr(response, "text", None))

    def chat(self, history: list[dict[str, str]], system_instruction: str) -> str:
        """Multi-turn chat. ``history`` items are {'role': 'user'|'assistant', 'content': str}."""
        trimmed = history[-MAX_CHAT_TURNS:]
        contents = [
            types.Content(
                role="user" if m["role"] == "user" else "model",
                parts=[types.Part(text=m["content"])],
            )
            for m in trimmed
        ]
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.5,
                ),
            )
        except Exception as exc:  # noqa: BLE001
            raise GeminiError(_friendly(exc)) from exc
        text = getattr(response, "text", None)
        if not text:
            raise GeminiError("The model returned an empty reply. Try rephrasing.")
        return text.strip()
