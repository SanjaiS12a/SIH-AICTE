export type User = {
  id: number;
  name: string;
  username: string;
  role: string;
  bureau: string | null;
};
export type Institution = {
  id: string;
  name: string;
  permanent_id: string;
  region: string;
  district: string;
};
export type Case = {
  id: string;
  reference: string;
  institution: Institution;
  bureau: string;
  category: string;
  summary: string;
  description: string;
  source_system: string;
  source_reference: string;
  incident_date: string | null;
  status: string;
  received_at: string;
  due_at: string;
  disposed_at: string | null;
  assigned_to: number | null;
  assigned_name: string;
  matching_state: string;
  matching_error: string;
  model_revision: string;
  version: number;
  overdue: boolean;
  created_at: string;
};
export type CaseAction = {
  id: number;
  kind: string;
  actor: string;
  reason: string;
  changes: Record<string, unknown>;
  created_at: string;
};
export type Attachment = {
  id: string;
  original_name: string;
  content_type: string;
  size: number;
  created_at: string;
};
export type CaseDetail = Case & {
  actions: CaseAction[];
  attachments: Attachment[];
  institution_history: Case[];
};
export type Page<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};
export type Options = {
  bureaus: { code: string; name: string }[];
  officers: { id: number; name: string; bureau: string }[];
  regions: string[];
};
export type Overlap = {
  id: number;
  left: Case;
  right: Case;
  score: number;
  evidence: {
    institution: string;
    shared_reference: boolean;
    categories: string[];
    incident_dates: string[];
    scope: string;
  };
  decision: string;
  reason: string;
  version: number;
  model_revision: string;
  reviewer: string | null;
  reviewed_at: string | null;
};
export type Dashboard = {
  attention: Case[];
  active_categories: { category: string; count: number }[];
  categories: { category: string; count: number }[];
  overdue_bureaus: { bureau__code: string; count: number }[];
  matching: Record<string, number>;
  total: number;
  pending: number;
  overdue: number;
  disposed: number;
  overlap_reviews?: number;
  generated_at: string;
  recent: Case[];
  workload: { bureau__code: string; count: number }[];
  statuses: { status: string; count: number }[];
  ageing: { name: string; count: number }[];
  trend: { month: string; received: number; disposed: number }[];
  coordination_notices?: {
    institution_id: string;
    institution__name: string;
    bureaus: number;
    count: number;
  }[];
};
export const labels: Record<string, string> = {
  registered: "Registered",
  under_review: "Under review",
  awaiting_response: "Awaiting response",
  disposed: "Closed",
  same_incident: "Same incident",
  related_issue: "Related issue",
  unrelated: "Unrelated",
  pending: "Pending review",
};
export const categories = [
  "admissions",
  "refunds",
  "documents",
  "facilities",
  "scholarships",
  "administration",
];
export const statuses = [
  "registered",
  "under_review",
  "awaiting_response",
  "disposed",
];
export const date = (value: string | null) =>
  value
    ? new Date(value).toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
      })
    : "Not recorded";
export function csrf() {
  return (
    document.cookie
      .split("; ")
      .find((x) => x.startsWith("csrftoken="))
      ?.slice(10) || ""
  );
}
export function errorText(value: unknown): string {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.map(errorText).join(" ");
  if (value && typeof value === "object")
    return Object.entries(value)
      .map(
        ([k, v]) =>
          `${k === "error" || k === "detail" ? "" : k + ": "}${errorText(v)}`,
      )
      .join(" ");
  return "The request could not be completed.";
}
export async function api<T>(url: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(url, {
    credentials: "same-origin",
    ...init,
    headers: {
      ...(init.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      "X-CSRFToken": csrf(),
      ...init.headers,
    },
  });
  const data = await response
    .json()
    .catch(() => ({ error: "The server returned an unexpected response." }));
  if (!response.ok) throw new Error(errorText(data));
  return data;
}
