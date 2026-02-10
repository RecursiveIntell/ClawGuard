"""Tests for the static analyzer."""

from clawguard.analyzers.base import Category, Finding, Severity
from clawguard.analyzers.static import StaticAnalyzer
from clawguard.parser.skill import parse_skill


class TestStaticAnalyzer:
    def setup_method(self):
        self.analyzer = StaticAnalyzer()

    def test_name(self):
        assert self.analyzer.name == "static"

    def test_clean_skill_minimal_findings(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "clean_skill")
        findings = self.analyzer.analyze(skill)
        # Clean skill should not have critical/high findings
        severe = [f for f in findings if f.severity in (Severity.CRITICAL, Severity.HIGH)]
        assert len(severe) == 0

    def test_clean_complex_skill_minimal_findings(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "clean_complex_skill")
        findings = self.analyzer.analyze(skill)
        severe = [f for f in findings if f.severity in (Severity.CRITICAL, Severity.HIGH)]
        assert len(severe) == 0

    def test_credential_harvester_detected(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "malicious_credential_harvester")
        findings = self.analyzer.analyze(skill)
        categories = {f.category for f in findings}
        assert Category.CREDENTIAL_EXPOSURE in categories
        # Should also detect known malicious publisher
        assert Category.MALWARE in categories

    def test_credential_harvester_has_c2_domain(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "malicious_credential_harvester")
        findings = self.analyzer.analyze(skill)
        c2_findings = [f for f in findings if f.category == Category.NETWORK_EXFILTRATION]
        assert len(c2_findings) > 0

    def test_prompt_injection_detected(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "prompt_injection_skill")
        findings = self.analyzer.analyze(skill)
        categories = {f.category for f in findings}
        has_injection = Category.PROMPT_INJECTION in categories
        has_memory = Category.MEMORY_MANIPULATION in categories
        assert has_injection or has_memory

    def test_obfuscated_payload_detected(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "obfuscated_payload")
        findings = self.analyzer.analyze(skill)
        categories = {f.category for f in findings}
        assert Category.OBFUSCATION in categories

    def test_social_engineering_detected(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "social_engineering_skill")
        findings = self.analyzer.analyze(skill)
        categories = {f.category for f in findings}
        assert Category.SOCIAL_ENGINEERING in categories

    def test_excessive_permissions_detected(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "excessive_permissions_skill")
        findings = self.analyzer.analyze(skill)
        categories = {f.category for f in findings}
        assert Category.EXCESSIVE_PERMISSIONS in categories

    def test_memory_manipulation_detected(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "memory_manipulation_skill")
        findings = self.analyzer.analyze(skill)
        categories = {f.category for f in findings}
        assert Category.MEMORY_MANIPULATION in categories

    def test_supply_chain_detected(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "supply_chain_timebomb")
        findings = self.analyzer.analyze(skill)
        categories = {f.category for f in findings}
        assert Category.SUPPLY_CHAIN in categories or Category.NETWORK_EXFILTRATION in categories

    def test_findings_are_finding_instances(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "malicious_credential_harvester")
        findings = self.analyzer.analyze(skill)
        assert all(isinstance(f, Finding) for f in findings)

    def test_findings_have_file_and_analyzer(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "malicious_credential_harvester")
        findings = self.analyzer.analyze(skill)
        for f in findings:
            assert f.analyzer == "static"
            assert f.file is not None

    def test_known_malicious_publisher(self, fixtures_dir):
        skill = parse_skill(fixtures_dir / "malicious_credential_harvester")
        findings = self.analyzer.analyze(skill)
        publisher_findings = [
            f for f in findings
            if f.category == Category.MALWARE and "publisher" in f.title.lower()
        ]
        assert len(publisher_findings) == 1
        assert "helpfuldev42" in publisher_findings[0].evidence

    def test_yara_rules_loaded(self):
        assert self.analyzer._yara_rules is not None
