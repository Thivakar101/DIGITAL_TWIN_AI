from __future__ import annotations
from typing import Iterable, List, Optional
import numpy as np

from models import MemoryItem


class MemoryBank:
    """In-memory store of memories with cosine similarity search."""

    def __init__(self):
        self._memories: List[MemoryItem] = []

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        if a.size == 0 or b.size == 0:
            return 0.0
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return 0.0
        return float(np.dot(a, b) / denom)

    def add(self, item: MemoryItem) -> None:
        self._memories.append(item)

    def list(self) -> List[MemoryItem]:
        return list(self._memories)

    def search(self, query_embedding: Iterable[float], top_k: int = 5, type_filter: Optional[str] = None) -> List[MemoryItem]:
        q = np.array(list(query_embedding), dtype=float)
        scored = []
        for m in self._memories:
            if type_filter and m.type != type_filter:
                continue
            s = self._cosine_similarity(q, np.array(m.embedding, dtype=float))
            scored.append((s, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:top_k]]

    def delete(self, idx: int) -> None:
        if 0 <= idx < len(self._memories):
            self._memories.pop(idx)

    def clear(self, keep_permanent: bool = True) -> None:
        if keep_permanent:
            self._memories = [m for m in self._memories if m.permanent]
        else:
            self._memories.clear()
