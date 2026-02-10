"""Scan pipeline — orchestrates parse, analyze, score stages."""

import time
from dataclasses import dataclass
from pathlib import Path

import structlog

from clawguard.analyzers.ast_analyzer import ASTAnalyzer
from clawguard.analyzers.base import AnalyzerBase, Category, Finding, Severity, SkillPackage
from clawguard.analyzers.llm import LLMAnalyzer
from clawguard.analyzers.static import StaticAnalyzer
from clawguard.parser.skill import parse_skill
from clawguard.reports.models import ScanReport
from clawguard.scoring.engine import compute_trust_score

logger = structlog.get_logger()


@dataclass
class ScanOptions:
    """Options controlling which analyzers run."""

    skip_llm: bool = False
    skip_ast: bool = False
    timeout: int = 120


class ScanPipeline:
    """Main scan pipeline: parse -> analyze -> score -> report."""

    def __init__(self, options: ScanOptions | None = None) -> None:
        self.options = options or ScanOptions()
        self.analyzers: list[AnalyzerBase] = self._build_analyzers()

    def _build_analyzers(self) -> list[AnalyzerBase]:
        """Build the analyzer list based on options."""
        analyzers: list[AnalyzerBase] = [StaticAnalyzer()]
        if not self.options.skip_ast:
            analyzers.append(ASTAnalyzer())
        if not self.options.skip_llm:
            analyzers.append(LLMAnalyzer())
        return analyzers

    def scan(self, skill_path: str | Path) -> ScanReport:
        """Run the full scan pipeline on a local skill directory."""
        start = time.monotonic()

        skill = parse_skill(skill_path)
        all_findings = self._run_analyzers(skill)
        score = compute_trust_score(all_findings)

        duration_ms = int((time.monotonic() - start) * 1000)

        return ScanReport(
            skill=skill,
            findings=all_findings,
            score=score,
            analyzers_run=[
                a.name for a in self.analyzers if a.supports(skill)
            ],
            scan_duration_ms=duration_ms,
        )

    def _run_analyzers(self, skill: SkillPackage) -> list[Finding]:
        """Run all applicable analyzers, catching errors gracefully."""
        all_findings: list[Finding] = []

        for analyzer in self.analyzers:
            if not analyzer.supports(skill):
                logger.info(
                    "analyzer_skipped",
                    analyzer=analyzer.name,
                    skill=skill.name,
                )
                continue

            try:
                findings = analyzer.analyze(skill)
                all_findings.extend(findings)
                logger.info(
                    "analyzer_complete",
                    analyzer=analyzer.name,
                    findings_count=len(findings),
                )
            except Exception as e:
                logger.error(
                    "analyzer_failed",
                    analyzer=analyzer.name,
                    error=str(e),
                )
                all_findings.append(
                    Finding(
                        analyzer=analyzer.name,
                        category=Category.BEST_PRACTICE,
                        severity=Severity.INFO,
                        title=f"Analyzer {analyzer.name} failed",
                        detail=f"The {analyzer.name} analyzer encountered an error: {e}",
                        recommendation="Check analyzer configuration.",
                    )
                )

        return all_findings
