"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { submitScanUrl, submitScanPath, uploadScanZip } from "@/lib/api";

type ScanMode = "url" | "path" | "upload";

export default function ScanPage() {
  const router = useRouter();
  const [mode, setMode] = useState<ScanMode>("url");
  const [input, setInput] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      let response;
      if (mode === "url") {
        response = await submitScanUrl(input);
      } else if (mode === "path") {
        response = await submitScanPath(input);
      } else if (file) {
        response = await uploadScanZip(file);
      } else {
        setError("Please select a file to upload.");
        setLoading(false);
        return;
      }
      router.push(`/scan/${response.scan_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scan failed");
      setLoading(false);
    }
  }

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) {
        setFile(droppedFile);
        setMode("upload");
      }
    },
    [],
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragging(false);
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Scan a Skill</h1>
        <p className="mt-1 text-sm text-slate-400">
          Analyze an AI agent skill for security issues.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex gap-2">
          {(["url", "path", "upload"] as ScanMode[]).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                mode === m
                  ? "bg-emerald-600 text-white"
                  : "bg-slate-800 text-slate-400 hover:text-slate-200"
              }`}
            >
              {m === "url" ? "ClawHub URL" : m === "path" ? "Local Path" : "Upload ZIP"}
            </button>
          ))}
        </div>

        {mode !== "upload" ? (
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              mode === "url"
                ? "https://clawhub.com/skills/author/name"
                : "/path/to/skill/directory"
            }
            className="w-full rounded-md border border-slate-700 bg-slate-800 px-4 py-2 text-slate-100 placeholder-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
        ) : (
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors ${
              dragging
                ? "border-emerald-400 bg-emerald-900/10"
                : "border-slate-700 bg-slate-800/50"
            }`}
          >
            <p className="mb-2 text-sm text-slate-400">
              {file ? file.name : "Drag & drop a ZIP file here, or click to browse"}
            </p>
            <input
              type="file"
              accept=".zip"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="text-sm text-slate-500 file:mr-4 file:rounded file:border-0 file:bg-emerald-600 file:px-3 file:py-1 file:text-sm file:text-white file:cursor-pointer"
            />
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-emerald-600 px-6 py-2 font-medium text-white transition-colors hover:bg-emerald-500 disabled:opacity-50"
        >
          {loading ? "Scanning..." : "Scan"}
        </button>
      </form>

      {error && (
        <div className="rounded-md border border-red-800 bg-red-900/30 px-4 py-3 text-red-300">
          {error}
        </div>
      )}

      {loading && (
        <div className="flex items-center gap-3 text-slate-400">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-600 border-t-emerald-400" />
          Analyzing skill...
        </div>
      )}
    </div>
  );
}
