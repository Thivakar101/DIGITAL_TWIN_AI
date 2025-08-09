"""
Lightweight Gemini client wrapper. Uses GEMINI_API_KEY if available.
Falls back to offline stubs so the app runs locally for testing.
"""
from __future__ import annotations
import os
import random
from typing import List, Optional

# Optional: load .env if available
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass


class GeminiClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-flash",
        embed_model: str = "text-embedding-004",
    ):
        self.api_key = (api_key or os.environ.get("GEMINI_API_KEY", "")).strip()
        self.model_name = model_name
        self.embed_model = embed_model
        self._configured = False
        self._have_sdk = False
        self._configure_sdk()

    def _configure_sdk(self) -> None:
        self._have_sdk = False
        if not self.api_key:
            return
        try:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=self.api_key)
            self._have_sdk = True
            self._configured = True
            self._genai = genai
        except Exception:
            # Keep fallback mode
            self._have_sdk = False
            self._configured = False

    def set_api_key(self, api_key: str) -> None:
        self.api_key = (api_key or "").strip()
        os.environ["GEMINI_API_KEY"] = self.api_key  # ensure downstream code sees it this process
        self._configure_sdk()

    # Embeddings API
    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if self._have_sdk and self._configured:
            try:
                # google-generativeai doesn't batch embed_content; loop for stability
                vecs: List[List[float]] = []
                for t in texts:
                    res = self._genai.embed_content(model=self.embed_model, content=t)
                    # res: { 'embedding': [ ... ] }
                    vecs.append(list(res.get("embedding", []) or []))
                # Basic guard: fallback if empty
                if all(len(v) == 0 for v in vecs):
                    raise RuntimeError("Empty embeddings from API")
                return vecs
            except Exception:
                pass  # fall through to stub
        # Offline deterministic pseudo-embeddings
        vecs = []
        for t in texts:
            r = random.Random(hash(t) & 0xFFFFFFFF)
            vecs.append([r.random() for _ in range(256)])
        return vecs

    # Chat API
    def chat(self, system_prompt: str, user_message: str) -> str:
        if self._have_sdk and self._configured:
            try:
                model = self._genai.GenerativeModel(
                    self.model_name, system_instruction=system_prompt
                )
                resp = model.generate_content(user_message)
                txt = getattr(resp, "text", None)
                if isinstance(txt, str) and txt.strip():
                    return txt.strip()
                # Fallback to concatenating parts
                if hasattr(resp, "candidates") and resp.candidates:
                    for c in resp.candidates:
                        parts = getattr(getattr(c, "content", None), "parts", None)
                        if parts:
                            joined = " ".join(
                                str(getattr(p, "text", "")) for p in parts
                            )
                            if joined.strip():
                                return joined.strip()
            except Exception:
                pass
        return (
            "[Stubbed Gemini Reply] Based on your persona and memories, "
            f"here's a likely response: {user_message[:160]} ..."
        )
