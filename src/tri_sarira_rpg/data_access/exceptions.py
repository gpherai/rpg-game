"""Custom exceptions voor data access layer.

Deze module definieert specifieke exceptions voor data loading en validatie,
zodat error handling preciezer en informatiever kan zijn.
"""

from __future__ import annotations

from pathlib import Path


class DataAccessError(Exception):
    """Base exception voor alle data access errors."""

    pass


class DataFileNotFoundError(DataAccessError):
    """Exception wanneer een data bestand niet gevonden wordt."""

    def __init__(self, filepath: Path, message: str | None = None) -> None:
        self.filepath = filepath
        self.message = message or f"Data file not found: {filepath}"
        super().__init__(self.message)


class DataParseError(DataAccessError):
    """Exception wanneer JSON parsing faalt."""

    def __init__(
        self,
        filepath: Path,
        original_error: Exception,
        line: int | None = None,
        column: int | None = None,
    ) -> None:
        self.filepath = filepath
        self.original_error = original_error
        self.line = line
        self.column = column

        location = ""
        if line is not None:
            location = f" at line {line}"
            if column is not None:
                location += f", column {column}"

        self.message = f"Failed to parse JSON in {filepath}{location}: {original_error}"
        super().__init__(self.message)


class DataValidationError(DataAccessError):
    """Exception wanneer data validatie faalt."""

    def __init__(
        self,
        filepath: Path,
        errors: list[str],
        data_type: str | None = None,
    ) -> None:
        self.filepath = filepath
        self.errors = errors
        self.data_type = data_type

        error_summary = "; ".join(errors[:3])
        if len(errors) > 3:
            error_summary += f" (and {len(errors) - 3} more)"

        self.message = f"Validation failed for {filepath}: {error_summary}"
        super().__init__(self.message)


class DataSchemaError(DataAccessError):
    """Exception wanneer data niet voldoet aan verwacht schema."""

    def __init__(
        self,
        filepath: Path,
        expected_key: str,
        entry_id: str | None = None,
    ) -> None:
        self.filepath = filepath
        self.expected_key = expected_key
        self.entry_id = entry_id

        if entry_id:
            self.message = (
                f"Schema error in {filepath}: entry '{entry_id}' missing required key '{expected_key}'"
            )
        else:
            self.message = f"Schema error in {filepath}: missing required key '{expected_key}'"

        super().__init__(self.message)


class DataPermissionError(DataAccessError):
    """Exception wanneer bestand niet gelezen kan worden door permissions."""

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.message = f"Permission denied reading data file: {filepath}"
        super().__init__(self.message)


class DataEncodingError(DataAccessError):
    """Exception wanneer bestand encoding problemen heeft."""

    def __init__(self, filepath: Path, encoding: str = "utf-8") -> None:
        self.filepath = filepath
        self.encoding = encoding
        self.message = f"Encoding error reading {filepath} (expected {encoding})"
        super().__init__(self.message)


__all__ = [
    "DataAccessError",
    "DataFileNotFoundError",
    "DataParseError",
    "DataValidationError",
    "DataSchemaError",
    "DataPermissionError",
    "DataEncodingError",
]
