"""Tests for report generation (JSON, Markdown, HTML)."""

import json
from datetime import UTC, datetime

from clawguard.analyzers.base import Category, Finding, Severity, SkillPackage
from clawguard.reports.html_report import to_html
from clawguard.reports.json_report import report_to_dict, to_json
from clawguard.reports.markdown_report import to_markdown
from clawguard.reports.models import ScanReport
from clawguard.scoring.engine import TrustScore


def _make_report(findings=None, score=None):
    """Helper to build a ScanReport for testing."""
    skill = SkillPackage(
        name="test-skill",
        description="A test skill",
        path="/tmp/test",
        skill_md_raw="---\nname: test-skill\n---\n# Test",
        frontmatter={"name": "test-skill"},
        instructions="# Test",
    )
    if score is None:
        score = TrustScore(
            score=75,
            grade="B",
            summary="1 high finding",
            top_risks=["High risk item"],
            recommendation="CAUTION",
        )
    return ScanReport(
        skill=skill,
        findings=findings or [],
        score=score,
        analyzers_run=["static", "ast"],
        scan_duration_ms=42,
        scanned_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
    )


def _sample_finding():
    return Finding(
        analyzer="static",
        category=Category.CREDENTIAL_EXPOSURE,
        severity=Severity.HIGH,
        title="API key detected",
        detail="Found hardcoded API key in setup.sh",
        file="setup.sh",
        line=5,
        evidence="sk-abc123...",
        recommendation="Remove the hardcoded key.",
    )


# ── JSON report tests ────────────────────────────────────────────────────────


class TestJsonReport:
    def test_to_json_valid(self):
        report = _make_report()
        result = to_json(report)
        parsed = json.loads(result)
        assert parsed["skill"]["name"] == "test-skill"
        assert parsed["score"]["score"] == 75
        assert parsed["score"]["grade"] == "B"

    def test_to_json_with_findings(self):
        report = _make_report(findings=[_sample_finding()])
        result = to_json(report)
        parsed = json.loads(result)
        assert len(parsed["findings"]) == 1
        assert parsed["findings"][0]["category"] == "credential_exposure"
        assert parsed["findings"][0]["severity"] == "high"

    def test_to_json_empty_findings(self):
        report = _make_report()
        result = to_json(report)
        parsed = json.loads(result)
        assert parsed["findings"] == []

    def test_report_to_dict_roundtrips(self):
        report = _make_report(findings=[_sample_finding()])
        d = report_to_dict(report)
        json_str = json.dumps(d)
        parsed = json.loads(json_str)
        assert parsed["skill"]["name"] == "test-skill"

    def test_scanned_at_is_iso(self):
        report = _make_report()
        result = to_json(report)
        parsed = json.loads(result)
        assert "2025-01-15" in parsed["scanned_at"]


# ── Markdown report tests ────────────────────────────────────────────────────


class TestMarkdownReport:
    def test_contains_skill_name(self):
        report = _make_report()
        md = to_markdown(report)
        assert "test-skill" in md

    def test_contains_score(self):
        report = _make_report()
        md = to_markdown(report)
        assert "75/100" in md
        assert "(B)" in md

    def test_contains_recommendation(self):
        report = _make_report()
        md = to_markdown(report)
        assert "CAUTION" in md

    def test_findings_grouped_by_severity(self):
        report = _make_report(findings=[_sample_finding()])
        md = to_markdown(report)
        assert "### High" in md
        assert "API key detected" in md

    def test_no_findings_message(self):
        score = TrustScore(
            score=100, grade="A", summary="No findings",
            top_risks=[], recommendation="PASS",
        )
        report = _make_report(score=score)
        md = to_markdown(report)
        assert "No issues found" in md

    def test_top_risks_listed(self):
        report = _make_report()
        md = to_markdown(report)
        assert "High risk item" in md

    def test_finding_file_and_line(self):
        report = _make_report(findings=[_sample_finding()])
        md = to_markdown(report)
        assert "setup.sh" in md
        assert "Line: 5" in md


# ── HTML report tests ────────────────────────────────────────────────────────


class TestHtmlReport:
    def test_is_valid_html(self):
        report = _make_report()
        html = to_html(report)
        assert html.startswith("<!DOCTYPE html>")
        assert "</html>" in html

    def test_self_contained(self):
        report = _make_report()
        html = to_html(report)
        assert "<style>" in html
        # No external CSS/JS links
        assert 'href="http' not in html
        assert 'src="http' not in html

    def test_contains_score(self):
        report = _make_report()
        html = to_html(report)
        assert "75/100" in html
        assert "Grade: B" in html

    def test_contains_findings(self):
        report = _make_report(findings=[_sample_finding()])
        html = to_html(report)
        assert "API key detected" in html
        assert "HIGH" in html

    def test_no_findings_message(self):
        score = TrustScore(
            score=100, grade="A", summary="No findings",
            top_risks=[], recommendation="PASS",
        )
        report = _make_report(score=score)
        html = to_html(report)
        assert "No issues found" in html

    def test_escapes_html(self):
        finding = Finding(
            analyzer="test",
            category=Category.MALWARE,
            severity=Severity.CRITICAL,
            title="<script>alert('xss')</script>",
            detail="Test <b>detail</b>",
        )
        report = _make_report(findings=[finding])
        html = to_html(report)
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
