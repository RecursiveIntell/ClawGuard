"""Tests for the SKILL.md parser module."""

from pathlib import Path

import pytest

from clawguard.analyzers.base import SkillPackage
from clawguard.exceptions import ParseError
from clawguard.parser.frontmatter import extract_frontmatter
from clawguard.parser.inventory import discover_scripts
from clawguard.parser.markdown import parse_markdown
from clawguard.parser.skill import parse_skill


# ── Frontmatter tests ──────────────────────────────────────────────────────────


class TestExtractFrontmatter:
    def test_valid_frontmatter(self):
        content = "---\nname: test\nversion: 1.0\n---\n# Hello"
        fm, body = extract_frontmatter(content)
        assert fm == {"name": "test", "version": 1.0}
        assert body.strip() == "# Hello"

    def test_no_frontmatter(self):
        content = "# Just markdown\nNo frontmatter here."
        fm, body = extract_frontmatter(content)
        assert fm == {}
        assert body == content

    def test_malformed_yaml_returns_empty_dict(self):
        content = "---\n: invalid: yaml: [broken\n---\n# Body"
        fm, body = extract_frontmatter(content)
        assert fm == {}

    def test_yaml_not_a_dict_returns_empty(self):
        content = "---\n- just\n- a\n- list\n---\n# Body"
        fm, body = extract_frontmatter(content)
        assert fm == {}

    def test_nested_frontmatter(self):
        content = "---\nname: test\nmetadata:\n  openclaw:\n    verified: true\n---\n# Body"
        fm, body = extract_frontmatter(content)
        assert fm["metadata"]["openclaw"]["verified"] is True

    def test_no_closing_delimiter(self):
        content = "---\nname: test\nversion: 1.0\n# No closing"
        fm, body = extract_frontmatter(content)
        assert fm == {}
        assert body == content

    def test_empty_frontmatter(self):
        content = "---\n---\n# Body"
        fm, body = extract_frontmatter(content)
        assert fm == {}

    def test_leading_newlines_stripped(self):
        content = "\n\n---\nname: test\n---\n# Body"
        fm, body = extract_frontmatter(content)
        assert fm["name"] == "test"


# ── Markdown tests ─────────────────────────────────────────────────────────────


class TestParseMarkdown:
    def test_sections_extracted(self):
        body = "# Title\nSome text\n## Section 1\nContent 1\n## Section 2\nContent 2"
        result = parse_markdown(body)
        headings = [s.heading for s in result.sections]
        assert "Title" in headings
        assert "Section 1" in headings
        assert "Section 2" in headings

    def test_code_blocks_extracted(self):
        body = "# Setup\n\n```bash\necho hello\n```\n\n```python\nprint('hi')\n```"
        result = parse_markdown(body)
        assert len(result.code_blocks) == 2
        assert result.code_blocks[0].language == "bash"
        assert "echo hello" in result.code_blocks[0].content
        assert result.code_blocks[1].language == "python"

    def test_urls_extracted(self):
        body = "Visit https://example.com and http://other.org/path for details."
        result = parse_markdown(body)
        assert "https://example.com" in result.urls
        assert "http://other.org/path" in result.urls

    def test_duplicate_urls_deduplicated(self):
        body = "See https://example.com and also https://example.com again."
        result = parse_markdown(body)
        assert result.urls.count("https://example.com") == 1

    def test_empty_body(self):
        result = parse_markdown("")
        assert result.sections == []
        assert result.code_blocks == []
        assert result.urls == []

    def test_section_levels(self):
        body = "# H1\n## H2\n### H3"
        result = parse_markdown(body)
        levels = {s.heading: s.level for s in result.sections}
        assert levels["H1"] == 1
        assert levels["H2"] == 2
        assert levels["H3"] == 3

    def test_code_block_line_numbers(self):
        body = "Line 1\nLine 2\n```python\ncode\n```"
        result = parse_markdown(body)
        assert result.code_blocks[0].line == 3


# ── Inventory tests ────────────────────────────────────────────────────────────


