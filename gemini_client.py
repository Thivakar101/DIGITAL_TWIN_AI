"""Gemini REST client with explicit error handling and offline fallback."""
from __future__ import annotations

import json
import os
import random
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

from app_config import get_env_value, load_environment


class GeminiAPIError(RuntimeError):
    """Raised when a live Gemini request fails."""


class GeminiClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-3.5-flash",
        embed_model: str = "gemini-embedding-001",
        timeout_seconds: int = 30,
    ):
        load_environment()
        self.api_key = (api_key or get_env_value("GEMINI_API_KEY", "")).strip()
        self.model_name = model_name
        self.embed_model = embed_model
        self.timeout_seconds = timeout_seconds
        self.last_error = ""

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)

    def status(self) -> Dict[str, object]:
        return {
            "configured": self.has_api_key,
            "mode": "live" if self.has_api_key else "offline",
            "last_error": self.last_error,
            "model_name": self.model_name,
            "embed_model": self.embed_model,
        }

    def set_api_key(self, api_key: str) -> None:
        self.api_key = (api_key or "").strip()
        os.environ["GEMINI_API_KEY"] = self.api_key
        self.last_error = ""

    def _endpoint(self, model_name: str, action: str) -> str:
        query = urllib.parse.urlencode({"key": self.api_key})
        return f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:{action}?{query}"

    def _post_json(self, url: str, payload: Dict[str, object]) -> Dict[str, object]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            message = body
            try:
                parsed = json.loads(body)
                message = parsed.get("error", {}).get("message", body)
            except Exception:
                pass
            self.last_error = f"Gemini API error ({exc.code}): {message}"
            raise GeminiAPIError(self.last_error) from exc
        except Exception as exc:
            self.last_error = f"Gemini request failed: {exc}"
            raise GeminiAPIError(self.last_error) from exc

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self.has_api_key:
            vectors: List[List[float]] = []
            for text in texts:
                response = self._post_json(
                    self._endpoint(self.embed_model, "embedContent"),
                    {
                        "model": f"models/{self.embed_model}",
                        "content": {"parts": [{"text": text}]},
                    },
                )
                values = response.get("embedding", {}).get("values", [])
                if not values:
                    self.last_error = "Gemini embedding response was empty."
                    raise GeminiAPIError(self.last_error)
                vectors.append([float(value) for value in values])
            self.last_error = ""
            return vectors

        vectors = []
        for text in texts:
            seeded = random.Random(hash(text) & 0xFFFFFFFF)
            vectors.append([seeded.random() for _ in range(256)])
        return vectors

    def chat(self, system_prompt: str, user_message: str) -> str:
        if self.has_api_key:
            response = self._post_json(
                self._endpoint(self.model_name, "generateContent"),
                {
                    "system_instruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"parts": [{"text": user_message}]}],
                    "generationConfig": {"temperature": 0.7, "maxOutputTokens": 400},
                },
            )
            candidates = response.get("candidates", [])
            for candidate in candidates:
                parts = candidate.get("content", {}).get("parts", [])
                text = " ".join(part.get("text", "") for part in parts).strip()
                if text:
                    self.last_error = ""
                    return text
            self.last_error = "Gemini generated an empty response."
            raise GeminiAPIError(self.last_error)

        return (
            "[Offline Mode] No Gemini API key is configured, so this is a local placeholder reply: "
            f"{user_message[:160]} ..."
        )
