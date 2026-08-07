"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ReportDetail } from "@/lib/types";

interface Props {
  reportId: string;
  onClose: () => void;
  onEdit?: () => void;
  onDelete?: () => void | Promise<void>;
}

export default function ReportDetailModal({
  reportId,
  onClose,
  onEdit,
  onDelete,
}: Props) {
  const [report, setReport] = useState<ReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(null);
    api
      .report(reportId)
      .then(setReport)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load report"),
      )
      .finally(() => setLoading(false));
  }, [reportId]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function handleDelete() {
    if (!onDelete) return;
    if (
      !window.confirm(
        `Delete report ${reportId}? This cannot be undone.`,
      )
    ) {
      return;
    }
    setDeleting(true);
    try {
      await onDelete();
      onClose();
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-slate-200 bg-white px-5 py-4">
          <h2 className="font-semibold text-slate-900">{reportId}</h2>
          <div className="flex items-center gap-2">
            {onEdit && (
              <button
                onClick={onEdit}
                className="rounded-lg border border-slate-300 px-3 py-1 text-sm text-slate-600 hover:bg-slate-100"
              >
                Edit
              </button>
            )}
            {onDelete && (
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="rounded-lg border border-rose-200 px-3 py-1 text-sm text-rose-600 hover:bg-rose-50 disabled:opacity-50"
              >
                {deleting ? "Deleting…" : "Delete"}
              </button>
            )}
            <button
              onClick={onClose}
              className="rounded-lg px-3 py-1 text-sm text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            >
              Close
            </button>
          </div>
        </div>

        <div className="p-5">
          {loading && <p className="text-slate-500 text-sm">Loading report…</p>}
          {error && <p className="text-rose-600 text-sm">{error}</p>}
          {report && (
            <div className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <Badge>{report.date}</Badge>
                {report.incident_type && <Badge>{report.incident_type}</Badge>}
                {report.location && <Badge>{report.location}</Badge>}
                {report.reporting_officer && (
                  <Badge>Officer: {report.reporting_officer}</Badge>
                )}
              </div>
              {report.people_involved.length > 0 && (
                <div>
                  <p className="text-xs uppercase tracking-wider text-slate-500 mb-2">
                    People involved
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {report.people_involved.map((person) => (
                      <Badge key={person}>{person}</Badge>
                    ))}
                  </div>
                </div>
              )}
              <p className="text-slate-700 leading-relaxed whitespace-pre-wrap">
                {report.narrative}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs text-slate-700">
      {children}
    </span>
  );
}
