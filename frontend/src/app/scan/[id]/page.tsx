"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import type { ScanResult } from "@/lib/api";
import { getScan } from "@/lib/api";
import ScanResultView from "@/components/scan-result";

export default function ScanResultPage() {
  const params = useParams<{ id: string }>();
  const [result, setResult] = useState<ScanResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.id) return;
    getScan(params.id)
      .then(setResult)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <div className="flex items-center gap-3 py-12 text-slate-400">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-600 border-t-emerald-400" />
        Loading scan results...
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-red-800 bg-red-900/30 px-4 py-3 text-red-300">
        {error}
      </div>
    );
  }

  if (!result) {
    return <p className="text-slate-500">Scan not found.</p>;
  }

  return <ScanResultView result={result} showExport />;
}
