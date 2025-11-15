"""Configuratie-object voor runtime-instellingen."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Config:
    """Bundelt scherminstellingen, padlocaties en dev-flags."""

    resolution: tuple[int, int]
    target_fps: int

    @classmethod
    def load(cls, root: Path | None = None) -> "Config":
        """Lees config-bestanden en bouw het Config-object.

        Parameters
        ----------
        root:
            Optioneel pad naar de projectroot om config-bestanden te vinden.
        """

        return cls(resolution=(1280, 720), target_fps=60)


__all__ = ["Config"]
