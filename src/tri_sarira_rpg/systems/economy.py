"""Shops, valuta en transacties."""

from __future__ import annotations

from typing import Any


class EconomySystem:
    """Regelt geldstromen en shopinventories."""

    def __init__(self, data_repository: Any | None = None) -> None:
        self._data_repository = data_repository
        self._currency: int = 0

    def add_currency(self, amount: int) -> None:
        """Voeg geld toe (beloning, verkoop)."""

        pass

    def spend_currency(self, amount: int) -> bool:
        """Probeer geld uit te geven en geef succes terug."""

        return False

    def open_shop(self, shop_id: str) -> list[dict[str, Any]]:
        """Geef shopinventaris terug voor UI."""

        return []

    @property
    def balance(self) -> int:
        """Huidige hoeveelheid valuta."""

        return self._currency


__all__ = ["EconomySystem"]
