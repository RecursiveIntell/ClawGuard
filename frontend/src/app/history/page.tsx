"use client";

import { useEffect, useState, useMemo, useCallback } from "react";
import { useRouter } from "next/navigation";
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

type SortField = "date" | "score" | "name";
type SortDirection = "asc" | "desc";

const PAGE_SIZE = 20;

export default function HistoryPage() {
  const router = useRouter();
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>("date");
  const [sortDir, setSortDir] = useState<SortDirection>("desc");
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const loadScans = useCallback((offset: number) => {
    setLoading(true);
    listScans(PAGE_SIZE, offset)
      .then((data) => {
        setScans((prev) => (offset === 0 ? data : [...prev, ...data]));
        setHasMore(data.length === PAGE_SIZE);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadScans(0);
  }, [loadScans]);

  const sortedScans = useMemo(() => {
    const sorted = [...scans];
    sorted.sort((a, b) => {
      let cmp = 0;
      if (sortField === "date") {
        cmp = new Date(a.scanned_at).getTime() - new Date(b.scanned_at).getTime();
      } else if (sortField === "score") {
        cmp = a.trust_score - b.trust_score;
      } else {
        cmp = a.skill_name.localeCompare(b.skill_name);
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
    return sorted;
  }, [scans, sortField, sortDir]);

  function handleSort(field: SortField) {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  }

  function sortIndicator(field: SortField) {
    if (sortField !== field) return "";
    return sortDir === "asc" ? " \u25B2" : " \u25BC";
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Scan History</h1>
        <p className="mt-1 text-sm text-slate-400">
          Previously scanned skills and their trust scores.
        </p>
      </div>

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
                <th
                  className="cursor-pointer px-4 py-3 font-medium text-slate-400 hover:text-slate-200"
                  onClick={() => handleSort("name")}
                >
                  Skill{sortIndicator("name")}
                </th>
                <th
                  className="cursor-pointer px-4 py-3 font-medium text-slate-400 hover:text-slate-200"
                  onClick={() => handleSort("score")}
                >
                  Score{sortIndicator("score")}
                </th>
                <th className="px-4 py-3 font-medium text-slate-400">Grade</th>
                <th className="px-4 py-3 font-medium text-slate-400">Status</th>
                <th className="px-4 py-3 font-medium text-slate-400">Findings</th>
                <th
                  className="cursor-pointer px-4 py-3 font-medium text-slate-400 hover:text-slate-200"
                  onClick={() => handleSort("date")}
                >
                  Scanned{sortIndicator("date")}
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {sortedScans.map((scan) => (
                <tr
                  key={scan.scan_id}
                  onClick={() => router.push(`/scan/${scan.scan_id}`)}
                  className="cursor-pointer hover:bg-slate-800/30"
                >
                  <td className="px-4 py-3 font-medium text-slate-100">
                    {scan.skill_name}
                  </td>
                  <td className="px-4 py-3 text-slate-300">
                    {scan.trust_score}/100
                  </td>
                  <td
                    className={`px-4 py-3 font-bold ${GRADE_COLORS[scan.grade] ?? ""}`}
                  >
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

      {/* Pagination */}
      {hasMore && !loading && scans.length > 0 && (
        <div className="flex justify-center">
          <button
            type="button"
            onClick={() => {
              const nextPage = page + 1;
              setPage(nextPage);
              loadScans(nextPage * PAGE_SIZE);
            }}
            className="rounded-md bg-slate-800 px-4 py-2 text-sm text-slate-300 transition-colors hover:bg-slate-700"
          >
            Load More
          </button>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center gap-3 py-4 text-slate-400">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-600 border-t-emerald-400" />
          {scans.length > 0 ? "Loading more..." : "Loading scan history..."}
        </div>
      )}
    </div>
  );
}
