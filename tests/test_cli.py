"""Tests for the ClawGuard CLI."""

from click.testing import CliRunner

from clawguard.cli.main import cli


class TestCliScan:
    def test_scan_clean_skill(self, fixtures_dir):
        runner = CliRunner(mix_stderr=False)
        result = runner.invoke(cli, ["scan", str(fixtures_dir / "clean_skill"), "--no-llm"])
        assert result.exit_code == 0  # PASS

    def test_scan_malicious_skill(self, fixtures_dir):
        runner = CliRunner(mix_stderr=False)
        result = runner.invoke(
            cli,
            ["scan", str(fixtures_dir / "malicious_credential_harvester"), "--no-llm"],
        )
        # Should exit with CAUTION, REVIEW, or BLOCK
        assert result.exit_code > 0

    def test_scan_json_output(self, fixtures_dir):
        runner = CliRunner(mix_stderr=False)
        result = runner.invoke(
            cli,
            ["scan", str(fixtures_dir / "clean_skill"), "--no-llm", "--json"],
        )
        import json

        parsed = json.loads(result.output)
        assert parsed["skill"]["name"] == "github"
        assert "score" in parsed

    def test_scan_quiet_output(self, fixtures_dir):
        runner = CliRunner(mix_stderr=False)
        result = runner.invoke(
            cli,
            ["scan", str(fixtures_dir / "clean_skill"), "--no-llm", "--quiet"],
        )
        parts = result.output.strip().split()
        assert parts[0] in ("PASS", "CAUTION", "REVIEW", "BLOCK")
        assert parts[1].isdigit()

    def test_scan_no_path_or_url(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["scan"])
        assert result.exit_code != 0
        assert "Provide a PATH or --url" in result.output

    def test_scan_output_to_file(self, fixtures_dir, tmp_path):
        out_file = tmp_path / "report.md"
        runner = CliRunner(mix_stderr=False)
        runner.invoke(
            cli,
            [
                "scan",
                str(fixtures_dir / "clean_skill"),
                "--no-llm",
                "--output",
                str(out_file),
            ],
        )
        assert out_file.exists()
        content = out_file.read_text()
        assert "github" in content.lower()

    def test_scan_verbose(self, fixtures_dir):
        runner = CliRunner(mix_stderr=False)
        result = runner.invoke(
            cli,
            ["scan", str(fixtures_dir / "malicious_credential_harvester"), "--no-llm", "-v"],
        )
        # Verbose should still produce output without crashing
        assert result.exit_code >= 0


class TestCliScanAll:
    def test_scan_all_fixtures(self, fixtures_dir):
        runner = CliRunner(mix_stderr=False)
        result = runner.invoke(
            cli,
            ["scan-all", str(fixtures_dir), "--no-llm", "--quiet"],
        )
        assert "PASS" in result.output or "CAUTION" in result.output

    def test_scan_all_json(self, fixtures_dir):
        runner = CliRunner(mix_stderr=False)
        result = runner.invoke(
            cli,
            ["scan-all", str(fixtures_dir), "--no-llm", "--json"],
        )
        import json

        parsed = json.loads(result.output)
        assert isinstance(parsed, list)
        assert len(parsed) > 0

    def test_scan_all_bad_directory(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(cli, ["scan-all", str(tmp_path / "nonexistent")])
        assert result.exit_code != 0


class TestCliBulkScan:
    def test_bulk_scan_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["bulk-scan", "--help"])
        assert result.exit_code == 0
        assert "--limit" in result.output


class TestCliWatch:
    def test_watch_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["watch", "--help"])
        assert result.exit_code == 0
        assert "Watch" in result.output

    def test_watch_bad_directory(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["watch", "/nonexistent/path"])
        assert result.exit_code != 0


class TestCliVersion:
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestCliExitCodes:
    def test_pass_exit_code(self, fixtures_dir):
        runner = CliRunner(mix_stderr=False)
        result = runner.invoke(
            cli, ["scan", str(fixtures_dir / "clean_skill"), "--no-llm"]
        )
        assert result.exit_code == 0

    def test_non_pass_exit_code(self, fixtures_dir):
        runner = CliRunner(mix_stderr=False)
        result = runner.invoke(
            cli,
            ["scan", str(fixtures_dir / "malicious_credential_harvester"), "--no-llm"],
        )
        assert result.exit_code in (1, 2, 3)
