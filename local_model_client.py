from __future__ import annotations

import hashlib
from typing import Dict, List, Optional

import requests

from app_config import get_env_value, load_environment


class LocalModelError(RuntimeError):
    pass


class LocalModelClient:
    def __init__(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: int = 180,
    ):
        load_environment()
        self.model_name = (model_name or get_env_value('OLLAMA_MODEL', 'llama3')).strip() or 'llama3'
        self.base_url = (base_url or get_env_value('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')).strip().rstrip('/')
        self.timeout_seconds = timeout_seconds
        self.last_error = ''

    def status(self) -> Dict[str, object]:
        return {
            'configured': True,
            'mode': 'local',
            'provider': 'ollama',
            'last_error': self.last_error,
            'model_name': self.model_name,
            'base_url': self.base_url,
        }

    def set_model(self, model_name: str) -> None:
        self.model_name = (model_name or 'llama3').strip() or 'llama3'
        self.last_error = ''

    def set_base_url(self, base_url: str) -> None:
        self.base_url = (base_url or 'http://127.0.0.1:11434').strip().rstrip('/')
        self.last_error = ''

    def _post_json(self, path: str, payload: Dict[str, object]) -> Dict[str, object]:
        url = f'{self.base_url}{path}'
        try:
            response = requests.post(url, json=payload, timeout=(10, self.timeout_seconds))
            response.raise_for_status()
            data = response.json()
            self.last_error = ''
            return data
        except requests.RequestException as exc:
            body = ''
            if getattr(exc, 'response', None) is not None:
                try:
                    body = exc.response.text
                except Exception:
                    body = ''
            self.last_error = f'Local model request failed: {exc}' + (f' | {body}' if body else '')
            raise LocalModelError(self.last_error) from exc

    def ping(self) -> bool:
        try:
            response = requests.get(f'{self.base_url}/api/tags', timeout=(5, 10))
            response.raise_for_status()
            self.last_error = ''
            return True
        except requests.RequestException as exc:
            self.last_error = f'Cannot reach Ollama at {self.base_url}: {exc}'
            raise LocalModelError(self.last_error) from exc

    def embed(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode('utf-8')).digest()
            seed_bytes = digest * 8
            vector = [((b / 255.0) * 2.0) - 1.0 for b in seed_bytes[:256]]
            vectors.append(vector)
        return vectors

    def chat(self, system_prompt: str, user_message: str) -> str:
        data = self._post_json(
            '/api/chat',
            {
                'model': self.model_name,
                'stream': False,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_message},
                ],
            },
        )
        message = data.get('message', {})
        content = str(message.get('content', '')).strip()
        if not content:
            self.last_error = 'Local model returned an empty response.'
            raise LocalModelError(self.last_error)
        return content
