from __future__ import annotations

import json


def encode_str_list(values: list[str]) -> str:
    """Serialize a list of strings to JSON for safe DB storage."""
    return json.dumps(values, ensure_ascii=False)


def decode_str_list(raw: str | None) -> list[str]:
    """Parse list data stored as JSON; fall back to legacy comma-separated format."""
    if not raw:
        return []

    text = raw.strip()
    if text.startswith("["):
        try:
            loaded = json.loads(text)
            if isinstance(loaded, list):
                return [str(item).strip() for item in loaded if str(item).strip()]
        except json.JSONDecodeError:
            pass

    return [item.strip() for item in raw.split(",") if item.strip()]
