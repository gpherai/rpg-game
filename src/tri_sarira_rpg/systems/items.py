"""Inventory- en itemgebruik."""

from __future__ import annotations

from typing import Any


class ItemsSystem:
    """Beheert items, stacks en gebruikslogica."""

    def __init__(self, data_repository: Any | None = None) -> None:
        self._inventory: dict[str, int] = {}
        self._data_repository = data_repository

    def add_item(self, item_id: str, amount: int = 1) -> None:
        """Voeg items toe aan de voorraad."""

        pass

    def remove_item(self, item_id: str, amount: int = 1) -> None:
        """Verbruik items als onderdeel van gebruik/shopping."""

        pass

    def use_item(self, item_id: str, target: str) -> None:
        """Start itemeffect op een doel (party-member)."""

        pass

    def current_inventory(self) -> dict[str, int]:
        """Geef de huidige itemaantallen terug."""

        return dict(self._inventory)


__all__ = ["ItemsSystem"]
