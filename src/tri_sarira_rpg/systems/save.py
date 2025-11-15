"""Save- en loadfunctionaliteit."""

from __future__ import annotations

from typing import Any


class SaveSystem:
    """Bouwt save-structuren op vanuit actieve systems."""

    def __init__(self, data_repository: Any | None = None) -> None:
        self._data_repository = data_repository

    def build_save(self) -> dict[str, Any]:
        """Verzamel data uit systemen en maak een SaveData-dict."""

        return {}

    def load_save(self, payload: dict[str, Any]) -> None:
        """Herstel systemen vanuit een SaveData-dict."""

        pass

    def export_trilogy_profile(self) -> dict[str, Any]:
        """Maak een compacte export voor vervolgspellen."""

        return {}


__all__ = ["SaveSystem"]
