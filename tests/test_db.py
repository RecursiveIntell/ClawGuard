"""Tests for the database repository (mocked asyncpg)."""

import json
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from clawguard.analyzers.base import Category, Finding, Severity, SkillPackage
from clawguard.db.repository import ScanRepository, ScanSummary
from clawguard.reports.models import ScanReport
from clawguard.scoring.engine import TrustScore


def _make_report():
    skill = SkillPackage(
        name="test-skill",
        description="A test skill",
        path="/tmp/test",
        skill_md_raw="---\nname: test-skill\n---\n# Test",
        frontmatter={"name": "test-skill"},
        instructions="# Test",
    )
    score = TrustScore(
        score=75,
        grade="B",
        summary="1 high finding",
        top_risks=["High risk item"],
        recommendation="CAUTION",
    )
    findings = [
        Finding(
            analyzer="static",
            category=Category.CREDENTIAL_EXPOSURE,
            severity=Severity.HIGH,
            title="API key detected",
            detail="Found hardcoded API key",
        ),
    ]
    return ScanReport(
        skill=skill,
        findings=findings,
        score=score,
        analyzers_run=["static"],
        scan_duration_ms=42,
        scanned_at=datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
    )


def _make_mock_pool(mock_conn):
    """Create a mock asyncpg pool with proper async context manager."""
    mock_pool = AsyncMock()

    @asynccontextmanager
    async def acquire():
        yield mock_conn

    mock_pool.acquire = acquire
    return mock_pool


class TestScanRepository:
    @pytest.mark.asyncio
    async def test_save_scan(self):
        mock_conn = AsyncMock()
        mock_pool = _make_mock_pool(mock_conn)

        repo = ScanRepository(mock_pool)
        report = _make_report()
        scan_id = await repo.save_scan(report, skill_source="local")

        assert isinstance(scan_id, uuid.UUID)
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args[0]
        assert "INSERT INTO scans" in call_args[0]
        assert call_args[2] == "test-skill"  # skill_name
        assert call_args[3] == "local"  # skill_source
        assert call_args[4] == 75  # trust_score
        assert call_args[5] == "B"  # grade

    @pytest.mark.asyncio
    async def test_get_scan_found(self):
        report_dict = {
            "skill": {"name": "test-skill", "description": "", "path": "/tmp"},
            "score": {"score": 75, "grade": "B"},
            "findings": [],
        }
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = {
            "report_json": json.dumps(report_dict),
            "created_at": datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC),
        }
        mock_pool = _make_mock_pool(mock_conn)

        repo = ScanRepository(mock_pool)
        scan_id = uuid.uuid4()
        result = await repo.get_scan(scan_id)

        assert result is not None
        assert result["scan_id"] == str(scan_id)
        assert result["skill"]["name"] == "test-skill"

    @pytest.mark.asyncio
    async def test_get_scan_not_found(self):
        mock_conn = AsyncMock()
        mock_conn.fetchrow.return_value = None
        mock_pool = _make_mock_pool(mock_conn)

        repo = ScanRepository(mock_pool)
        result = await repo.get_scan(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_list_scans(self):
        mock_rows = [
            {
                "id": uuid.uuid4(),
                "skill_name": "skill-a",
                "skill_source": "local",
                "trust_score": 90,
                "grade": "A",
                "recommendation": "PASS",
                "findings_count": 0,
                "critical_count": 0,
                "high_count": 0,
                "created_at": datetime(2025, 1, 15, tzinfo=UTC),
            },
            {
                "id": uuid.uuid4(),
                "skill_name": "skill-b",
                "skill_source": "https://clawhub.com/skills/a/b",
                "trust_score": 30,
                "grade": "D",
                "recommendation": "REVIEW",
                "findings_count": 5,
                "critical_count": 1,
                "high_count": 2,
                "created_at": datetime(2025, 1, 14, tzinfo=UTC),
            },
        ]
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = mock_rows
        mock_pool = _make_mock_pool(mock_conn)

        repo = ScanRepository(mock_pool)
        summaries = await repo.list_scans(limit=10, offset=0)

        assert len(summaries) == 2
        assert isinstance(summaries[0], ScanSummary)
        assert summaries[0].skill_name == "skill-a"
        assert summaries[1].trust_score == 30

    @pytest.mark.asyncio
    async def test_close(self):
        mock_pool = AsyncMock()
        repo = ScanRepository(mock_pool)
        await repo.close()
        mock_pool.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_scan_counts_severities(self):
        """Verify critical and high counts are computed correctly."""
        report = _make_report()
        report.findings.append(
            Finding(
                analyzer="static",
                category=Category.MALWARE,
                severity=Severity.CRITICAL,
                title="Malware detected",
                detail="Bad stuff",
            )
        )

        mock_conn = AsyncMock()
        mock_pool = _make_mock_pool(mock_conn)

        repo = ScanRepository(mock_pool)
        await repo.save_scan(report)

        call_args = mock_conn.execute.call_args[0]
        assert call_args[7] == 2  # findings_count
        assert call_args[8] == 1  # critical_count
        assert call_args[9] == 1  # high_count
