export type User = {
  id: number;
  name: string;
  username: string;
  role: string;
  bureau: string | null;
  features?: { reviewed_facts: boolean; incident_groups: boolean; demo_mode?: boolean };
};
export const classifications: Record<string, string> = {
  grievance: "Grievance",
  regulatory_compliance: "Regulatory / Compliance",
  unclassified: "Unclassified",
};
export type Institution = {
  id: string;
  name: string;
  permanent_id: string;
  region: string;
  district: string;
};
export type InstitutionProfile = Institution & {
  address: string;
  official_email: string;
  official_phone: string;
  version: number;
  overview: {
    total: number;
    open: number;
    closed: number;
    overdue: number;
    unresolved_escalations: number;
  };
  classifications: { classification: string; count: number }[];
  scope: "all_bureaus" | "current_bureau";
  history_period: "all_time";
  bureaus: { bureau__code: string; bureau__name: string; count: number }[];
  cases_url: string;
  history_url: string;
};
export type InstitutionAction = CaseAction & {
  case_id: string;
  reference: string;
};
export type Case = {
  has_unresolved_escalation: boolean;
  id: string;
  reference: string;
  institution: Institution;
  bureau: string;
  category: string;
  classification: string;
  next_action: string;
  next_action_date: string | null;
  summary: string;
  description: string;
  source_system: string;
  source_reference: string;
  source_status: string;
  source_bureau: string | null;
  source_last_seen_at: string | null;
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
  bureau_at_action: string | null;
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
export type Escalation = {
  id: string;
  case: Case;
  created_by: string;
  reason: string;
  status: "pending" | "resolved";
  created_at: string;
  resolved_by: string | null;
  resolution_reason: string;
  resolved_at: string | null;
  version: number;
};
export type Page<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};
export type Options = {
  categories?: string[];
  category_labels?: Record<string,string>;
  bureaus: { code: string; name: string }[];
  officers: { id: number; name: string; bureau: string }[];
  regions: string[];
};
export type EvidenceComparison = {
  left: string | string[] | null;
  right: string | string[] | null;
  state: "agrees" | "differs" | "unknown" | "unverified";
};
export type MatchingEvidence = {
  institution?: string;
  shared_reference?: boolean;
  categories?: string[];
  incident_dates?: string[];
  scope?: string;
  schema_version?: number;
  discovery_method?: string;
  matching_policy_revision?: string;
  cosine_score?: number | null;
  encoder_revision?: string | null;
  comparisons?: Record<string, EvidenceComparison>;
  canonical_institution?: {
    left: { id: string; permanent_id: string; name: string };
    right: { id: string; permanent_id: string; name: string };
    state: string;
    source: string;
  };
  provenance?: { source: string; left_case_id: string; right_case_id: string; left_case_version: number; right_case_version: number };
  incident_finding?: { state: string; source: string };
  limitations?: string[];
};
export type ReviewSnapshot = {
  evidence: MatchingEvidence;
  matching_policy_revision: string | null;
  score: number | null;
  model_revision: string;
  origin: string;
  relationship_version: number;
  decision: string;
  reason: string;
  reviewer: { id: number; name: string };
  reviewed_at: string;
};
export type Overlap = {
  id: number;
  left: Case;
  right: Case;
  score: number | null;
  origin: "semantic" | "manual";
  evidence: MatchingEvidence;
  review_snapshot?: ReviewSnapshot | null;
  decision: string;
  reason: string;
  version: number;
  model_revision: string;
  reviewer: string | null;
  reviewed_at: string | null;
};
export type Dashboard = {
  institutions: number;
  approaching: number;
  unresolved_escalations: number;
  under_process: number;
  coordination_institutions?: number;
  closed_share: number;
  management?: {
    pending_acknowledgment_records: number;
    priority_institutions: {
      institution_id: string;
      institution__name: string;
      institution__permanent_id: string;
      count: number;
      overdue: number;
      unresolved_escalations: number;
      earliest_deadline: string;
    }[];
    regions: {
      institution__region: string;
      institution__district: string;
      count: number;
      institutions: number;
    }[];
    classifications: { classification: string; count: number }[];
    institutions: {
      institution_id: string;
      institution__name: string;
      institution__permanent_id: string;
      institution__region: string;
      institution__district?: string;
      count: number;
      /** bureaus is returned by the analytics function */
      bureaus?: number;
      overdue: number;
      approaching?: number;
      /** unresolved_escalations is returned by Milestone 3 analytics */
      unresolved_escalations?: number;
      /** Legacy field name still returned by older analytics path */
      escalations?: number;
      bureau_names: string[];
      bureau_details?: { code: string; name: string; count: number }[];
      coordination: boolean;
    }[];
    quarters: {
      start: string;
      label: string;
      received: number;
      disposed: number;
    }[];
    movement_counts: { event: string; count: number }[];
    recent_movements: Movement[];
  };
  attention: Case[];
  active_categories: { category: string; count: number }[];
  categories: { category: string; count: number }[];
  overdue_bureaus: { bureau__code: string; bureau__name?: string; count: number }[];
  matching: Record<string, number>;
  total: number;
  pending: number;
  overdue: number;
  disposed: number;
  overlap_reviews?: number;
  generated_at: string;
  recent: Case[];
  workload: {
    bureau__code: string;
    bureau__name?: string;
    count: number;
    overdue: number;
    approaching?: number;
    institutions?: number;
  }[];
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
export type Movement = CaseAction & {
  case_id: string;
  reference: string;
  institution: string;
  event: string;
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
  "other",
  "needs_categorization",
];
const categoryLabels: Record<string,string> = {other:'Other',needs_categorization:'Needs categorization'};
export const categoryLabel = (value: string) => typeof value==='string' ? (Object.hasOwn(categoryLabels,value) ? categoryLabels[value] : value.replaceAll('_',' ')) : 'Unknown category';
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
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
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
  if (!response.ok) throw new ApiError(errorText(data), response.status);
  if (url === '/api/options' && data.categories !== undefined) {
    if (!Array.isArray(data.categories) || !data.categories.every((c:unknown)=>typeof c==='string') ||
        !data.category_labels || typeof data.category_labels!=='object' || Array.isArray(data.category_labels) || !Object.values(data.category_labels).every(x=>typeof x==='string'))
      throw new Error('The server returned malformed category choices.');
    categories.splice(0,categories.length,...data.categories);
    Object.assign(categoryLabels,data.category_labels);
  }
  return data;
}
