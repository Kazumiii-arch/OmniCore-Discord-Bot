"""Parse and format human durations like `10m`, `1h30m`, `2d`."""

import re
from datetime import timedelta
from typing import Optional

_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
_PART = re.compile(r"(\d+)([smhdw])")


def parse_duration(text: str) -> Optional[timedelta]:
    text = text.strip().lower().replace(" ", "")
    if not text:
        return None
    total = 0
    pos = 0
    for match in _PART.finditer(text):
        if match.start() != pos:
            return None
        total += int(match.group(1)) * _UNITS[match.group(2)]
        pos = match.end()
    if pos != len(text) or total <= 0:
        return None
    return timedelta(seconds=total)


def format_duration(delta: timedelta) -> str:
    seconds = int(delta.total_seconds())
    if seconds <= 0:
        return "0s"
    parts = []
    for name, size in (("d", 86400), ("h", 3600), ("m", 60), ("s", 1)):
        amount, seconds = divmod(seconds, size)
        if amount:
            parts.append(f"{amount}{name}")
    return " ".join(parts)
