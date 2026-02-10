"""Tests for ClawHub client (mocked HTTP)."""

import zipfile
from io import BytesIO

import httpx
import pytest
import respx

from clawguard.clawhub.client import ClawHubClient, SkillInfo
from clawguard.exceptions import ClawHubError


def _make_skill_zip() -> bytes:
    """Create a minimal skill zip archive in memory."""
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("SKILL.md", "---\nname: test\n---\n# Test Skill")
    return buf.getvalue()


class TestClawHubClient:
    def test_parse_url_full(self):
        client = ClawHubClient()
        result = client._parse_url("https://clawhub.com/skills/author/name")
        assert result == "author/name"

    def test_parse_url_trailing_slash(self):
        client = ClawHubClient()
        result = client._parse_url("https://clawhub.com/skills/a/b/")
        assert result == "a/b"

    @respx.mock
    def test_download_success(self, tmp_path):
        zip_data = _make_skill_zip()
        respx.get(
            "https://clawhub.com/api/skills/author/name/download"
        ).mock(return_value=httpx.Response(200, content=zip_data))

        client = ClawHubClient()
        try:
            path = client.download("https://clawhub.com/skills/author/name")
            assert (path / "SKILL.md").exists()
        finally:
            client.cleanup()

    @respx.mock
    def test_download_404_raises(self):
        respx.get(
            "https://clawhub.com/api/skills/author/gone/download"
        ).mock(return_value=httpx.Response(404))

        client = ClawHubClient()
        with pytest.raises(ClawHubError, match="Skill not found"):
            client.download("https://clawhub.com/skills/author/gone")

    @respx.mock
    def test_download_server_error_raises(self):
        respx.get(
            "https://clawhub.com/api/skills/author/broken/download"
        ).mock(return_value=httpx.Response(500))

        client = ClawHubClient()
        with pytest.raises(ClawHubError, match="500"):
            client.download("https://clawhub.com/skills/author/broken")

    @respx.mock
    def test_download_bad_zip_raises(self):
        respx.get(
            "https://clawhub.com/api/skills/author/bad/download"
        ).mock(return_value=httpx.Response(200, content=b"not a zip"))

        client = ClawHubClient()
        with pytest.raises(ClawHubError, match="Invalid skill archive"):
            client.download("https://clawhub.com/skills/author/bad")

    @respx.mock
    def test_download_no_skill_md_raises(self):
        buf = BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("README.md", "no skill here")
        respx.get(
            "https://clawhub.com/api/skills/author/empty/download"
        ).mock(return_value=httpx.Response(200, content=buf.getvalue()))

        client = ClawHubClient()
        with pytest.raises(ClawHubError, match="no SKILL.md"):
            client.download("https://clawhub.com/skills/author/empty")

    def test_cleanup(self, tmp_path):
        client = ClawHubClient()
        client._temp_dirs.append(tmp_path)
        client.cleanup()
        assert len(client._temp_dirs) == 0


class TestListSkills:
    @respx.mock
    def test_list_skills_success(self):
        from clawguard.clawhub.bulk import list_skills

        respx.get("https://clawhub.com/api/skills?limit=2").mock(
            return_value=httpx.Response(200, json={
                "skills": [
                    {"name": "skill-a", "author": "auth1", "url": "u1"},
                    {"name": "skill-b", "author": "auth2", "url": "u2"},
                ]
            })
        )
        skills = list_skills(limit=2)
        assert len(skills) == 2
        assert isinstance(skills[0], SkillInfo)
        assert skills[0].name == "skill-a"

    @respx.mock
    def test_list_skills_api_error(self):
        from clawguard.clawhub.bulk import list_skills

        respx.get("https://clawhub.com/api/skills?limit=10").mock(
            return_value=httpx.Response(503)
        )
        with pytest.raises(ClawHubError, match="503"):
            list_skills(limit=10)
