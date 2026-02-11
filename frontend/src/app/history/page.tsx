"use client";

import { useEffect, useState } from "react";
import type { ScanSummary } from "@/lib/api";
import { listScans } from "@/lib/api";

const GRADE_COLORS: Record<string, string> = {
  A: "text-emerald-400",
  B: "text-green-400",
  C: "text-yellow-400",
  D: "text-orange-400",
  F: "text-red-400",
};

const REC_BADGES: Record<string, string> = {
  PASS: "bg-emerald-900/30 text-emerald-400",
  CAUTION: "bg-yellow-900/30 text-yellow-400",
  REVIEW: "bg-orange-900/30 text-orange-400",
  BLOCK: "bg-red-900/30 text-red-400",
};

export default function HistoryPage() {
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listScans()
      .then(setScans)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Scan History</h1>
        <p className="mt-1 text-sm text-slate-400">
          Previously scanned skills and their trust scores.
        </p>
      </div>

      {loading && (
        <div className="flex items-center gap-3 text-slate-400">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-600 border-t-emerald-400" />
          Loading scan history...
        </div>
      )}

      {error && (
        <div className="rounded-md border border-red-800 bg-red-900/30 px-4 py-3 text-red-300">
          {error}
        </div>
      )}

      {!loading && !error && scans.length === 0 && (
        <p className="text-slate-500">No scans yet. Run a scan to get started.</p>
      )}

      {scans.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 bg-slate-800/50">
              <tr>
                <th className="px-4 py-3 font-medium text-slate-400">Skill</th>
                <th className="px-4 py-3 font-medium text-slate-400">Score</th>
                <th className="px-4 py-3 font-medium text-slate-400">Grade</th>
                <th className="px-4 py-3 font-medium text-slate-400">Status</th>
                <th className="px-4 py-3 font-medium text-slate-400">Findings</th>
                <th className="px-4 py-3 font-medium text-slate-400">Scanned</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {scans.map((scan) => (
                <tr key={scan.scan_id} className="hover:bg-slate-800/30">
                  <td className="px-4 py-3 font-medium text-slate-100">
                    {scan.skill_name}
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    {scan.trust_score}/100
                  </td>
                  <td className={`px-4 py-3 font-bold ${GRADE_COLORS[scan.grade] ?? ""}`}>
                    {scan.grade}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded px-2 py-0.5 text-xs font-medium ${
                        REC_BADGES[scan.recommendation] ?? ""
                      }`}
                    >
                      {scan.recommendation}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-400">
                    {scan.findings_count}
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {new Date(scan.scanned_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
