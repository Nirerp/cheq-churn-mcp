"""Tests for safe local bootstrap-file materialization."""

import stat
from pathlib import Path

import pytest

from cheq_churn_mcp.data.bootstrap import _write_atomically


def test_write_atomically_replaces_file_with_owner_only_permissions(tmp_path: Path) -> None:
    destination = tmp_path / "customers.csv"
    destination.write_text("old", encoding="utf-8")

    _write_atomically(destination, lambda path: path.write_text("new", encoding="utf-8"))

    assert destination.read_text(encoding="utf-8") == "new"
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert list(tmp_path.glob(".*.tmp")) == []


def test_write_atomically_removes_temporary_file_after_failure(tmp_path: Path) -> None:
    destination = tmp_path / "customers.csv"
    destination.write_text("previous-good-snapshot", encoding="utf-8")

    def fail_after_write(path: Path) -> None:
        path.write_text("partial", encoding="utf-8")
        raise RuntimeError("download interrupted")

    with pytest.raises(RuntimeError, match="download interrupted"):
        _write_atomically(destination, fail_after_write)

    assert destination.read_text(encoding="utf-8") == "previous-good-snapshot"
    assert list(tmp_path.glob(".*.tmp")) == []
