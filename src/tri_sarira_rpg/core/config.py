"""Configuratie-object voor runtime-instellingen."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path

# Python 3.11+ heeft tomllib in stdlib
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # type: ignore
    except ImportError:
        raise ImportError(
            "tomllib not available. Install tomli for Python <3.11: pip install tomli"
        )

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Config:
    """Bundelt scherminstellingen, padlocaties en dev-flags."""

    # Display settings
    resolution: tuple[int, int]
    target_fps: int
    title: str
    fullscreen: bool

    # Paths
    data_dir: Path
    assets_dir: Path
    maps_dir: Path
    schema_dir: Path

    # Development
    debug_mode: bool
    show_fps: bool
    skip_intro: bool

    # Logging
    log_level: str

    @classmethod
    def load(cls, root: Path | None = None) -> Config:
        """Lees config-bestanden en bouw het Config-object.

        Parameters
        ----------
        root:
            Optioneel pad naar de projectroot om config-bestanden te vinden.

        Raises
        ------
        FileNotFoundError:
            Als config/default_config.toml niet bestaat.
        ValueError:
            Als de TOML-structuur ongeldig is.
        """
        if root is None:
            # Ga uit van dat we in de projectroot zitten of src/
            # Zoek naar config/ directory
            root = Path.cwd()
            if (root / "src").exists():
                root = root  # We zijn in projectroot
            elif root.name == "src":
                root = root.parent  # We zijn in src/, ga omhoog
            elif (root.parent / "config").exists():
                root = root.parent  # We zijn in een subdir

        config_file = root / "config" / "default_config.toml"

        if not config_file.exists():
            logger.error(f"Config file not found: {config_file}")
            raise FileNotFoundError(
                f"Required config file not found: {config_file}\n"
                f"Expected location: config/default_config.toml in project root"
            )

        logger.info(f"Loading config from: {config_file}")

        try:
            with open(config_file, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            logger.error(f"Failed to parse TOML config: {e}")
            raise ValueError(f"Invalid TOML in {config_file}: {e}") from e

        # Extract sections
        display = data.get("display", {})
        paths = data.get("paths", {})
        dev = data.get("development", {})
        log_config = data.get("logging", {})

        # Build Config object
        return cls(
            # Display
            resolution=(display.get("width", 1280), display.get("height", 720)),
            target_fps=display.get("target_fps", 60),
            title=display.get("title", "Tri-Śarīra RPG"),
            fullscreen=display.get("fullscreen", False),
            # Paths (relative to project root)
            data_dir=root / paths.get("data_dir", "data"),
            assets_dir=root / paths.get("assets_dir", "assets"),
            maps_dir=root / paths.get("maps_dir", "maps"),
            schema_dir=root / paths.get("schema_dir", "schema"),
            # Development
            debug_mode=dev.get("debug_mode", False),
            show_fps=dev.get("show_fps", False),
            skip_intro=dev.get("skip_intro", False),
            # Logging
            log_level=log_config.get("level", "INFO"),
        )


__all__ = ["Config"]
