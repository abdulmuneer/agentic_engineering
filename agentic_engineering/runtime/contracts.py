from __future__ import annotations

from typing import Any

PLACEHOLDER_PREFIXES = ("Define and deliver the observable outcome for", "Replace with")


def placeholder_free(value: Any) -> bool:
    """True when a canonical field holds real content rather than scaffold text."""
    if isinstance(value, str):
        text = value.strip()
        return bool(text) and not text.startswith(PLACEHOLDER_PREFIXES)
    if isinstance(value, list):
        return bool(value) and all(
            placeholder_free(item.get("statement") if isinstance(item, dict) else item)
            for item in value
        )
    return False
