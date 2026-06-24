from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None

ROOT_DIR = Path(__file__).resolve().parent
ENV_PATH = ROOT_DIR / '.env'


def load_environment() -> None:
    if load_dotenv:
        load_dotenv(ENV_PATH, override=False)


def get_env_value(key: str, default: str = '') -> str:
    load_environment()
    return os.environ.get(key, default)


def set_env_values(updates: Dict[str, str]) -> None:
    existing_lines = []
    if ENV_PATH.exists():
        existing_lines = ENV_PATH.read_text(encoding='utf-8').splitlines()

    pending = dict(updates)
    new_lines = []

    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or '=' not in line:
            new_lines.append(line)
            continue

        key, _value = line.split('=', 1)
        clean_key = key.strip()
        if clean_key in pending:
            new_lines.append(f'{clean_key}={pending.pop(clean_key)}')
        else:
            new_lines.append(line)

    for key, value in pending.items():
        new_lines.append(f'{key}={value}')

    ENV_PATH.write_text('\n'.join(new_lines).rstrip() + '\n', encoding='utf-8')
    for key, value in updates.items():
        os.environ[key] = value
