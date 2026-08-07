"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { QueryResponse } from "@/lib/types";
import ReportDetailModal from "./ReportDetailModal";

const EXAMPLE_PROMPTS = [
  "What incidents involved David Chen?",
  "What happened in May 2026?",
  "List harassment complaints in the warehouse",
  "Who was involved in INC-0004?",
];

export default function AskAgent() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedReport, setSelectedReport] = useState<string | null>(null);

  async function submit(e?: React.FormEvent) {
    e?.preventDefault();
    const q = question.trim();
    if (!q) return;

    setLoading(true);
    setError(null);
    try {
      setResult(await api.query(q));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-slate-600 text-sm mb-3">
          Ask natural-language questions about incident reports. Answers are
          grounded in retrieved sources with citations.
        </p>
        <form onSubmit={submit} className="flex gap-3">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="What incidents involved David Chen in May 2026?"
            className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-3 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="rounded-lg bg-indigo-600 px-6 py-3 font-medium text-white hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? "Thinking…" : "Ask"}
          </button>
        </form>
      </div>

      <div className="flex flex-wrap gap-2">
        {EXAMPLE_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            onClick={() => {
              setQuestion(prompt);
            }}
            className="rounded-full border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-600 hover:border-indigo-400 hover:text-indigo-700 transition-colors"
          >
            {prompt}
          </button>
        ))}
      </div>

      {error && (
        <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-rose-700 text-sm">
          {error}
        </div>
      )}

      {loading && (
        <div className="space-y-3 animate-pulse">
          <div className="h-24 rounded-xl bg-slate-200" />
          <div className="h-16 rounded-lg bg-slate-200/70" />
          <div className="h-16 rounded-lg bg-slate-200/70" />
        </div>
      )}

      {result && !loading && (
        <div className="space-y-5">
          <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-xs uppercase tracking-wider text-slate-500 mb-3">
              Answer
            </h2>
            <p className="leading-relaxed text-slate-800 whitespace-pre-wrap">
              {result.answer}
            </p>
          </section>

          {result.sources.length > 0 && (
            <section>
              <h2 className="text-xs uppercase tracking-wider text-slate-500 mb-3">
                Sources ({result.sources.length})
              </h2>
              <div className="grid gap-3">
                {result.sources.map((source, i) => (
                  <article
                    key={i}
                    className="rounded-lg border border-slate-200 bg-white p-4 hover:border-slate-300 shadow-sm transition-colors"
                  >
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      {source.report_id && (
                        <button
                          onClick={() => setSelectedReport(source.report_id!)}
                          className="rounded-md bg-indigo-50 text-indigo-700 px-2.5 py-1 text-xs font-medium hover:bg-indigo-100 transition-colors"
                        >
                          {source.report_id}
                        </button>
                      )}
                      {source.date && (
                        <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs text-slate-600">
                          {source.date}
                        </span>
                      )}
                      {source.incident_type && (
                        <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs text-slate-600">
                          {source.incident_type}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-600 leading-relaxed">
                      {source.excerpt}
                      {source.excerpt.length >= 200 && "…"}
                    </p>
                  </article>
                ))}
              </div>
            </section>
          )}

          <details className="rounded-lg border border-slate-200 bg-white shadow-sm">
            <summary className="cursor-pointer px-4 py-3 text-xs uppercase tracking-wider text-slate-500 hover:text-slate-700">
              Routing debug
            </summary>
            <pre className="px-4 pb-4 text-xs text-slate-600 overflow-auto font-mono">
              {JSON.stringify(result.routing, null, 2)}
            </pre>
          </details>
        </div>
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
