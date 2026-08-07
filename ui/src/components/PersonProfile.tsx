"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { ReportSummary } from "@/lib/types";
import ReportDetailModal from "./ReportDetailModal";

export default function PersonProfile() {
  const [name, setName] = useState("David Chen");
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [selectedReport, setSelectedReport] = useState<string | null>(null);

  async function search(e?: React.FormEvent) {
    e?.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;

    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      setReports(await api.profile(trimmed));
    } catch (err) {
      setReports([]);
      setError(err instanceof Error ? err.message : "Person not found");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-slate-600 text-sm">
        Look up all incident reports involving a specific person, sorted by
        date.
      </p>

      <form onSubmit={search} className="flex gap-3">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Person name"
          className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-3 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !name.trim()}
          className="rounded-lg bg-indigo-600 px-6 py-3 font-medium text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </form>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-rose-700 text-sm">
          {error}
        </div>
      )}

      {reports.length > 0 && (
        <div>
          <p className="text-xs text-slate-500 mb-3">
            {reports.length} incident(s) involving{" "}
            <span className="text-slate-800 font-medium">{name}</span>
          </p>
          <ul className="space-y-2">
            {reports.map((r) => (
              <li key={r.report_id}>
                <button
                  onClick={() => setSelectedReport(r.report_id)}
                  className="w-full rounded-lg border border-slate-200 bg-white p-4 text-left hover:border-slate-300 hover:bg-slate-50 shadow-sm transition-colors"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-slate-900">
                        {r.report_id} — {r.incident_type ?? "Unknown"}
                      </p>
                      <p className="text-sm text-slate-600 mt-0.5">
                        {r.location ?? "Location unknown"}
                      </p>
                    </div>
                    <span className="text-sm text-slate-500 shrink-0 ml-4">
                      {r.date}
                    </span>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {searched && !loading && !error && reports.length === 0 && (
        <p className="text-slate-500 text-sm">No incidents found.</p>
      )}

      {selectedReport && (
        <ReportDetailModal
          reportId={selectedReport}
          onClose={() => setSelectedReport(null)}
        />
      )}
    </div>
  );
}
