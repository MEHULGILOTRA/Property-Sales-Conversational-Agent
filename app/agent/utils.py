import re
from typing import Optional

# Bare "m" is deliberately NOT a budget suffix — messages like "350m" usually
# mean square meters. "k" and "million"/"mn" are unambiguous.
_FULL_NUMBER = re.compile(r"\d{6,}")
_SHORTHAND = re.compile(r"(\d+(?:\.\d+)?)\s*(k|million|mn)\b", re.IGNORECASE)

_MULTIPLIERS = {"k": 1_000, "million": 1_000_000, "mn": 1_000_000}


def parse_budget(text: str) -> Optional[int]:
    """Extract a budget in USD from free text.

    Supports full numbers ("800000"), thousands shorthand ("800k") and
    millions ("1.2 million"). The first full number wins over shorthand, so
    corrections like "400000, not 800000" pick the corrected value.
    """
    if not text:
        return None

    match = _FULL_NUMBER.search(text)
    if match:
        return int(match.group())

    match = _SHORTHAND.search(text)
    if match:
        value = float(match.group(1)) * _MULTIPLIERS[match.group(2).lower()]
        return int(value)

    return None
