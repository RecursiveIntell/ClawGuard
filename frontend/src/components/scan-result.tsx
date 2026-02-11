"use client";

import { useState } from "react";
import type { ScanResult, Finding } from "@/lib/api";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "text-red-400 bg-red-900/30 border-red-800",
  high: "text-orange-400 bg-orange-900/30 border-orange-800",
  medium: "text-yellow-400 bg-yellow-900/30 border-yellow-800",
  low: "text-blue-400 bg-blue-900/30 border-blue-800",
  info: "text-slate-400 bg-slate-800/50 border-slate-700",
};

const SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"];

const GRADE_COLORS: Record<string, string> = {
  A: "text-emerald-400",
  B: "text-green-400",
  C: "text-yellow-400",
  D: "text-orange-400",
  F: "text-red-400",
};

const SCORE_RING_COLORS: Record<string, string> = {
  A: "stroke-emerald-400",
  B: "stroke-green-400",
  C: "stroke-yellow-400",
  D: "stroke-orange-400",
  F: "stroke-red-400",
};

const REC_COLORS: Record<string, string> = {
  PASS: "bg-emerald-900/30 text-emerald-400 border-emerald-800",
  CAUTION: "bg-yellow-900/30 text-yellow-400 border-yellow-800",
  REVIEW: "bg-orange-900/30 text-orange-400 border-orange-800",
  BLOCK: "bg-red-900/30 text-red-400 border-red-800",
};

function ScoreCircle({ score, grade }: { score: number; grade: string }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;
  const ringColor = SCORE_RING_COLORS[grade] ?? "stroke-slate-400";
  const gradeColor = GRADE_COLORS[grade] ?? "text-slate-400";

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="140" height="140" className="-rotate-90">
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          className="text-slate-800"
        />
        <circle
          cx="70"
          cy="70"
          r={radius}
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          className={`transition-all duration-700 ${ringColor}`}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-3xl font-bold text-slate-100">{score}</span>
        <span className={`text-lg font-bold ${gradeColor}`}>{grade}</span>
      </div>
    </div>
  );
}

