"""Bulk scanning of ClawHub registry skills."""

from collections.abc import Callable
from dataclasses import dataclass

import httpx
import structlog

from clawguard.clawhub.client import CLAWHUB_BASE_URL, SkillInfo
from clawguard.exceptions import ClawHubError

logger = structlog.get_logger()


@dataclass
class BulkScanProgress:
    """Progress update for bulk scanning."""

    current: int
    total: int
    skill_name: str


def list_skills(
    limit: int = 100,
    base_url: str = CLAWHUB_BASE_URL,
) -> list[SkillInfo]:
    """List skills from the ClawHub registry."""
    url = f"{base_url.rstrip('/')}/api/skills?limit={limit}"

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise ClawHubError(
            f"ClawHub API error: {e.response.status_code}"
        ) from e
    except httpx.RequestError as e:
        raise ClawHubError(f"Network error: {e}") from e

    data = response.json()
    skills = []
    for item in data.get("skills", []):
        skills.append(
            SkillInfo(
                name=item.get("name", ""),
                author=item.get("author", ""),
                url=item.get("url", ""),
                description=item.get("description", ""),
                downloads=item.get("downloads", 0),
            )
        )
    return skills


def bulk_scan(
    limit: int = 100,
    base_url: str = CLAWHUB_BASE_URL,
    progress_callback: Callable[[BulkScanProgress], None] | None = None,
) -> list[dict]:
    """Scan top N skills from ClawHub. Returns list of result dicts.

    Each result dict has: name, url, score, grade, recommendation, error.
    Full ScanReport generation requires the pipeline (circular import),
    so this returns summary dicts instead.
    """
    from clawguard.clawhub.client import ClawHubClient
    from clawguard.pipeline import ScanOptions, ScanPipeline

    skills = list_skills(limit=limit, base_url=base_url)
    pipeline = ScanPipeline(options=ScanOptions(skip_llm=True))
    client = ClawHubClient(base_url=base_url)

    results = []
    try:
        for i, skill_info in enumerate(skills):
            if progress_callback:
                progress_callback(
                    BulkScanProgress(
                        current=i + 1,
                        total=len(skills),
                        skill_name=skill_info.name,
                    )
                )

            try:
                local_path = client.download(skill_info.url)
                report = pipeline.scan(local_path)
                results.append({
                    "name": skill_info.name,
                    "url": skill_info.url,
                    "score": report.score.score,
                    "grade": report.score.grade,
                    "recommendation": report.score.recommendation,
                    "error": None,
                })
            except Exception as e:
                logger.error(
                    "bulk_scan_skill_failed",
                    skill=skill_info.name,
                    error=str(e),
                )
                results.append({
                    "name": skill_info.name,
                    "url": skill_info.url,
                    "score": None,
                    "grade": None,
                    "recommendation": None,
                    "error": str(e),
                })
    finally:
        client.cleanup()

    return results
