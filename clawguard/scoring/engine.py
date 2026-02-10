"""Weighted trust score computation from analyzer findings."""

from collections import Counter
from dataclasses import dataclass

from clawguard.analyzers.base import Category, Finding, Severity

# Points deducted per severity level
SEVERITY_DEDUCTIONS: dict[Severity, int] = {
    Severity.CRITICAL: 40,
    Severity.HIGH: 20,
    Severity.MEDIUM: 10,
    Severity.LOW: 3,
    Severity.INFO: 0,
}

# Category multipliers — more dangerous categories hit harder
CATEGORY_MULTIPLIERS: dict[Category, float] = {
    Category.MALWARE: 2.0,
    Category.PROMPT_INJECTION: 1.5,
    Category.CREDENTIAL_EXPOSURE: 1.5,
    Category.SOCIAL_ENGINEERING: 1.0,
    Category.NETWORK_EXFILTRATION: 1.0,
    Category.OBFUSCATION: 1.0,
    Category.EXCESSIVE_PERMISSIONS: 1.0,
    Category.TYPOSQUATTING: 1.0,
    Category.SUPPLY_CHAIN: 1.0,
    Category.MEMORY_MANIPULATION: 1.0,
    Category.BEST_PRACTICE: 1.0,
}

# Diminishing returns: 1st finding = full, 2nd = 0.5x, 3rd+ = 0.25x
DIMINISHING_FACTORS = [1.0, 0.5, 0.25]


def _grade_from_score(score: int) -> str:
    """Map numeric score to letter grade."""
    if score >= 80:
        return "A"
    if score >= 60:
        return "B"
    if score >= 40:
        return "C"
    if score >= 20:
        return "D"
    return "F"


def _recommendation_from_score(score: int) -> str:
    """Map numeric score to action recommendation."""
    if score >= 80:
        return "PASS"
    if score >= 50:
        return "CAUTION"
    if score >= 20:
        return "REVIEW"
    return "BLOCK"


def _build_summary(findings: list[Finding]) -> str:
    """Build a human-readable summary of findings by severity."""
    counts = Counter(f.severity for f in findings)
    parts = []
    for sev in Severity:
        count = counts.get(sev, 0)
        if count > 0:
            parts.append(f"{count} {sev.value}")
    if not parts:
        return "No findings"
    return ", ".join(parts) + f" finding{'s' if len(findings) != 1 else ''}"


@dataclass
class TrustScore:
    """Computed trust score for a skill package."""

    score: int              # 0-100
    grade: str              # A (80-100), B (60-79), C (40-59), D (20-39), F (0-19)
    summary: str            # "3 critical, 1 high, 2 medium findings"
    top_risks: list[str]    # Top 3 finding titles
    recommendation: str     # "BLOCK" / "REVIEW" / "CAUTION" / "PASS"


def compute_trust_score(findings: list[Finding]) -> TrustScore:
    """Compute a trust score from a list of findings.

    Algorithm:
    - Start at 100
    - For each finding: deduction = severity_points * category_multiplier * diminishing_factor
    - Multiple findings in same category get diminishing returns
    - Floor at 0
    """
    score = 100.0

    # Track how many findings per category for diminishing returns
    category_counts: dict[Category, int] = Counter()

    # Sort findings by severity (most severe first) for consistent ordering
    sorted_findings = sorted(
        findings,
        key=lambda f: list(Severity).index(f.severity),
    )

    for finding in sorted_findings:
        base_deduction = SEVERITY_DEDUCTIONS.get(finding.severity, 0)
        multiplier = CATEGORY_MULTIPLIERS.get(finding.category, 1.0)

        count = category_counts[finding.category]
        if count < len(DIMINISHING_FACTORS):
            diminish = DIMINISHING_FACTORS[count]
        else:
            diminish = DIMINISHING_FACTORS[-1]

        deduction = base_deduction * multiplier * diminish
        score -= deduction
        category_counts[finding.category] += 1

    final_score = max(0, int(score))

    # Top risks: top 3 most severe findings by title
    top_risks = [f.title for f in sorted_findings[:3]]

    return TrustScore(
        score=final_score,
        grade=_grade_from_score(final_score),
        summary=_build_summary(findings),
        top_risks=top_risks,
        recommendation=_recommendation_from_score(final_score),
    )
