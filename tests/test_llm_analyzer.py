"""Tests for the LLM analyzer (mocked — no real API calls)."""

from unittest.mock import MagicMock, patch

from clawguard.analyzers.base import Category, Severity, SkillPackage
from clawguard.analyzers.llm import LLMAnalyzer, _build_user_prompt, _parse_llm_response


def _make_skill(**kwargs):
    """Helper to create a minimal SkillPackage for testing."""
    defaults = {
        "name": "test-skill",
        "description": "A test skill",
        "path": "/tmp/test",
        "skill_md_raw": "---\nname: test-skill\n---\n# Test",
        "frontmatter": {"name": "test-skill"},
        "instructions": "# Test",
        "scripts": [],
    }
    defaults.update(kwargs)
    return SkillPackage(**defaults)


# ── _build_user_prompt tests ──────────────────────────────────────────────────


class TestBuildUserPrompt:
    def test_includes_skill_name(self):
        skill = _make_skill(name="my-skill")
        prompt = _build_user_prompt(skill)
        assert "my-skill" in prompt

    def test_includes_description(self):
        skill = _make_skill(description="Does cool things")
        prompt = _build_user_prompt(skill)
        assert "Does cool things" in prompt

    def test_includes_skill_md_raw(self):
        skill = _make_skill(skill_md_raw="# Full content here")
        prompt = _build_user_prompt(skill)
        assert "# Full content here" in prompt

    def test_includes_scripts(self):
        skill = _make_skill(scripts=[{
            "path": "helper.py",
            "content": "print('hello')",
            "language": "python",
        }])
        prompt = _build_user_prompt(skill)
        assert "helper.py" in prompt
        assert "print('hello')" in prompt

    def test_includes_metadata(self):
        skill = _make_skill(frontmatter={"name": "test", "version": "1.0"})
        prompt = _build_user_prompt(skill)
        assert '"version": "1.0"' in prompt


# ── _parse_llm_response tests ────────────────────────────────────────────────


class TestParseLlmResponse:
    def test_valid_json_array(self):
        response = '[{"category": "malware", "severity": "critical", "title": "Bad"}]'
        result = _parse_llm_response(response)
        assert len(result) == 1
        assert result[0]["title"] == "Bad"

    def test_empty_array(self):
        result = _parse_llm_response("[]")
        assert result == []

    def test_json_with_surrounding_text(self):
        response = 'Here are my findings:\n[{"title": "Issue"}]\nThat is all.'
        result = _parse_llm_response(response)
        assert len(result) == 1

    def test_malformed_json(self):
        result = _parse_llm_response("{not valid json")
        assert result == []

    def test_no_json_at_all(self):
        result = _parse_llm_response("No issues found.")
        assert result == []

    def test_json_not_list(self):
        result = _parse_llm_response('{"single": "object"}')
        assert result == []


# ── LLMAnalyzer tests ────────────────────────────────────────────────────────


class TestLLMAnalyzer:
    def setup_method(self):
        self.analyzer = LLMAnalyzer()

    def test_name(self):
        assert self.analyzer.name == "llm"

    def test_supports_without_api_key(self):
        skill = _make_skill()
        with patch("clawguard.analyzers.llm.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = ""
            assert self.analyzer.supports(skill) is False

    def test_supports_with_api_key(self):
        skill = _make_skill()
        with patch("clawguard.analyzers.llm.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "sk-test-key"
            assert self.analyzer.supports(skill) is True

    def test_analyze_returns_empty_without_key(self):
        skill = _make_skill()
        with patch("clawguard.analyzers.llm.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = ""
            findings = self.analyzer.analyze(skill)
            assert findings == []

    @patch("clawguard.analyzers.llm.anthropic.Anthropic")
    def test_analyze_with_valid_response(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_message = MagicMock()
        llm_json = (
            '[{"category": "malware", "severity": "critical",'
            ' "title": "Bad stuff", "detail": "Very bad",'
            ' "file": "setup.sh",'
            ' "evidence": "curl http://evil.com",'
            ' "recommendation": "Remove it"}]'
        )
        mock_message.content = [MagicMock(text=llm_json)]
        mock_message.usage.input_tokens = 100
        mock_message.usage.output_tokens = 50
        mock_client.messages.create.return_value = mock_message

        skill = _make_skill()
        with patch("clawguard.analyzers.llm.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "sk-test-key"
            mock_settings.CLAWGUARD_MODEL = "claude-sonnet-4-5-20250929"
            findings = self.analyzer.analyze(skill)

        assert len(findings) == 1
        assert findings[0].category == Category.MALWARE
        assert findings[0].severity == Severity.CRITICAL
        assert findings[0].title == "Bad stuff"
        assert findings[0].analyzer == "llm"

    @patch("clawguard.analyzers.llm.anthropic.Anthropic")
    def test_analyze_with_empty_response(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="[]")]
        mock_message.usage.input_tokens = 100
        mock_message.usage.output_tokens = 5
        mock_client.messages.create.return_value = mock_message

        skill = _make_skill()
        with patch("clawguard.analyzers.llm.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "sk-test-key"
            mock_settings.CLAWGUARD_MODEL = "claude-sonnet-4-5-20250929"
            findings = self.analyzer.analyze(skill)

        assert findings == []

    @patch("clawguard.analyzers.llm.anthropic.Anthropic")
    def test_analyze_api_error_returns_empty(self, mock_anthropic_cls):
        import anthropic

        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.side_effect = anthropic.APIError(
            message="Server error",
            request=MagicMock(),
            body=None,
        )

        skill = _make_skill()
        with patch("clawguard.analyzers.llm.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "sk-test-key"
            mock_settings.CLAWGUARD_MODEL = "claude-sonnet-4-5-20250929"
            findings = self.analyzer.analyze(skill)

        assert findings == []

    @patch("clawguard.analyzers.llm.anthropic.Anthropic")
    def test_analyze_rate_limit_returns_empty(self, mock_anthropic_cls):
        import anthropic

        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.side_effect = anthropic.RateLimitError(
            message="Rate limited",
            response=MagicMock(status_code=429, headers={}),
            body=None,
        )

        skill = _make_skill()
        with patch("clawguard.analyzers.llm.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "sk-test-key"
            mock_settings.CLAWGUARD_MODEL = "claude-sonnet-4-5-20250929"
            findings = self.analyzer.analyze(skill)

        assert findings == []

    def test_map_findings_unknown_category(self):
        raw = [{"category": "unknown_cat", "severity": "high", "title": "Test"}]
        findings = self.analyzer._map_findings(raw)
        assert len(findings) == 1
        assert findings[0].category == Category.MALWARE  # default

    def test_map_findings_unknown_severity(self):
        raw = [{"category": "malware", "severity": "unknown_sev", "title": "Test"}]
        findings = self.analyzer._map_findings(raw)
        assert len(findings) == 1
        assert findings[0].severity == Severity.MEDIUM  # default

    def test_map_findings_skips_non_dicts(self):
        raw = [{"title": "Valid"}, "not a dict", 42, None]
        findings = self.analyzer._map_findings(raw)
        assert len(findings) == 1
