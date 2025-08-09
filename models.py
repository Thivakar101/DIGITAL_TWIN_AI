from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


VALID_MEMORY_TYPES = {"survey", "chat", "decision", "correction", "situation"}


@dataclass
class MemoryItem:
    type: str
    text: str
    embedding: List[float]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    meta: Dict[str, str] = field(default_factory=dict)
    permanent: bool = False

    def __post_init__(self):
        if self.type not in VALID_MEMORY_TYPES:
            raise ValueError(f"Invalid memory type: {self.type}")


@dataclass
class Persona:
    user_name: str = "You"
    persona_summary: str = ""
    tone_style: str = "Balanced, friendly"
    values: str = "Pragmatic, honest"
    humor: str = "Light, situational"
    decision_style: str = "Evidence-driven with intuition"
    survey_json: Dict[str, object] = field(default_factory=dict)
    mbti: str = ""
