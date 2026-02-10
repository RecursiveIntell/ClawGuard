"""Generate self-contained HTML scan reports."""

import html

from clawguard.analyzers.base import Severity
from clawguard.reports.models import ScanReport

_SEVERITY_COLORS = {
    Severity.CRITICAL: "#dc2626",
    Severity.HIGH: "#ea580c",
    Severity.MEDIUM: "#ca8a04",
    Severity.LOW: "#2563eb",
    Severity.INFO: "#6b7280",
}

_SCORE_COLOR_THRESHOLDS = [
    (80, "#16a34a"),
    (60, "#ca8a04"),
    (40, "#ea580c"),
    (20, "#dc2626"),
    (0, "#991b1b"),
]

_CSS = """
body { font-family: -apple-system, sans-serif; max-width: 800px;
       margin: 0 auto; padding: 2rem; background: #0f172a; color: #e2e8f0; }
h1 { color: #f8fafc; border-bottom: 2px solid #334155; padding-bottom: 0.5rem; }
h2 { color: #94a3b8; margin-top: 2rem; }
.score-box { text-align: center; padding: 1.5rem; border-radius: 12px;
             background: #1e293b; margin: 1rem 0; }
.score-num { font-size: 3rem; font-weight: bold; }
.grade { font-size: 1.5rem; opacity: 0.8; }
.rec { font-size: 1.2rem; padding: 0.5rem 1rem; border-radius: 6px;
       display: inline-block; margin-top: 0.5rem; color: #fff; }
.finding { background: #1e293b; border-left: 4px solid; padding: 1rem;
           margin: 0.5rem 0; border-radius: 0 8px 8px 0; }
.finding-title { font-weight: bold; }
.finding-detail { color: #94a3b8; margin-top: 0.5rem; font-size: 0.9rem; }
.finding-meta { color: #64748b; font-size: 0.85rem; margin-top: 0.25rem; }
.summary { color: #94a3b8; }
.no-issues { color: #16a34a; font-size: 1.2rem; }
"""


def _score_color(score: int) -> str:
    """Get color for a score value."""
    for threshold, color in _SCORE_COLOR_THRESHOLDS:
        if score >= threshold:
            return color
    return "#991b1b"


def _rec_color(rec: str) -> str:
    """Get background color for recommendation."""
    return {
        "PASS": "#16a34a",
        "CAUTION": "#ca8a04",
        "REVIEW": "#ea580c",
        "BLOCK": "#dc2626",
    }.get(rec, "#6b7280")


def to_html(report: ScanReport) -> str:
    """Generate a self-contained HTML scan report."""
    esc = html.escape
    score_clr = _score_color(report.score.score)
    rec_clr = _rec_color(report.score.recommendation)

    parts = [
        "<!DOCTYPE html>",
        '<html lang="en"><head>',
        '<meta charset="utf-8">',
        f"<title>ClawGuard: {esc(report.skill.name)}</title>",
        f"<style>{_CSS}</style>",
        "</head><body>",
        f"<h1>ClawGuard Scan: {esc(report.skill.name)}</h1>",
        '<div class="score-box">',
        f'<div class="score-num" style="color:{score_clr}">'
        f"{report.score.score}/100</div>",
        f'<div class="grade">Grade: {report.score.grade}</div>',
        f'<div class="rec" style="background:{rec_clr}">'
        f"{report.score.recommendation}</div>",
        "</div>",
        f'<p class="summary">{esc(report.score.summary)}</p>',
    ]

    if report.findings:
        parts.append("<h2>Findings</h2>")
        for f in sorted(
            report.findings,
            key=lambda x: list(Severity).index(x.severity),
        ):
            clr = _SEVERITY_COLORS.get(f.severity, "#6b7280")
            parts.append(
                f'<div class="finding" style="border-color:{clr}">'
            )
            parts.append(
                f'<div class="finding-title" style="color:{clr}">'
                f"[{f.severity.value.upper()}] {esc(f.title)}</div>"
            )
            if f.file:
                loc = f"File: {esc(f.file)}"
                if f.line:
                    loc += f", Line: {f.line}"
                parts.append(f'<div class="finding-meta">{loc}</div>')
            if f.detail:
                parts.append(
                    f'<div class="finding-detail">{esc(f.detail)}</div>'
                )
            if f.recommendation:
                parts.append(
                    f'<div class="finding-meta">'
                    f"Rec: {esc(f.recommendation)}</div>"
                )
            parts.append("</div>")
    else:
        parts.append('<p class="no-issues">No issues found.</p>')

    parts.append("</body></html>")
    return "\n".join(parts)
