"""Scan report data models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

from clawguard.analyzers.base import Finding, SkillPackage
from clawguard.scoring.engine import TrustScore


@dataclass
class ScanReport:
    """Complete scan result for a skill package."""

    skill: SkillPackage
    findings: list[Finding]
    score: TrustScore
    analyzers_run: list[str]
    scan_duration_ms: int = 0
    scanned_at: datetime = field(default_factory=lambda: datetime.now(UTC))
