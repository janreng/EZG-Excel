"""Shared fixtures for Qt tests. ASCII only (Windows console cp1252)."""
import os
import sys
from pathlib import Path

# Must be set before importing PySide6 -> no real display needed.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402


@pytest.fixture(scope="session")
def qapp():
    """A single QApplication shared across the test session."""
    app = QApplication.instance() or QApplication([])
    yield app
