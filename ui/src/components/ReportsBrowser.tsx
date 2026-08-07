"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ReportSummary } from "@/lib/types";
import ReportDetailModal from "./ReportDetailModal";
import ReportFormModal from "./ReportFormModal";

export default function ReportsBrowser() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedReport, setSelectedReport] = useState<string | null>(null);
  const [formMode, setFormMode] = useState<"create" | "edit" | null>(null);
  const [editReportId, setEditReportId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setReports(await api.reports(start || undefined, end || undefined));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load reports");
    } finally {
      setLoading(false);
    }
  }, [start, end]);

  useEffect(() => {
    load();
  }, [load]);

  function openCreate() {
    setEditReportId(null);
    setFormMode("create");
  }

  function openEdit(reportId: string) {
    setEditReportId(reportId);
    setFormMode("edit");
    setSelectedReport(null);
  }

  async function handleDelete(reportId: string) {
    if (
      !window.confirm(
        `Delete report ${reportId}? This removes it from the database, vector index, and disk.`,
      )
    ) {
      return;
    }

    setDeletingId(reportId);
    setError(null);
    try {
      await api.deleteReport(reportId);
      if (selectedReport === reportId) setSelectedReport(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete report");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <p className="text-slate-600 text-sm max-w-xl">
          Browse, create, edit, and delete incident reports. Changes sync to
          SQLite, the markdown file on disk, and the vector index.
        </p>
        <button
          onClick={openCreate}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 transition-colors shrink-0"
        >
          + New report
        </button>
      </div>

      <div className="flex flex-wrap gap-4 items-end">
        <label className="text-sm text-slate-600">
          Start date
          <input
            type="date"
            value={start}
            onChange={(e) => setStart(e.target.value)}
            className="mt-1 block rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </label>
        <label className="text-sm text-slate-600">
          End date
          <input
            type="date"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
            className="mt-1 block rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </label>
        <button
          onClick={load}
          disabled={loading}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
        >
          {loading ? "Loading…" : "Apply filter"}
        </button>
        {(start || end) && (
          <button
            onClick={() => {
              setStart("");
              setEnd("");
            }}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-rose-700 text-sm">
          {error}
        </div>
      )}

      {!loading && !error && (
        <p className="text-xs text-slate-500">{reports.length} report(s)</p>
      )}

      <ul className="divide-y divide-slate-200 rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        {loading
          ? Array.from({ length: 5 }).map((_, i) => (
              <li key={i} className="bg-white px-4 py-4 animate-pulse">
                <div className="h-4 w-32 bg-slate-200 rounded mb-2" />
                <div className="h-3 w-48 bg-slate-100 rounded" />
              </li>
            ))
          : reports.map((r) => (
              <li
                key={r.report_id}
                className="bg-white px-4 py-4 flex justify-between items-start gap-4 hover:bg-slate-50 transition-colors"
              >
                <button
                  onClick={() => setSelectedReport(r.report_id)}
                  className="flex-1 text-left min-w-0"
                >
                  <p className="font-medium text-slate-900">{r.report_id}</p>
                  <p className="text-sm text-slate-600 mt-0.5">
                    {r.incident_type ?? "Unknown type"}
                    {r.location ? ` · ${r.location}` : ""}
                  </p>
                  {r.reporting_officer && (
                    <p className="text-xs text-slate-500 mt-1">
                      {r.reporting_officer}
                    </p>
                  )}
                </button>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-sm text-slate-500 mr-2">{r.date}</span>
                  <button
                    onClick={() => openEdit(r.report_id)}
                    className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(r.report_id)}
                    disabled={deletingId === r.report_id}
                    className="rounded-lg border border-rose-200 px-3 py-1.5 text-xs text-rose-600 hover:bg-rose-50 disabled:opacity-50"
                  >
                    {deletingId === r.report_id ? "Deleting…" : "Delete"}
                  </button>
                </div>
              </li>
            ))}
        {!loading && reports.length === 0 && (
          <li className="bg-white px-4 py-8 text-center text-slate-500 text-sm">
            No reports found.{" "}
            <button
              onClick={openCreate}
              className="text-indigo-600 hover:underline"
            >
              Create one
            </button>
          </li>
        )}
      </ul>

      {selectedReport && (
        <ReportDetailModal
          reportId={selectedReport}
          onClose={() => setSelectedReport(null)}
          onEdit={() => openEdit(selectedReport)}
          onDelete={async () => {
            await handleDelete(selectedReport);
          }}
        />
      )}

      {formMode && (
        <ReportFormModal
          mode={formMode}
          reportId={editReportId ?? undefined}
          onClose={() => setFormMode(null)}
          onSaved={load}
        />
      )}
    </div>
  );
}
