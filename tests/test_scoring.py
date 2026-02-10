"""Tests for the trust score engine — targeting 100% coverage."""

from clawguard.analyzers.base import Category, Finding, Severity
from clawguard.scoring.engine import TrustScore, compute_trust_score


def _finding(
    category=Category.MALWARE,
    severity=Severity.CRITICAL,
    title="Test finding",
):
    """Helper to create a minimal Finding."""
    return Finding(
        analyzer="test",
        category=category,
        severity=severity,
        title=title,
        detail="Test detail",
    )


class TestComputeTrustScore:
    def test_no_findings_gives_100(self):
        result = compute_trust_score([])
        assert result.score == 100
        assert result.grade == "A"
        assert result.recommendation == "PASS"
        assert result.top_risks == []
        assert result.summary == "No findings"

    def test_one_critical_malware(self):
        """CRITICAL=40 * MALWARE=2.0 = 80 deducted -> score 20."""
        findings = [_finding(Category.MALWARE, Severity.CRITICAL)]
        result = compute_trust_score(findings)
        assert result.score == 20
        assert result.grade == "D"
        assert result.recommendation == "REVIEW"

    def test_one_critical_generic(self):
        """CRITICAL=40 * 1.0 = 40 deducted -> score 60."""
        findings = [_finding(Category.OBFUSCATION, Severity.CRITICAL)]
        result = compute_trust_score(findings)
        assert result.score == 60
        assert result.grade == "B"
        assert result.recommendation == "CAUTION"

    def test_one_high_finding(self):
        """HIGH=20 * 1.0 = 20 deducted -> score 80."""
        findings = [_finding(Category.SUPPLY_CHAIN, Severity.HIGH)]
        result = compute_trust_score(findings)
        assert result.score == 80
        assert result.grade == "A"
        assert result.recommendation == "PASS"

    def test_one_medium_finding(self):
        """MEDIUM=10 * 1.0 = 10 deducted -> score 90."""
        findings = [_finding(Category.OBFUSCATION, Severity.MEDIUM)]
        result = compute_trust_score(findings)
        assert result.score == 90

    def test_one_low_finding(self):
        """LOW=3 * 1.0 = 3 deducted -> score 97."""
        findings = [_finding(Category.BEST_PRACTICE, Severity.LOW)]
        result = compute_trust_score(findings)
        assert result.score == 97

    def test_info_findings_no_deduction(self):
        findings = [_finding(Category.BEST_PRACTICE, Severity.INFO)]
        result = compute_trust_score(findings)
        assert result.score == 100

    def test_two_critical_malware_block(self):
        """2 CRITICAL MALWARE: 40*2*1.0 + 40*2*0.5 = 80+40 = 120 -> floor 0."""
        findings = [
            _finding(Category.MALWARE, Severity.CRITICAL, "Finding 1"),
            _finding(Category.MALWARE, Severity.CRITICAL, "Finding 2"),
        ]
        result = compute_trust_score(findings)
        assert result.score == 0
        assert result.grade == "F"
        assert result.recommendation == "BLOCK"

    def test_diminishing_returns_same_category(self):
        """3 findings in same category: 1st=full, 2nd=0.5x, 3rd=0.25x."""
        findings = [
            _finding(Category.OBFUSCATION, Severity.MEDIUM, "First"),
            _finding(Category.OBFUSCATION, Severity.MEDIUM, "Second"),
            _finding(Category.OBFUSCATION, Severity.MEDIUM, "Third"),
        ]
        # 10*1.0 + 10*0.5 + 10*0.25 = 10+5+2.5 = 17.5 -> 82
        result = compute_trust_score(findings)
        assert result.score == 82

    def test_fourth_finding_uses_last_diminishing(self):
        """4th+ finding in same category uses 0.25x factor."""
        findings = [
            _finding(Category.OBFUSCATION, Severity.MEDIUM, f"F{i}")
            for i in range(4)
        ]
        # 10*1.0 + 10*0.5 + 10*0.25 + 10*0.25 = 20 -> 80
        result = compute_trust_score(findings)
        assert result.score == 80

    def test_different_categories_no_diminishing(self):
        """Findings in different categories each get full deduction."""
        findings = [
            _finding(Category.OBFUSCATION, Severity.MEDIUM, "Obfusc"),
            _finding(Category.SUPPLY_CHAIN, Severity.MEDIUM, "Supply"),
        ]
        # 10*1.0 + 10*1.0 = 20 deducted -> 80
        result = compute_trust_score(findings)
        assert result.score == 80

    def test_credential_exposure_multiplier(self):
        """CREDENTIAL_EXPOSURE has 1.5x multiplier."""
        findings = [_finding(Category.CREDENTIAL_EXPOSURE, Severity.HIGH)]
        # 20 * 1.5 = 30 deducted -> 70
        result = compute_trust_score(findings)
        assert result.score == 70

    def test_prompt_injection_multiplier(self):
        """PROMPT_INJECTION has 1.5x multiplier."""
        findings = [_finding(Category.PROMPT_INJECTION, Severity.HIGH)]
        # 20 * 1.5 = 30 deducted -> 70
        result = compute_trust_score(findings)
        assert result.score == 70

    def test_floor_at_zero(self):
        """Score never goes below 0."""
        findings = [
            _finding(Category.MALWARE, Severity.CRITICAL, f"F{i}")
            for i in range(10)
        ]
        result = compute_trust_score(findings)
        assert result.score == 0

    def test_grade_boundaries(self):
        # Test each grade boundary
        assert compute_trust_score([]).grade == "A"  # 100

        # B: 60-79 -> one critical generic = 60
        f60 = [_finding(Category.OBFUSCATION, Severity.CRITICAL)]
        assert compute_trust_score(f60).grade == "B"

        # C: 40-59 -> CRITICAL prompt_injection = 40*1.5=60 deducted -> 40
        f40 = [_finding(Category.PROMPT_INJECTION, Severity.CRITICAL)]
        assert compute_trust_score(f40).grade == "C"

        # D: 20-39 -> CRITICAL malware = 40*2=80 deducted -> 20
        f20 = [_finding(Category.MALWARE, Severity.CRITICAL)]
        assert compute_trust_score(f20).grade == "D"

        # F: 0-19
        f0 = [
            _finding(Category.MALWARE, Severity.CRITICAL, "F1"),
            _finding(Category.MALWARE, Severity.CRITICAL, "F2"),
        ]
        assert compute_trust_score(f0).grade == "F"

    def test_recommendation_boundaries(self):
        assert compute_trust_score([]).recommendation == "PASS"  # 100

        # CAUTION: 50-79
        f_caution = [_finding(Category.OBFUSCATION, Severity.CRITICAL)]
        assert compute_trust_score(f_caution).recommendation == "CAUTION"  # 60

        # REVIEW: 20-49
        f_review = [_finding(Category.PROMPT_INJECTION, Severity.CRITICAL)]
        assert compute_trust_score(f_review).recommendation == "REVIEW"  # 40

        # BLOCK: <20
        f_block = [
            _finding(Category.MALWARE, Severity.CRITICAL, "F1"),
            _finding(Category.MALWARE, Severity.CRITICAL, "F2"),
        ]
        assert compute_trust_score(f_block).recommendation == "BLOCK"  # 0

    def test_top_risks_max_three(self):
        findings = [
            _finding(Category.MALWARE, Severity.CRITICAL, "Risk 1"),
            _finding(Category.OBFUSCATION, Severity.HIGH, "Risk 2"),
            _finding(Category.SUPPLY_CHAIN, Severity.MEDIUM, "Risk 3"),
            _finding(Category.BEST_PRACTICE, Severity.LOW, "Risk 4"),
        ]
        result = compute_trust_score(findings)
        assert len(result.top_risks) == 3

    def test_top_risks_ordered_by_severity(self):
        findings = [
            _finding(Category.BEST_PRACTICE, Severity.LOW, "Low risk"),
            _finding(Category.MALWARE, Severity.CRITICAL, "Critical risk"),
            _finding(Category.OBFUSCATION, Severity.MEDIUM, "Medium risk"),
        ]
        result = compute_trust_score(findings)
        assert result.top_risks[0] == "Critical risk"

    def test_summary_format(self):
        findings = [
            _finding(Category.MALWARE, Severity.CRITICAL, "F1"),
            _finding(Category.OBFUSCATION, Severity.HIGH, "F2"),
            _finding(Category.SUPPLY_CHAIN, Severity.HIGH, "F3"),
        ]
        result = compute_trust_score(findings)
        assert "1 critical" in result.summary
        assert "2 high" in result.summary
        assert "findings" in result.summary

    def test_summary_single_finding(self):
        findings = [_finding(Category.MALWARE, Severity.CRITICAL)]
        result = compute_trust_score(findings)
        assert "finding" in result.summary
        assert "findings" not in result.summary

    def test_returns_trust_score_dataclass(self):
        result = compute_trust_score([])
        assert isinstance(result, TrustScore)

    def test_mixed_real_scenario(self):
        """Simulate a realistic scan with mixed findings."""
        findings = [
            _finding(Category.CREDENTIAL_EXPOSURE, Severity.HIGH, "Env harvesting"),
            _finding(Category.SOCIAL_ENGINEERING, Severity.CRITICAL, "curl|bash"),
            _finding(Category.MEMORY_MANIPULATION, Severity.CRITICAL, "HEARTBEAT write"),
            _finding(Category.OBFUSCATION, Severity.MEDIUM, "base64 decode"),
        ]
        result = compute_trust_score(findings)
        assert result.score < 50
        assert result.recommendation in ("BLOCK", "REVIEW")
