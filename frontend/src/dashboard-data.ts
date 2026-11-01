import type { Dashboard } from "./api";

export function validDashboard(
  value: unknown,
  managementRequired = false,
): boolean {
  if (!value || typeof value !== "object") return false;
  const d = value as Dashboard;
  const count = (v: unknown) => Number.isSafeInteger(v) && Number(v) >= 0;
  const rows = <T,>(v: unknown, valid: (row: T) => boolean): boolean =>
    Array.isArray(v) && v.every((row) => !!row && valid(row));
  const validCase = (c: Dashboard["attention"][number]) =>
    typeof c.id === "string" &&
    typeof c.reference === "string" &&
    typeof c.summary === "string" &&
    typeof c.bureau === "string" &&
    typeof c.due_at === "string" &&
    typeof c.institution?.id === "string" &&
    typeof c.institution?.name === "string";
  if (
    ![
      d.pending,
      d.overdue,
      d.total,
      d.disposed,
      d.institutions,
      d.approaching,
      d.unresolved_escalations,
      d.under_process,
    ].every(count) ||
    typeof d.generated_at !== "string" ||
    typeof d.closed_share !== "number" ||
    !Number.isFinite(d.closed_share) ||
    d.closed_share < 0 ||
    d.closed_share > 1
  )
    return false;
  if (
    !rows(d.attention, validCase) ||
    !rows(d.recent, validCase) ||
    !rows<{ month: string; received: number; disposed: number }>(
      d.trend,
      (t) =>
        typeof t.month === "string" && count(t.received) && count(t.disposed),
    ) ||
    !rows<{
      bureau__code: string;
      count: number;
      overdue: number;
      approaching: number;
      institutions: number;
    }>(
      d.workload,
      (b) =>
        typeof b.bureau__code === "string" &&
        [b.count, b.overdue, b.approaching, b.institutions].every(count),
    )
  )
    return false;
  if (
    !rows<{ name: string; count: number }>(
      d.ageing,
      (r) => typeof r.name === "string" && count(r.count),
    ) ||
    !rows<{ status: string; count: number }>(
      d.statuses,
      (r) => typeof r.status === "string" && count(r.count),
    )
  )
    return false;
  if (
    ![d.categories, d.active_categories].every((v) =>
      rows<{ category: string; count: number }>(
        v,
        (r) => typeof r.category === "string" && count(r.count),
      ),
    ) ||
    !Array.isArray(d.overdue_bureaus) ||
    !d.overdue_bureaus.every(
      (b) => !!b && typeof b.bureau__code === "string" && count(b.count),
    )
  )
    return false;
  if (
    !d.matching ||
    typeof d.matching !== "object" ||
    Array.isArray(d.matching) ||
    !Object.values(d.matching).every(count)
  )
    return false;
  if (managementRequired && !d.management) return false;
  if (d.management !== undefined) {
    const m = d.management;
    if (!m || !count(m.pending_acknowledgment_records) || !count(d.coordination_institutions) || !count(d.overlap_reviews))
      return false;
    if (
      !rows<NonNullable<Dashboard["management"]>["institutions"][number]>(
        m.institutions,
        (r) =>
          typeof r.institution_id === "string" &&
          typeof r.institution__name === "string" &&
          typeof r.institution__permanent_id === "string" &&
          typeof r.institution__region === "string" &&
          (r.institution__district === undefined || typeof r.institution__district === "string") &&
          [
            r.count,
            r.overdue,
            r.approaching,
            r.unresolved_escalations,
            r.bureaus,
          ].every(count) &&
          Array.isArray(r.bureau_names) &&
          r.bureau_names.every((n) => typeof n === "string") &&
          (r.bureau_details === undefined || rows<{code:string;name:string;count:number}>(r.bureau_details,
            b => typeof b.code === "string" && typeof b.name === "string" && count(b.count))) &&
          typeof r.coordination === "boolean",
      )
    )
      return false;
    if (!rows<NonNullable<Dashboard["management"]>["priority_institutions"][number]>(m.priority_institutions, r =>
      typeof r.institution_id === "string" && typeof r.institution__name === "string" &&
      typeof r.institution__permanent_id === "string" && typeof r.earliest_deadline === "string" &&
      [r.count, r.overdue, r.unresolved_escalations].every(count))) return false;
    if (
      !rows<NonNullable<Dashboard["management"]>["regions"][number]>(
        m.regions,
        (r) =>
          typeof r.institution__region === "string" &&
          typeof r.institution__district === "string" &&
          count(r.count) &&
          count(r.institutions),
      ) ||
      !rows<{ classification: string; count: number }>(
        m.classifications,
        (r) => typeof r.classification === "string" && count(r.count),
      )
    )
      return false;
    if (
      !rows<{
        start: string;
        label: string;
        received: number;
        disposed: number;
      }>(
        m.quarters,
        (r) =>
          typeof r.start === "string" &&
          typeof r.label === "string" &&
          count(r.received) &&
          count(r.disposed),
      ) ||
      !rows<{ event: string; count: number }>(
        m.movement_counts,
        (r) => typeof r.event === "string" && count(r.count),
      ) ||
      !rows<NonNullable<Dashboard["management"]>["recent_movements"][number]>(
        m.recent_movements,
        (r) =>
          typeof r.case_id === "string" &&
          typeof r.reference === "string" &&
          typeof r.event === "string" &&
          typeof r.reason === "string" &&
          typeof r.institution === "string" &&
          typeof r.created_at === "string",
      )
    )
      return false;
    if (
      !rows<NonNullable<Dashboard["coordination_notices"]>[number]>(
        d.coordination_notices,
        (r) =>
          typeof r.institution_id === "string" &&
          typeof r.institution__name === "string" &&
          count(r.bureaus) &&
          count(r.count),
      )
    )
      return false;
  }
  return true;
}
