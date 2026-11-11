"""Tiny JSON-file storage with atomic writes."""

import asyncio
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger("OmniCore.storage")


class JsonStore:
    def __init__(self, path: Path, default=None) -> None:
        self.path = Path(path)
        self._default = default if default is not None else {}
        self._lock = asyncio.Lock()
        self.data = self._load()

    def _load(self):
        try:
            with self.path.open(encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return json.loads(json.dumps(self._default))
        except json.JSONDecodeError:
            # Keep the broken file for inspection instead of silently overwriting it.
            backup = self.path.with_suffix(self.path.suffix + ".corrupt")
            os.replace(self.path, backup)
            logger.error("%s was corrupt; moved it to %s and started fresh.", self.path, backup)
            return json.loads(json.dumps(self._default))

    async def save(self) -> None:
        async with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(self.path.suffix + ".tmp")
            tmp.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
            os.replace(tmp, self.path)