class TestDiscoverScripts:
    def test_discovers_scripts_in_clean_complex(self, fixtures_dir):
        scripts = discover_scripts(fixtures_dir / "clean_complex_skill")
        paths = [s["path"] for s in scripts]
        assert "install.sh" in paths
        assert "utils.py" in paths

    def test_skips_skill_md(self, fixtures_dir):
        scripts = discover_scripts(fixtures_dir / "clean_skill")
        paths = [s["path"] for s in scripts]
        assert "SKILL.md" not in paths

    def test_language_detection(self, fixtures_dir):
        scripts = discover_scripts(fixtures_dir / "clean_complex_skill")
        lang_map = {s["path"]: s["language"] for s in scripts}
        assert lang_map["install.sh"] == "bash"
        assert lang_map["utils.py"] == "python"

    def test_nonexistent_dir(self, tmp_path):
        scripts = discover_scripts(tmp_path / "nonexistent")
        assert scripts == []

    def test_script_content_readable(self, fixtures_dir):
        scripts = discover_scripts(fixtures_dir / "malicious_credential_harvester")
        assert len(scripts) == 1
        assert scripts[0]["path"] == "setup.sh"
        assert "curl" in scripts[0]["content"]

    def test_supply_chain_scripts(self, fixtures_dir):
        scripts = discover_scripts(fixtures_dir / "supply_chain_timebomb")
        assert len(scripts) == 1
        assert scripts[0]["path"] == "loader.py"
        assert scripts[0]["language"] == "python"


# ── parse_skill integration tests ─────────────────────────────────────────────


class TestParseSkill:
    def test_clean_skill(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "clean_skill")
        assert isinstance(skill, SkillPackage)
        assert skill.name == "github"
        assert "GitHub" in skill.description
        assert skill.frontmatter["version"] == "1.2.0"
        assert skill.requires["bins"] == ["git", "gh"]
        assert skill.instructions.strip().startswith("# GitHub Integration")

    def test_clean_complex_skill(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "clean_complex_skill")
        assert skill.name == "data-pipeline"
        assert len(skill.scripts) == 2
        script_paths = [s["path"] for s in skill.scripts]
        assert "install.sh" in script_paths
        assert "utils.py" in script_paths
        assert len(skill.install_instructions) == 1
        assert "bash install.sh" in skill.install_instructions[0]["command"]

    def test_malicious_credential_harvester(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "malicious_credential_harvester")
        assert skill.name == "env-backup"
        assert len(skill.scripts) == 1
        assert skill.scripts[0]["language"] == "bash"

    def test_prompt_injection(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "prompt_injection_skill")
        assert skill.name == "friendly-helper"
        # The hidden HTML comments should be in the instructions
        assert "HEARTBEAT.md" in skill.instructions

    def test_obfuscated_payload(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "obfuscated_payload")
        assert skill.name == "text-formatter"
        assert len(skill.scripts) == 1
        assert "base64" in skill.scripts[0]["content"]

    def test_typosquat(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "typosquat_skill")
        assert skill.name == "githuh"

    def test_social_engineering(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "social_engineering_skill")
        assert skill.name == "smart-terminal"
        assert "curl" in skill.instructions

    def test_excessive_permissions(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "excessive_permissions_skill")
        assert skill.name == "text-beautifier"
        assert "sudo" in skill.requires["bins"]

    def test_memory_manipulation(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "memory_manipulation_skill")
        assert skill.name == "personality-enhancer"
        assert "MEMORY.md" in skill.instructions
        assert "SOUL.md" in skill.instructions

    def test_supply_chain_timebomb(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "supply_chain_timebomb")
        assert skill.name == "code-metrics"
        assert len(skill.scripts) == 1
        assert "urllib" in skill.scripts[0]["content"]

    def test_missing_skill_md_raises(self, tmp_path):
        with pytest.raises(ParseError, match="SKILL.md not found"):
            parse_skill(tmp_path)

    def test_missing_name_raises(self, tmp_path):
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text("---\ndescription: no name\n---\n# Test")
        with pytest.raises(ParseError, match="missing required 'name' field"):
            parse_skill(tmp_path)

    def test_all_fixtures_parse_without_crash(self, fixtures_dir):
        """Every fixture directory should parse successfully."""
        for fixture_dir in sorted(fixtures_dir.iterdir()):
            if fixture_dir.is_dir() and (fixture_dir / "SKILL.md").exists():
                skill = parse_skill(fixture_dir)
                assert skill.name
                assert skill.skill_md_raw
                assert skill.path == str(fixture_dir)

    def test_metadata_extracted(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "clean_skill")
        assert skill.metadata.get("openclaw", {}).get("category") == "developer-tools"

    def test_raw_content_preserved(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "clean_skill")
        assert skill.skill_md_raw.startswith("---")
        assert "name: github" in skill.skill_md_raw
