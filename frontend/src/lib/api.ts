/**
 * Typed API client for the ClawGuard backend.
 */

const API_BASE = "/api";

// ── Types ──────────────────────────────────────────────────────────────────

export interface Finding {
  analyzer: string;
  category: string;
  severity: string;
  title: string;
  detail: string;
  file: string | null;
  line: number | null;
  evidence: string | null;
  cwe: string | null;
  recommendation: string;
}

export interface Score {
  score: number;
  grade: string;
  summary: string;
  top_risks: string[];
  recommendation: string;
}

export interface Skill {
  name: string;
  description: string;
  path: string;
}

export interface ScanResult {
  scan_id: string;
  skill: Skill;
  score: Score;
  findings: Finding[];
  analyzers_run: string[];
  scan_duration_ms: number;
  scanned_at: string;
}

export interface ScanSubmitResponse {
  scan_id: string;
  status: string;
  result: ScanResult | null;
}

export interface ScanSummary {
  scan_id: string;
  skill_name: string;
  trust_score: number;
  grade: string;
  recommendation: string;
  findings_count: number;
  scanned_at: string;
}

export interface HealthResponse {
  status: string;
  version: string;
}

// ── Error ──────────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(`API Error ${status}: ${detail}`);
    this.name = "ApiError";
  }
}

// ── Fetch wrapper ──────────────────────────────────────────────────────────

async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      body.detail?.detail || body.detail || "Unknown error",
    );
  }

  return response.json();
}

// ── API methods ────────────────────────────────────────────────────────────

export async function getHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/health");
}

export async function submitScanUrl(
  url: string,
): Promise<ScanSubmitResponse> {
  return apiFetch<ScanSubmitResponse>("/scan", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export async function submitScanPath(
  path: string,
): Promise<ScanSubmitResponse> {
  return apiFetch<ScanSubmitResponse>("/scan", {
    method: "POST",
    body: JSON.stringify({ path }),
  });
}

export async function uploadScanZip(
  file: File,
): Promise<ScanSubmitResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/scan/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      body.detail?.detail || body.detail || "Upload failed",
    );
  }

  return response.json();
}

export async function getScan(scanId: string): Promise<ScanResult> {
  return apiFetch<ScanResult>(`/scan/${scanId}`);
}

export async function listScans(
  limit = 20,
  offset = 0,
): Promise<ScanSummary[]> {
  return apiFetch<ScanSummary[]>(`/scans?limit=${limit}&offset=${offset}`);
}
