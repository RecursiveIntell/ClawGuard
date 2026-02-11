"""Database repository for scan results using asyncpg."""

import json
import uuid
from dataclasses import dataclass
from datetime import datetime

import asyncpg
import structlog

from clawguard.analyzers.base import Severity
from clawguard.config import settings
from clawguard.reports.json_report import report_to_dict
from clawguard.reports.models import ScanReport

logger = structlog.get_logger()


@dataclass
class ScanSummary:
    """Lightweight scan record for list views."""

    id: uuid.UUID
    skill_name: str
    skill_source: str | None
    trust_score: int
    grade: str
    recommendation: str
    findings_count: int
    critical_count: int
    high_count: int
    created_at: datetime


class ScanRepository:
    """Async PostgreSQL repository for scan data."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @classmethod
    async def create(cls, database_url: str | None = None) -> "ScanRepository":
        """Create a repository with a connection pool."""
        url = database_url or settings.DATABASE_URL
        pool = await asyncpg.create_pool(url)
        return cls(pool)

    async def initialize(self) -> None:
        """Create tables if they don't exist."""
        from pathlib import Path

        schema_path = Path(__file__).parent / "schema.sql"
        schema_sql = schema_path.read_text(encoding="utf-8")
        async with self._pool.acquire() as conn:
            await conn.execute(schema_sql)
        logger.info("database_initialized")

    async def save_scan(
        self,
        report: ScanReport,
        skill_source: str | None = None,
    ) -> uuid.UUID:
        """Save a scan report to the database. Returns the scan UUID."""
        scan_id = uuid.uuid4()
        report_dict = report_to_dict(report)

        critical_count = sum(
            1 for f in report.findings if f.severity == Severity.CRITICAL
        )
        high_count = sum(
            1 for f in report.findings if f.severity == Severity.HIGH
        )

        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO scans (
                    id, skill_name, skill_source, trust_score, grade,
                    recommendation, findings_count, critical_count,
                    high_count, report_json
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                scan_id,
                report.skill.name,
                skill_source,
                report.score.score,
                report.score.grade,
                report.score.recommendation,
                len(report.findings),
                critical_count,
                high_count,
                json.dumps(report_dict),
            )

        logger.info("scan_saved", scan_id=str(scan_id), skill=report.skill.name)
        return scan_id

    async def get_scan(self, scan_id: uuid.UUID) -> dict | None:
        """Get a full scan report by ID. Returns the report JSON dict or None."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT report_json, created_at FROM scans WHERE id = $1",
                scan_id,
            )
        if not row:
            return None
        report_dict = json.loads(row["report_json"])
        report_dict["scan_id"] = str(scan_id)
        report_dict["created_at"] = row["created_at"].isoformat()
        return report_dict

    async def list_scans(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ScanSummary]:
        """List scan summaries, newest first."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, skill_name, skill_source, trust_score, grade,
                       recommendation, findings_count, critical_count,
                       high_count, created_at
                FROM scans
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )
        return [
            ScanSummary(
                id=row["id"],
                skill_name=row["skill_name"],
                skill_source=row["skill_source"],
                trust_score=row["trust_score"],
                grade=row["grade"],
                recommendation=row["recommendation"],
                findings_count=row["findings_count"],
                critical_count=row["critical_count"],
                high_count=row["high_count"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def close(self) -> None:
        """Close the connection pool."""
        await self._pool.close()
