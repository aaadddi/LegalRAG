import type {
  QueryResponse,
  ReportCreateInput,
  ReportDetail,
  ReportSummary,
  ReportUpdateInput,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = err.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).join(", ")
          : res.statusText;
    throw new Error(message || "Request failed");
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json();
}

export const api = {
  health: () => request<{ status: string }>("/health"),

  query: (question: string) =>
    request<QueryResponse>("/query", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  reports: (start?: string, end?: string) => {
    const params = new URLSearchParams();
    if (start) params.set("start_date", start);
    if (end) params.set("end_date", end);
    const q = params.toString();
    return request<ReportSummary[]>(`/reports${q ? `?${q}` : ""}`);
  },

  report: (id: string) => request<ReportDetail>(`/reports/${id}`),

  createReport: (data: ReportCreateInput) =>
    request<ReportDetail>("/reports", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateReport: (id: string, data: ReportUpdateInput) =>
    request<ReportDetail>(`/reports/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteReport: (id: string) =>
    request<void>(`/reports/${id}`, { method: "DELETE" }),

  profile: (name: string) =>
    request<ReportSummary[]>(`/profile/${encodeURIComponent(name)}`),
};
