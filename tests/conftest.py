"""Shared pytest fixtures for ClawGuard tests."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def fixture_path(fixtures_dir: Path):
    """Return a helper to get a specific fixture directory by name."""
    def _get(name: str) -> Path:
        path = fixtures_dir / name
        assert path.exists(), f"Fixture {name} not found at {path}"
        return path
    return _get
