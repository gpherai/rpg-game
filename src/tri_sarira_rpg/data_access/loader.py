"""Utility voor het lezen van JSON-bestanden vanuit de data-folder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DataLoader:
    """Laadt ruwe JSON en cachet resultaten."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or Path("data")
        self._cache: dict[str, Any] = {}

    def load_json(self, filename: str) -> Any:
        """Lees een JSON-bestand en retourneer de inhoud."""

        if filename not in self._cache:
            with (self._data_dir / filename).open("r", encoding="utf-8") as fh:
                self._cache[filename] = json.load(fh)
        return self._cache[filename]


__all__ = ["DataLoader"]
