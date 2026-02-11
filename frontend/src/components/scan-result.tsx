import type { ScanResult, Finding } from "@/lib/api";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "text-red-400 bg-red-900/30 border-red-800",
  high: "text-orange-400 bg-orange-900/30 border-orange-800",
  medium: "text-yellow-400 bg-yellow-900/30 border-yellow-800",
  low: "text-blue-400 bg-blue-900/30 border-blue-800",
  info: "text-slate-400 bg-slate-800/50 border-slate-700",
};

const GRADE_COLORS: Record<string, string> = {
  A: "text-emerald-400",
  B: "text-green-400",
  C: "text-yellow-400",
  D: "text-orange-400",
  F: "text-red-400",
};

const REC_COLORS: Record<string, string> = {
  PASS: "bg-emerald-900/30 text-emerald-400 border-emerald-800",
  CAUTION: "bg-yellow-900/30 text-yellow-400 border-yellow-800",
  REVIEW: "bg-orange-900/30 text-orange-400 border-orange-800",
  BLOCK: "bg-red-900/30 text-red-400 border-red-800",
};

function ScoreBadge({ score, grade }: { score: number; grade: string }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="text-4xl font-bold text-slate-100">{score}</span>
      <span className="text-lg text-slate-500">/100</span>
      <span className={`ml-2 text-2xl font-bold ${GRADE_COLORS[grade] ?? "text-slate-400"}`}>
        {grade}
      </span>
    </div>
  );
}

function FindingCard({ finding }: { finding: Finding }) {
  const colors = SEVERITY_COLORS[finding.severity] ?? SEVERITY_COLORS.info;
  return (
    <div className={`rounded-md border p-3 ${colors}`}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <span className="text-xs font-semibold uppercase">
            {finding.severity}
          </span>
          <h4 className="mt-0.5 font-medium text-slate-100">{finding.title}</h4>
        </div>
        <span className="shrink-0 rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-400">
          {finding.category}
        </span>
      </div>
      {finding.detail && (
        <p className="mt-2 text-sm text-slate-300">{finding.detail}</p>
      )}
      <div className="mt-2 flex flex-wrap gap-3 text-xs text-slate-500">
        {finding.file && <span>File: {finding.file}</span>}
        {finding.line && <span>Line: {finding.line}</span>}
        {finding.analyzer && <span>Analyzer: {finding.analyzer}</span>}
      </div>
      {finding.recommendation && (
        <p className="mt-2 text-xs text-slate-400">
          Recommendation: {finding.recommendation}
        </p>
      )}
    </div>
  );
}

export default function ScanResultView({ result }: { result: ScanResult }) {
  const recColors = REC_COLORS[result.score.recommendation] ?? "";

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-slate-800 bg-slate-800/50 p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-bold text-slate-100">
              {result.skill.name}
            </h2>
            <p className="text-sm text-slate-400">
              Scanned in {result.scan_duration_ms}ms &middot;{" "}
              {new Date(result.scanned_at).toLocaleString()}
            </p>
          </div>
          <ScoreBadge score={result.score.score} grade={result.score.grade} />
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <span className={`rounded-md border px-3 py-1 text-sm font-medium ${recColors}`}>
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

      <div>
        <h3 className="mb-3 text-lg font-semibold text-slate-200">
          Findings ({result.findings.length})
        </h3>
        {result.findings.length === 0 ? (
          <p className="text-slate-400">No issues found.</p>
        ) : (
          <div className="space-y-3">
            {result.findings.map((f, i) => (
              <FindingCard key={i} finding={f} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
