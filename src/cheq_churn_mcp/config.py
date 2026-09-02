"""Typed, environment-backed application configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Configuration required by the local analytics process."""

    dataset_path: Path
    query_timeout_seconds: int = 10
    max_rows: int = 100

    def __post_init__(self) -> None:
        if self.query_timeout_seconds < 1:
            raise ValueError("query_timeout_seconds must be at least 1")
        if self.max_rows < 1:
            raise ValueError("max_rows must be at least 1")