function FindingCard({ finding }: { finding: Finding }) {
  const [expanded, setExpanded] = useState(false);
  const colors = SEVERITY_COLORS[finding.severity] ?? SEVERITY_COLORS.info;

  return (
    <div className={`rounded-md border ${colors}`}>
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-start justify-between gap-2 p-3 text-left"
      >
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase">
              {finding.severity}
            </span>
            <span className="shrink-0 rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
              {finding.category}
            </span>
          </div>
          <h4 className="mt-0.5 font-medium text-slate-100">{finding.title}</h4>
        </div>
        <span className="mt-1 shrink-0 text-slate-500">
          {expanded ? "\u25B2" : "\u25BC"}
        </span>
      </button>

      {expanded && (
        <div className="border-t border-slate-700/50 px-3 pb-3 pt-2">
          {finding.detail && (
            <p className="text-sm text-slate-300">{finding.detail}</p>
          )}
          {finding.evidence && (
            <div className="mt-2">
              <span className="text-xs font-semibold text-slate-500">Evidence:</span>
              <pre className="mt-1 overflow-x-auto rounded bg-slate-900 p-2 text-xs text-slate-400">
                {finding.evidence}
              </pre>
            </div>
          )}
          <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-500">
            {finding.file && <span>File: {finding.file}</span>}
            {finding.line && <span>Line: {finding.line}</span>}
            {finding.analyzer && <span>Analyzer: {finding.analyzer}</span>}
            {finding.cwe && <span>CWE: {finding.cwe}</span>}
          </div>
          {finding.recommendation && (
            <p className="mt-2 text-xs text-slate-400">
              Recommendation: {finding.recommendation}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function groupBySeverity(findings: Finding[]): Record<string, Finding[]> {
  const groups: Record<string, Finding[]> = {};
  for (const f of findings) {
    if (!groups[f.severity]) groups[f.severity] = [];
    groups[f.severity].push(f);
  }
  return groups;
}

function exportJson(result: ScanResult) {
  const blob = new Blob([JSON.stringify(result, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `clawguard-${result.skill.name}-report.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function exportMarkdown(result: ScanResult) {
  const lines = [
    `# ClawGuard Scan Report: ${result.skill.name}`,
    "",
    `**Trust Score**: ${result.score.score}/100 (${result.score.grade}) - ${result.score.recommendation}`,
    `**Scanned**: ${new Date(result.scanned_at).toLocaleString()}`,
    `**Analyzers**: ${result.analyzers_run.join(", ")}`,
    `**Duration**: ${result.scan_duration_ms}ms`,
    "",
    "## Summary",
    "",
    result.score.summary,
    "",
  ];

  if (result.score.top_risks.length > 0) {
    lines.push("## Top Risks", "");
    result.score.top_risks.forEach((r, i) => lines.push(`${i + 1}. ${r}`));
    lines.push("");
  }

  lines.push("## Findings", "");
  if (result.findings.length === 0) {
    lines.push("No issues found.");
  } else {
    for (const f of result.findings) {
      lines.push(`### ${f.severity.toUpperCase()}: ${f.title}`);
      if (f.file) lines.push(`- File: ${f.file}${f.line ? `, Line: ${f.line}` : ""}`);
      if (f.detail) lines.push(`- ${f.detail}`);
      if (f.recommendation) lines.push(`- Recommendation: ${f.recommendation}`);
      lines.push("");
    }
  }

  const blob = new Blob([lines.join("\n")], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `clawguard-${result.skill.name}-report.md`;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ScanResultView({
  result,
  showExport = false,
}: {
  result: ScanResult;
  showExport?: boolean;
}) {
  const recColors = REC_COLORS[result.score.recommendation] ?? "";
  const grouped = groupBySeverity(result.findings);

  return (
    <div className="space-y-6">
      {/* Header with score circle */}
      <div className="rounded-lg border border-slate-800 bg-slate-800/50 p-6">
        <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex-1">
            <h2 className="text-xl font-bold text-slate-100">
              {result.skill.name}
            </h2>
            <p className="text-sm text-slate-400">
              Scanned in {result.scan_duration_ms}ms &middot;{" "}
              {new Date(result.scanned_at).toLocaleString()}
            </p>

            <div className="mt-4 flex flex-wrap gap-2">
              <span
                className={`rounded-md border px-3 py-1 text-sm font-medium ${recColors}`}
              >
                {result.score.recommendation}
              </span>
              {result.analyzers_run.map((a) => (
                <span
                  key={a}
                  className="rounded-md bg-slate-700 px-2 py-1 text-xs text-slate-300"
                >
                  {a}
                </span>
              ))}
            </div>

            {result.score.top_risks.length > 0 && (
              <div className="mt-4">
                <h3 className="text-sm font-semibold text-slate-400">Top Risks</h3>
                <ul className="mt-1 list-inside list-disc text-sm text-slate-300">
                  {result.score.top_risks.map((risk, i) => (
                    <li key={i}>{risk}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <ScoreCircle score={result.score.score} grade={result.score.grade} />
        </div>
      </div>

      {/* Export buttons */}
      {showExport && (
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => exportJson(result)}
            className="rounded-md bg-slate-800 px-4 py-2 text-sm text-slate-300 transition-colors hover:bg-slate-700"
          >
            Export JSON
          </button>
          <button
            type="button"
            onClick={() => exportMarkdown(result)}
            className="rounded-md bg-slate-800 px-4 py-2 text-sm text-slate-300 transition-colors hover:bg-slate-700"
          >
            Export Markdown
          </button>
        </div>
      )}

      {/* Findings grouped by severity */}
      <div>
        <h3 className="mb-3 text-lg font-semibold text-slate-200">
          Findings ({result.findings.length})
        </h3>
        {result.findings.length === 0 ? (
          <p className="text-slate-400">No issues found.</p>
        ) : (
          <div className="space-y-4">
            {SEVERITY_ORDER.filter((s) => grouped[s]?.length).map((severity) => (
              <div key={severity}>
                <h4 className="mb-2 text-sm font-semibold uppercase text-slate-500">
                  {severity} ({grouped[severity].length})
                </h4>
                <div className="space-y-2">
                  {grouped[severity].map((f, i) => (
                    <FindingCard key={i} finding={f} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
