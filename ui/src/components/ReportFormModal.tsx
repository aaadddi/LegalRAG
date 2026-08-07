"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ReportCreateInput, ReportDetail, ReportUpdateInput } from "@/lib/types";

interface Props {
  mode: "create" | "edit";
  reportId?: string;
  onClose: () => void;
  onSaved: () => void;
}

const EMPTY_FORM = {
  report_id: "",
  date: "",
  location: "",
  incident_type: "",
  reporting_officer: "",
  people_involved: "",
  narrative: "",
};

export default function ReportFormModal({
  mode,
  reportId,
  onClose,
  onSaved,
}: Props) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [loading, setLoading] = useState(mode === "edit");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (mode !== "edit" || !reportId) return;

    setLoading(true);
    setError(null);
    api
      .report(reportId)
      .then((report: ReportDetail) => {
        setForm({
          report_id: report.report_id,
          date: report.date,
          location: report.location ?? "",
          incident_type: report.incident_type ?? "",
          reporting_officer: report.reporting_officer ?? "",
          people_involved: report.people_involved.join(", "),
          narrative: report.narrative,
        });
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load report"),
      )
      .finally(() => setLoading(false));
  }, [mode, reportId]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function update(field: keyof typeof form, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function parsePeople(raw: string): string[] {
    return raw
      .split(",")
      .map((p) => p.trim())
      .filter(Boolean);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.date.trim() || !form.narrative.trim()) {
      setError("Date and narrative are required.");
      return;
    }

    setSaving(true);
    setError(null);

    const payload = {
      date: form.date,
      location: form.location.trim(),
      incident_type: form.incident_type.trim(),
      reporting_officer: form.reporting_officer.trim(),
      people_involved: parsePeople(form.people_involved),
      narrative: form.narrative.trim(),
    };

    try {
      if (mode === "create") {
        const createPayload: ReportCreateInput = {
          ...payload,
          ...(form.report_id.trim()
            ? { report_id: form.report_id.trim() }
            : {}),
        };
        await api.createReport(createPayload);
      } else if (reportId) {
        await api.updateReport(reportId, payload as ReportUpdateInput);
      }
      onSaved();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save report");
    } finally {
      setSaving(false);
    }
  }

  const inputClass =
    "mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500";
  const labelClass = "block text-sm text-slate-600";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-xl border border-slate-200 bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center justify-between border-b border-slate-200 bg-white px-5 py-4">
          <h2 className="font-semibold text-slate-900">
            {mode === "create" ? "New Report" : `Edit ${reportId}`}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-3 py-1 text-sm text-slate-600 hover:bg-slate-100"
          >
            Cancel
          </button>
        </div>

        <form onSubmit={submit} className="p-5 space-y-4">
          {loading && (
            <p className="text-slate-500 text-sm">Loading report…</p>
          )}

          {!loading && (
            <>
              {mode === "create" && (
                <label className={labelClass}>
                  Report ID{" "}
                  <span className="text-slate-400">(optional, auto-generated)</span>
                  <input
                    value={form.report_id}
                    onChange={(e) => update("report_id", e.target.value)}
                    placeholder="INC-0043"
                    className={inputClass}
                  />
                </label>
              )}

              <div className="grid gap-4 sm:grid-cols-2">
                <label className={labelClass}>
                  Date <span className="text-rose-500">*</span>
                  <input
                    type="date"
                    required
                    value={form.date}
                    onChange={(e) => update("date", e.target.value)}
                    className={inputClass}
                  />
                </label>
                <label className={labelClass}>
                  Incident type
                  <input
                    value={form.incident_type}
                    onChange={(e) => update("incident_type", e.target.value)}
                    placeholder="Harassment Complaint"
                    className={inputClass}
                  />
                </label>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className={labelClass}>
                  Location
                  <input
                    value={form.location}
                    onChange={(e) => update("location", e.target.value)}
                    placeholder="Warehouse A, Aisle 12"
                    className={inputClass}
                  />
                </label>
                <label className={labelClass}>
                  Reporting officer
                  <input
                    value={form.reporting_officer}
                    onChange={(e) => update("reporting_officer", e.target.value)}
                    placeholder="Officer T. Alvarez"
                    className={inputClass}
                  />
                </label>
              </div>

              <label className={labelClass}>
                People involved{" "}
                <span className="text-slate-400">(comma-separated)</span>
                <input
                  value={form.people_involved}
                  onChange={(e) => update("people_involved", e.target.value)}
                  placeholder="David Chen, Tomas Kowalski"
                  className={inputClass}
                />
              </label>

              <label className={labelClass}>
                Narrative <span className="text-rose-500">*</span>
                <textarea
                  required
                  rows={6}
                  value={form.narrative}
                  onChange={(e) => update("narrative", e.target.value)}
                  placeholder="Describe the incident…"
                  className={`${inputClass} resize-y min-h-[120px]`}
                />
              </label>
            </>
          )}

          {error && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-rose-700 text-sm">
              {error}
            </div>
          )}

          {!loading && (
            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={saving}
                className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {saving
                  ? "Saving…"
                  : mode === "create"
                    ? "Create report"
                    : "Save changes"}
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
