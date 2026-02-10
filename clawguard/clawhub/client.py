"""ClawHub client — download skills from the registry."""

import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import httpx
import structlog

from clawguard.exceptions import ClawHubError

logger = structlog.get_logger()

CLAWHUB_BASE_URL = "https://clawhub.com"


@dataclass
class SkillInfo:
    """Summary info for a skill in the ClawHub registry."""

    name: str
    author: str
    url: str
    description: str = ""
    downloads: int = 0


class ClawHubClient:
    """Client for interacting with the ClawHub skill registry."""

    def __init__(self, base_url: str = CLAWHUB_BASE_URL) -> None:
        self.base_url = base_url.rstrip("/")
        self._temp_dirs: list[Path] = []

    def download(self, url: str) -> Path:
        """Download a skill from a ClawHub URL to a temp directory.

        Returns the local path to the extracted skill directory.
        """
        skill_id = self._parse_url(url)
        download_url = f"{self.base_url}/api/skills/{skill_id}/download"

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(download_url)
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ClawHubError(f"Skill not found: {skill_id}") from e
            raise ClawHubError(
                f"ClawHub API error: {e.response.status_code}"
            ) from e
        except httpx.RequestError as e:
            raise ClawHubError(f"Network error: {e}") from e

        temp_dir = Path(tempfile.mkdtemp(prefix="clawguard_"))
        self._temp_dirs.append(temp_dir)

        try:
            with zipfile.ZipFile(BytesIO(response.content)) as zf:
                zf.extractall(temp_dir)
        except zipfile.BadZipFile as e:
            raise ClawHubError(f"Invalid skill archive: {e}") from e

        # Find SKILL.md in extracted content
        skill_md_files = list(temp_dir.rglob("SKILL.md"))
        if not skill_md_files:
            raise ClawHubError("Downloaded archive has no SKILL.md")

        return skill_md_files[0].parent

    def _parse_url(self, url: str) -> str:
        """Extract skill identifier from a ClawHub URL."""
        url = url.rstrip("/")
        # Handle: https://clawhub.com/skills/author/name
        parts = url.split("/")
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
        if len(parts) == 1:
            return parts[0]
        raise ClawHubError(f"Cannot parse ClawHub URL: {url}")

    def cleanup(self) -> None:
        """Remove all temporary directories created by downloads."""
        for temp_dir in self._temp_dirs:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
        self._temp_dirs.clear()

    def __del__(self) -> None:
        self.cleanup()
