"""FastAPI application for ClawGuard."""

import uuid

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import clawguard
from clawguard.api.schemas import (
    ErrorResponse,
    FindingResponse,
    HealthResponse,
    ScanRequest,
    ScanResponse,
    ScanSubmittedResponse,
    ScanSummaryResponse,
    ScoreResponse,
    SkillResponse,
)
from clawguard.clawhub.client import ClawHubClient
from clawguard.pipeline import ScanOptions, ScanPipeline
from clawguard.reports.models import ScanReport

app = FastAPI(
    title="ClawGuard API",
    description="Security scanner for AI agent skills",
    version=clawguard.__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory scan storage (MVP — replaced by DB in T12)
_scan_store: dict[str, ScanReport] = {}
_scan_ids: list[str] = []  # Ordered list for pagination


def _report_to_response(scan_id: str, report: ScanReport) -> ScanResponse:
    """Convert a ScanReport to a ScanResponse."""
    return ScanResponse(
        scan_id=scan_id,
        skill=SkillResponse(
            name=report.skill.name,
            description=report.skill.description,
            path=report.skill.path,
        ),
        score=ScoreResponse(
            score=report.score.score,
            grade=report.score.grade,
            summary=report.score.summary,
            top_risks=report.score.top_risks,
            recommendation=report.score.recommendation,
        ),
        findings=[
            FindingResponse(
                analyzer=f.analyzer,
                category=f.category.value,
                severity=f.severity.value,
                title=f.title,
                detail=f.detail,
                file=f.file,
                line=f.line,
                evidence=f.evidence,
                cwe=f.cwe,
                recommendation=f.recommendation,
            )
            for f in report.findings
        ],
        analyzers_run=report.analyzers_run,
        scan_duration_ms=report.scan_duration_ms,
        scanned_at=report.scanned_at.isoformat(),
    )


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=clawguard.__version__)


@app.post(
    "/api/scan",
    response_model=ScanSubmittedResponse,
    status_code=200,
    responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def submit_scan(request: ScanRequest) -> ScanSubmittedResponse:
    """Submit a skill for scanning via URL or local path."""
    if not request.url and not request.path:
        raise HTTPException(
            status_code=400,
            detail={"error": "Bad request", "detail": "Provide 'url' or 'path'."},
        )

    pipeline = ScanPipeline(options=ScanOptions(skip_llm=True))
    scan_id = str(uuid.uuid4())

    try:
        if request.url:
            client = ClawHubClient()
            try:
                local_path = client.download(request.url)
                report = pipeline.scan(local_path)
            finally:
                client.cleanup()
        else:
            report = pipeline.scan(request.path)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "Scan failed", "detail": str(e)},
        ) from e

    _scan_store[scan_id] = report
    _scan_ids.append(scan_id)

    return ScanSubmittedResponse(
        scan_id=scan_id,
        status="completed",
        result=_report_to_response(scan_id, report),
    )


@app.post(
    "/api/scan/upload",
    response_model=ScanSubmittedResponse,
    status_code=200,
    responses={400: {"model": ErrorResponse}},
)
async def upload_scan(file: UploadFile) -> ScanSubmittedResponse:
    """Scan an uploaded skill zip archive."""
    import tempfile
    import zipfile
    from io import BytesIO
    from pathlib import Path

    content = await file.read()
    try:
        zf = zipfile.ZipFile(BytesIO(content))
    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid file", "detail": "File is not a valid zip archive."},
        )

    temp_dir = Path(tempfile.mkdtemp(prefix="clawguard_upload_"))
    try:
        zf.extractall(temp_dir)
        zf.close()

        skill_md_files = list(temp_dir.rglob("SKILL.md"))
        if not skill_md_files:
            raise HTTPException(
                status_code=400,
                detail={"error": "Invalid skill", "detail": "Archive has no SKILL.md."},
            )

        pipeline = ScanPipeline(options=ScanOptions(skip_llm=True))
        scan_id = str(uuid.uuid4())
        report = pipeline.scan(skill_md_files[0].parent)

        _scan_store[scan_id] = report
        _scan_ids.append(scan_id)

        return ScanSubmittedResponse(
            scan_id=scan_id,
            status="completed",
            result=_report_to_response(scan_id, report),
        )
    finally:
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)


@app.get(
    "/api/scan/{scan_id}",
    response_model=ScanResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_scan(scan_id: str) -> ScanResponse:
    """Get scan results by ID."""
    report = _scan_store.get(scan_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail={"error": "Not found", "detail": f"Scan {scan_id} not found."},
        )
    return _report_to_response(scan_id, report)


@app.get("/api/scans", response_model=list[ScanSummaryResponse])
async def list_scans(
    limit: int = 20,
    offset: int = 0,
) -> list[ScanSummaryResponse]:
    """List scan history (paginated, newest first)."""
    ids = list(reversed(_scan_ids))[offset : offset + limit]
    results = []
    for sid in ids:
        report = _scan_store[sid]
        results.append(
            ScanSummaryResponse(
                scan_id=sid,
                skill_name=report.skill.name,
                trust_score=report.score.score,
                grade=report.score.grade,
                recommendation=report.score.recommendation,
                findings_count=len(report.findings),
                scanned_at=report.scanned_at.isoformat(),
            )
        )
    return results
