"""Serialize ScanReport to JSON."""

import json
from datetime import datetime
from enum import Enum

from clawguard.reports.models import ScanReport


def _default_serializer(obj: object) -> object:
    """Handle non-serializable types."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def report_to_dict(report: ScanReport) -> dict:
    """Convert a ScanReport to a plain dict for serialization."""
    return {
        "skill": {
            "name": report.skill.name,
            "description": report.skill.description,
            "path": report.skill.path,
        },
        "score": {
            "score": report.score.score,
            "grade": report.score.grade,
            "summary": report.score.summary,
            "top_risks": report.score.top_risks,
            "recommendation": report.score.recommendation,
        },
        "findings": [
            {
                "analyzer": f.analyzer,
                "category": f.category.value,
                "severity": f.severity.value,
                "title": f.title,
                "detail": f.detail,
                "file": f.file,
                "line": f.line,
                "evidence": f.evidence,
                "cwe": f.cwe,
                "recommendation": f.recommendation,
            }
            for f in report.findings
        ],
        "analyzers_run": report.analyzers_run,
        "scan_duration_ms": report.scan_duration_ms,
        "scanned_at": report.scanned_at.isoformat(),
    }


def to_json(report: ScanReport, indent: int = 2) -> str:
    """Serialize a ScanReport to a JSON string."""
    return json.dumps(
        report_to_dict(report),
        indent=indent,
        default=_default_serializer,
    )
