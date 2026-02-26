"""
Input sanitization utilities.

Strips potentially dangerous HTML/JS from user-generated text fields
using bleach. All user-input text should pass through `sanitize_text()`
before being written to the database.
"""
from __future__ import annotations

import bleach

# Tags we allow in user content (empty = plain text only)
_ALLOWED_TAGS: list[str] = []
_ALLOWED_ATTRIBUTES: dict[str, list[str]] = {}


def sanitize_text(value: str | None) -> str | None:
    """
    Strip all HTML/script tags from user-generated text.
    Returns None if input is None (for optional fields).
    """
    if value is None:
        return None
    cleaned = bleach.clean(
        value,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        strip=True,
    )
    # Also strip null bytes
    return cleaned.replace("\x00", "")


def sanitize_dict(data: dict, fields: list[str]) -> dict:
    """
    Sanitize specific string fields in a dict in-place.
    Useful for batch-sanitizing Pydantic model .dict() output.
    """
    for field in fields:
        if field in data and isinstance(data[field], str):
            data[field] = sanitize_text(data[field])
    return data
