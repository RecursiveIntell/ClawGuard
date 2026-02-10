"""Generate human-readable markdown reports."""

from clawguard.analyzers.base import Severity
from clawguard.reports.models import ScanReport

_SEVERITY_ICONS = {
    Severity.CRITICAL: "CRITICAL",
    Severity.HIGH: "HIGH",
    Severity.MEDIUM: "MEDIUM",
    Severity.LOW: "LOW",
    Severity.INFO: "INFO",
}

_SEVERITY_HEADERS = {
    Severity.CRITICAL: "Critical",
    Severity.HIGH: "High",
    Severity.MEDIUM: "Medium",
    Severity.LOW: "Low",
    Severity.INFO: "Informational",
}


def to_markdown(report: ScanReport) -> str:
    """Generate a markdown scan report."""
    lines = [
        f"# ClawGuard Scan Report: {report.skill.name}",
        "",
        f"**Trust Score**: {report.score.score}/100 ({report.score.grade})"
        f" — {report.score.recommendation}",
        f"**Scanned**: {report.scanned_at.strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Analyzers**: {', '.join(report.analyzers_run)}",
        f"**Duration**: {report.scan_duration_ms}ms",
        "",
        "## Summary",
        "",
        report.score.summary,
        "",
    ]

    if report.score.top_risks:
        lines.append("## Top Risks")
        lines.append("")
        for i, risk in enumerate(report.score.top_risks, 1):
            lines.append(f"{i}. {risk}")
        lines.append("")

    if report.findings:
        lines.append("## Findings")
        lines.append("")

        for severity in Severity:
            sev_findings = [
                f for f in report.findings if f.severity == severity
            ]
            if not sev_findings:
                continue

            lines.append(f"### {_SEVERITY_HEADERS[severity]}")
            lines.append("")

            for f in sev_findings:
                label = _SEVERITY_ICONS[f.severity]
                lines.append(f"**{label}**: {f.title}")
                if f.file:
                    loc = f"File: {f.file}"
                    if f.line:
                        loc += f", Line: {f.line}"
                    lines.append(f"  {loc}")
                if f.detail:
                    lines.append(f"  {f.detail}")
                if f.recommendation:
                    lines.append(f"  Recommendation: {f.recommendation}")
                lines.append("")
    else:
        lines.append("## Findings")
        lines.append("")
        lines.append("No issues found.")
        lines.append("")

    return "\n".join(lines)
