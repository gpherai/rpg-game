"""Utility voor het lezen van JSON-bestanden vanuit de data-folder."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .exceptions import (
    DataEncodingError,
    DataFileNotFoundError,
    DataParseError,
    DataPermissionError,
)

logger = logging.getLogger(__name__)


class DataLoader:
    """Laadt ruwe JSON en cachet resultaten met validatie."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self._data_dir = data_dir or Path("data")
        self._cache: dict[str, Any] = {}

    def load_json(self, filename: str) -> Any:
        """Lees een JSON-bestand en retourneer de inhoud.

        Parameters
        ----------
        filename : str
            Naam van het bestand (bijv. "actors.json")

        Returns
        -------
        Any
            De geparseerde JSON data

        Raises
        ------
        DataFileNotFoundError
            Als het bestand niet bestaat
        DataParseError
            Als JSON parsing faalt
        DataPermissionError
            Als het bestand niet gelezen kan worden door permissions
        DataEncodingError
            Als het bestand encoding problemen heeft
        """
        if filename in self._cache:
            return self._cache[filename]

        filepath = self._data_dir / filename

        if not filepath.exists():
            logger.error(f"Data file not found: {filepath}")
            raise DataFileNotFoundError(filepath)

        logger.info(f"Loading JSON from: {filepath}")

        try:
            with filepath.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON in {filepath}: {e}")
            raise DataParseError(
                filepath=filepath,
                original_error=e,
                line=e.lineno,
                column=e.colno,
            ) from e
        except PermissionError as e:
            logger.error(f"Permission denied reading {filepath}: {e}")
            raise DataPermissionError(filepath) from e
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error reading {filepath}: {e}")
            raise DataEncodingError(filepath) from e
        except OSError as e:
            logger.error(f"OS error loading {filepath}: {e}")
            raise DataFileNotFoundError(filepath, f"OS error: {e}") from e

        self._cache[filename] = data
        return data

    def validate_data(
        self, data: dict[str, Any], data_type: str, required_keys: list[str]
    ) -> list[str]:
        """Valideer dat data de vereiste keys bevat.

        Parameters
        ----------
        data : dict
            Data om te valideren (meestal een dict met entries)
        data_type : str
            Type data (bijv. "actors", "enemies") voor foutmeldingen
        required_keys : list[str]
            Lijst van vereiste keys per entry

        Returns
        -------
        list[str]
            Lijst van foutmeldingen (leeg als alles OK is)
        """
        errors = []

        # Check if data has expected top-level structure
        if data_type not in data:
            errors.append(f"Missing top-level key '{data_type}' in {data_type}.json")
            return errors

        entries = data[data_type]

        if not isinstance(entries, list):
            errors.append(f"Expected '{data_type}' to be a list, got {type(entries).__name__}")
            return errors

        # Validate each entry
        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                errors.append(f"Entry {idx} in '{data_type}' is not a dict: {type(entry).__name__}")
                continue

            # Check required keys
            entry_id = entry.get("id", f"<unknown at index {idx}>")
            for key in required_keys:
                if key not in entry:
                    errors.append(
                        f"Entry '{entry_id}' in {data_type}.json missing required key: '{key}'"
                    )

            # Validate key types
            if "id" in entry and not isinstance(entry["id"], str):
                errors.append(f"Entry '{entry_id}' in {data_type}.json has non-string 'id'")

            if "name" in entry and not isinstance(entry["name"], str):
                errors.append(f"Entry '{entry_id}' in {data_type}.json has non-string 'name'")

            if "type" in entry and not isinstance(entry["type"], str):
                errors.append(f"Entry '{entry_id}' in {data_type}.json has non-string 'type'")

            if "level" in entry and not isinstance(entry["level"], int):
                errors.append(f"Entry '{entry_id}' in {data_type}.json has non-int 'level'")

        return errors

    def clear_cache(self) -> None:
        """Leeg de cache (nuttig voor testen of hot reload)."""
        self._cache.clear()
        logger.debug("Data cache cleared")


__all__ = ["DataLoader"]
