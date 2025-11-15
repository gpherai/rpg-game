"""Resourcebeheer voor sprites, audio en overige assets."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class ResourceManager:
    """Laadt en cachet assets zodat scenes ze kunnen hergebruiken."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path.cwd()
        self._cache: dict[str, Any] = {}

    def load_sprite(self, asset_id: str) -> Any:
        """Laad of retourneer een sprite-asset placeholder."""

        return self._cache.setdefault(asset_id, None)

    def load_audio(self, asset_id: str) -> Any:
        """Laad of retourneer een audio-resource placeholder."""

        return self._cache.setdefault(asset_id, None)


__all__ = ["ResourceManager"]
