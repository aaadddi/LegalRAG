"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import AskAgent from "@/components/AskAgent";
import ReportsBrowser from "@/components/ReportsBrowser";
import PersonProfile from "@/components/PersonProfile";

type Tab = "ask" | "reports" | "profile";

const TABS: { id: Tab; label: string }[] = [
  { id: "ask", label: "Ask Agent" },
  { id: "reports", label: "Reports" },
  { id: "profile", label: "Person Profile" },
];

export default function Home() {
  const [tab, setTab] = useState<Tab>("ask");
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    api
      .health()
      .then(() => setHealthy(true))
      .catch(() => setHealthy(false));
  }, []);

  return (
    <div className="min-h-full flex flex-col bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">
            Legal Incident RAG
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Query incident reports with AI-powered retrieval
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span
            className={`inline-block h-2 w-2 rounded-full ${
              healthy === null
                ? "bg-slate-500 animate-pulse"
                : healthy
                  ? "bg-emerald-400"
                  : "bg-rose-400"
            }`}
          />
          <span
            className={
              healthy === null
                ? "text-slate-500"
                : healthy
                  ? "text-emerald-600"
                  : "text-rose-600"
            }
          >
            {healthy === null
              ? "Checking API…"
              : healthy
                ? "API connected"
                : "API offline — start uvicorn api.main:app --reload"}
          </span>
        </div>
      </header>

      <nav className="flex gap-1 px-6 py-3 border-b border-slate-200 bg-white">
        {TABS.map(({ id, label }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === id
                ? "bg-indigo-600 text-white"
                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            }`}
          >
            {label}
          </button>
        ))}
      </nav>

      <main className="flex-1 max-w-4xl w-full mx-auto px-6 py-8">
        {tab === "ask" && <AskAgent />}
        {tab === "reports" && <ReportsBrowser />}
        {tab === "profile" && <PersonProfile />}
      </main>
    </div>
  );
}
