"""Tests for the scan pipeline."""

from clawguard.analyzers.base import Category, Severity
from clawguard.pipeline import ScanOptions, ScanPipeline
from clawguard.reports.models import ScanReport
from clawguard.scoring.engine import TrustScore


class TestScanPipeline:
    def test_scan_clean_skill(self, fixtures_dir):
        pipeline = ScanPipeline(ScanOptions(skip_llm=True))
        report = pipeline.scan(fixtures_dir / "clean_skill")
        assert isinstance(report, ScanReport)
        assert report.skill.name == "github"
        assert isinstance(report.score, TrustScore)
        assert report.score.recommendation == "PASS"
        assert report.scan_duration_ms >= 0

    def test_scan_malicious_skill(self, fixtures_dir):
        pipeline = ScanPipeline(ScanOptions(skip_llm=True))
        report = pipeline.scan(fixtures_dir / "malicious_credential_harvester")
        assert report.score.score < 80
        assert len(report.findings) > 0
        categories = {f.category for f in report.findings}
        assert Category.CREDENTIAL_EXPOSURE in categories or Category.MALWARE in categories

    def test_scan_records_analyzers_run(self, fixtures_dir):
        pipeline = ScanPipeline(ScanOptions(skip_llm=True))
        report = pipeline.scan(fixtures_dir / "clean_skill")
        assert "static" in report.analyzers_run

    def test_skip_llm_option(self, fixtures_dir):
        pipeline = ScanPipeline(ScanOptions(skip_llm=True))
        report = pipeline.scan(fixtures_dir / "clean_skill")
        assert "llm" not in report.analyzers_run

    def test_skip_ast_option(self, fixtures_dir):
        pipeline = ScanPipeline(ScanOptions(skip_ast=True, skip_llm=True))
        report = pipeline.scan(fixtures_dir / "clean_complex_skill")
        assert "ast" not in report.analyzers_run

    def test_ast_runs_on_skills_with_scripts(self, fixtures_dir):
        pipeline = ScanPipeline(ScanOptions(skip_llm=True))
        report = pipeline.scan(fixtures_dir / "clean_complex_skill")
        assert "ast" in report.analyzers_run

    def test_ast_skipped_on_skills_without_scripts(self, fixtures_dir):
        pipeline = ScanPipeline(ScanOptions(skip_llm=True))
        report = pipeline.scan(fixtures_dir / "clean_skill")
        # clean_skill has no bundled scripts, AST should not run
        assert "ast" not in report.analyzers_run

    def test_scan_has_scanned_at(self, fixtures_dir):
        pipeline = ScanPipeline(ScanOptions(skip_llm=True))
        report = pipeline.scan(fixtures_dir / "clean_skill")
        assert report.scanned_at is not None

    def test_scan_obfuscated_payload(self, fixtures_dir):
        pipeline = ScanPipeline(ScanOptions(skip_llm=True))
        report = pipeline.scan(fixtures_dir / "obfuscated_payload")
        assert report.score.score < 80
        assert any(f.severity == Severity.HIGH for f in report.findings)

    def test_scan_all_fixtures(self, fixtures_dir):
        """Pipeline should never crash on any fixture."""
        pipeline = ScanPipeline(ScanOptions(skip_llm=True))
        for fixture_dir in sorted(fixtures_dir.iterdir()):
            if fixture_dir.is_dir() and (fixture_dir / "SKILL.md").exists():
                report = pipeline.scan(fixture_dir)
                assert isinstance(report, ScanReport)
                assert report.skill.name
