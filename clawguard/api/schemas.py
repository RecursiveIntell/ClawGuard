"""Pydantic request/response schemas for the ClawGuard API."""


from pydantic import BaseModel


class ScanRequest(BaseModel):
    """Request body for POST /api/scan."""

    url: str | None = None
    path: str | None = None


class FindingResponse(BaseModel):
    analyzer: str
    category: str
    severity: str
    title: str
    detail: str
    file: str | None = None
    line: int | None = None
    evidence: str | None = None
    cwe: str | None = None
    recommendation: str = ""


class ScoreResponse(BaseModel):
    score: int
    grade: str
    summary: str
    top_risks: list[str]
    recommendation: str


class SkillResponse(BaseModel):
    name: str
    description: str
    path: str


class ScanResponse(BaseModel):
    """Full scan result returned by GET /api/scan/{id}."""

    scan_id: str
    skill: SkillResponse
    score: ScoreResponse
    findings: list[FindingResponse]
    analyzers_run: list[str]
    scan_duration_ms: int
    scanned_at: str


class ScanSummaryResponse(BaseModel):
    """Summary for list view."""

    scan_id: str
    skill_name: str
    trust_score: int
    grade: str
    recommendation: str
    findings_count: int
    scanned_at: str


class ScanSubmittedResponse(BaseModel):
    """Response for POST /api/scan."""

    scan_id: str
    status: str = "completed"
    result: ScanResponse | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


class ErrorResponse(BaseModel):
    error: str
    detail: str = ""
