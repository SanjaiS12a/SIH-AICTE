/**
 * Management Command Centre — Milestone 3
 *
 * All metrics come from the authoritative /api/dashboard response.
 * No client-side reconstruction of totals.
 * Every KPI has a corresponding drill-down link.
 */
import { useState } from "react";
import { ArrowDownLeft, ArrowRight, CheckCircle, Clock, FileText } from "@phosphor-icons/react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  LabelList,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { date, classifications } from "./api";
import type { Dashboard, Case, Page, Movement } from "./api";
import { usePoll } from "./imports";
import { Heading, ErrorBox, Loading, Empty, Pagination, Badge } from "./ui";

// ── Types ──────────────────────────────────────────────────────────────────

export function ManagementHome({ data: d, filters }: { data: Dashboard; filters: string }) {
  const navigate = useNavigate();
  const m = d.management!;
  function cases(extra: Record<string, string> = {}) {
    const q = new URLSearchParams(filters); q.delete("page");
    Object.entries(extra).forEach(([k,v]) => v ? q.set(k,v) : q.delete(k));
    return `/cases?${q}`;
  }
  const cards: {label:string; count:number; extra:Record<string,string>; note:string; icon:typeof Clock}[] = [
    {label:"Received complaints", count:d.total, extra:{}, note:"All cases in the selected period", icon:ArrowDownLeft},
    {label:"Open complaints", count:d.pending, extra:{pending:"true"}, note:"Still waiting for resolution", icon:FileText},
    {label:"Under-process complaints", count:d.under_process, extra:{under_process:"true"}, note:"Being reviewed or awaiting a response", icon:Clock},
    {label:"Closed complaints", count:d.disposed, extra:{closed:"true"}, note:"A resolution has been recorded", icon:CheckCircle},
  ];
  return <>
    <div className="home-summary">{cards.map(({label,count,extra,note,icon:Icon}) =>
      <button className="home-stat" key={label} onClick={() => navigate(cases(extra))}>
        <span>{label}<Icon size={19} aria-hidden="true" /></span><strong>{count.toLocaleString("en-IN")}</strong>
        <small>{note}</small><ArrowRight className="stat-arrow" size={17} aria-hidden="true" />
      </button>)}</div>
    <div className="home-scope-note"><p>Selected receipt cohort. Under-process is included in Open.</p><Link to={cases({overdue:"true"})}>{d.overdue.toLocaleString("en-IN")} overdue complaints <ArrowRight size={14} aria-hidden="true" /></Link></div>
    <section className="panel home-attention" aria-labelledby="priority-title">
      <div className="home-section-heading"><div><h2 id="priority-title">Priority institutions</h2>
      <p>Selected receipt cohort. Ranked by overdue cases, unresolved escalations, then earliest deadline.</p></div></div>
      {m.priority_institutions.length ? <div className="table-wrap" role="region" aria-label="Priority institutions" tabIndex={0}><table>
        <thead><tr><th>Institution</th><th>Open</th><th>Overdue</th><th>Unresolved escalations</th><th>Earliest deadline</th></tr></thead>
        <tbody>{m.priority_institutions.map(i => <tr key={i.institution_id}>
          <td><Link to={`/institutions/${i.institution_id}`}>{i.institution__name}</Link><span className="table-sub">{i.institution__permanent_id}</span></td>
          <td><Link to={cases({institution:i.institution_id,pending:"true"})}>{i.count}</Link></td>
          <td><Link to={cases({institution:i.institution_id,overdue:"true"})}>{i.overdue}</Link></td>
          <td><Link to={cases({institution:i.institution_id,escalated:"true",pending:"true"})}>{i.unresolved_escalations}</Link></td>
          <td>{date(i.earliest_deadline)}</td>
        </tr>)}</tbody></table></div> : <div className="home-empty">No open cases in this cohort.</div>}
      <p className="home-guidance">Institution profiles show all-time authorized history, independently of these receipt filters.</p>
    </section>
  </>;
}

type Notice = {
  institution_id: string;
  institution__name: string;
  institution__permanent_id: string;
  institution__region: string;
  institution__district: string;
  count: number;
  bureaus: number;
  bureau_details: { code: string; name: string; count: number }[];
  officers: { name: string; count: number }[];
  cases: Case[];
  reviewed_relationships: number;
};

// ── CoordinationNotices (all-time cross-bureau panel) ─────────────────────

export function CoordinationNotices({ filters = "" }: { filters?: string }) {
  const [params, setParams] = useState(new URLSearchParams(filters));
  const { data, error } = usePoll<Page<Notice>>(
    `/api/coordination-notices?${params}`,
    5000,
  );
  return (
    <section
      className="panel detail-card"
      aria-label="All-time cross-bureau activity"
    >
      <div className="panel-heading">
        <h2>Cross-Bureau Activity — Coordination Review Required</h2>
      </div>
      <p className="card-body muted">
        All-time active cases across current Bureaus. Receipt dates, category
        and Bureau filters do not suppress detection. This notice does not
        confirm duplicate complaints or conflicting orders.
      </p>
      <ErrorBox message={error} />
      {!data && !error && <Loading />}
      {data && (
        <>
          {data.results.length ? (
            data.results.map((n) => (
              <article className="card-body" key={n.institution_id}>
                <h3>
                  <Link to={`/institutions/${n.institution_id}`}>
                    {n.institution__name}
                  </Link>
                </h3>
                <Link
                  to={`/coordination/workspace?institution=${n.institution_id}`}
                >
                  Open coordination workspace
                </Link>
                <p>
                  {n.institution__permanent_id} · {n.institution__region} ·{" "}
                  {n.institution__district} · {n.count} active cases ·{" "}
                  {n.bureaus} current Bureaus
                </p>
                <p>
                  {n.bureau_details
                    .map((b) => `${b.name}: ${b.count}`)
                    .join(" · ")}
                </p>
                <p>
                  Responsible officers:{" "}
                  {n.officers.map((o) => `${o.name} (${o.count})`).join(" · ")}
                </p>
                <div
                  className="table-scroll"
                  role="region"
                  aria-label={`Active cases at ${n.institution__name}`}
                  tabIndex={0}
                >
                  <table>
                    <thead>
                      <tr>
                        <th>Case</th>
                        <th>Bureau / officer</th>
                        <th>Status</th>
                        <th>Deadline</th>
                      </tr>
                    </thead>
                    <tbody>
                      {n.cases.map((c) => (
                        <tr key={c.id}>
                          <td>
                            <Link to={`/cases/${c.id}`}>{c.reference}</Link>
                          </td>
                          <td>
                            {c.bureau} · {c.assigned_name || "Unassigned"}
                          </td>
                          <td>
                            <Badge status={c.status} />
                          </td>
                          <td>{date(c.due_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="actions">
                  <Link
                    to={`/cases?institution=${n.institution_id}&pending=true`}
                  >
                    View all {n.count} active cases →
                  </Link>
                  <Link
                    to={`/coordination?institution=${n.institution_id}&decision=all`}
                  >
                    Review relationships ({n.reviewed_relationships}) →
                  </Link>
                </div>
                <small className="muted">
                  Preview: earliest five deadlines. The linked case list
                  includes every active case.
                </small>
              </article>
            ))
          ) : (
            <Empty>
              No institutions currently have active cases in two or more
              Bureaus.
            </Empty>
          )}
          <Pagination data={data} params={params} setParams={setParams} />
        </>
      )}
    </section>
  );
}

// ── Distribution chart (horizontal bar) ──────────────────────────────────

type ChartRow = { name: string; count: number; url: string };
function HorizontalDistribution({
  title,
  rows,
  color = "#2F7658",
  caption,
}: {
  title: string;
  rows: ChartRow[];
  color?: string;
  caption?: string;
}) {
  const navigate = useNavigate();
  if (!rows.length) {
    return (
      <section className="mgmt-chart-section">
        <div className="panel-heading">
          <h2>{title}</h2>
        </div>
        <div className="mgmt-chart-body">
          <Empty>No data in this cohort.</Empty>
        </div>
      </section>
    );
  }
  return (
    <section className="mgmt-chart-section">
      <div className="panel-heading">
        <h2>{title}</h2>
      </div>
      <div aria-hidden="true" style={{ height: Math.max(160, rows.length * 36 + 40) }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={rows}
            layout="vertical"
            margin={{ top: 8, right: 50, left: 8, bottom: 4 }}
          >
            <CartesianGrid stroke="#e2e8e4" horizontal={false} />
            <XAxis type="number" allowDecimals={false} />
            <YAxis
              type="category"
              dataKey="name"
              width={150}
              tick={{ fontSize: 11, fill: "#1F2D26" }}
              tickFormatter={(name) =>
                String(name).length > 26
                  ? String(name).slice(0, 24) + "…"
                  : String(name)
              }
            />
            <Tooltip />
            <Bar
              isAnimationActive={false}
              name={title}
              dataKey="count"
              fill={color}
              radius={[0, 4, 4, 0]}
              onClick={(entry) => {
                const row = (
                  (entry as unknown as { payload?: ChartRow }).payload ||
                  (entry as unknown as ChartRow)
                );
                if (row.url) navigate(row.url);
              }}
            >
              <LabelList
                dataKey="count"
                position="right"
                fill="#1F2D26"
                fontSize={11}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div
        className="table-scroll mgmt-chart-body"
        role="region"
        aria-label={`${title} data`}
        tabIndex={0}
      >
        <table>
          <caption>{caption || title}</caption>
          <thead>
            <tr>
              <th>Group</th>
              <th>Cases</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.name}>
                <th scope="row">{r.name}</th>
                <td>{r.count ? <Link to={r.url}>{r.count}</Link> : 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

// ── Ageing distribution — inline horizontal bars ──────────────────────────

function AgeingPanel({
  ageing,
  totalPending,
  cases,
}: {
  ageing: { name: string; count: number }[];
  totalPending: number;
  cases: (extra?: Record<string, string>) => string;
}) {
  // Map dashboard band names to filter values accepted by the API.
  const bandFilter: Record<string, string> = {
    "0-7 days": "0-7",
    "8-15 days": "8-15",
    "16-30 days": "16-30",
    "More than 30 days": "30+",
    // Legacy bands (still accepted by access.py).
    "0-7": "0-7",
    "8-30": "8-30",
    "31-60": "31-60",
    "61+": "61+",
  };
  const maxCount = Math.max(...ageing.map((a) => a.count), 1);
  return (
    <section className="mgmt-chart-section">
      <div className="panel-heading">
        <h2>Pending case ageing — by receipt date</h2>
      </div>
      <div className="mgmt-chart-body">
        <p style={{ fontSize: 11, color: "#69776E", marginBottom: 12 }}>
          Age calculated from received_at timestamp. Pending cases only. Does
          not imply an SLA breach unless the due date has also passed.
        </p>
        <div role="list" aria-label="Pending case ageing distribution">
          {ageing.map((a, i) => {
            const pct = totalPending > 0 ? (a.count / maxCount) * 100 : 0;
            const filterVal = bandFilter[a.name] || "";
            const isLast = i === ageing.length - 1;
            return (
              <div
                key={a.name}
                className={`ageing-row${isLast ? " overdue-row" : ""}`}
                role="listitem"
              >
                <span className="age-label">{a.name}</span>
                <div className="age-bar-wrap" aria-hidden="true">
                  <div
                    className="age-bar"
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className="age-count">
                  {filterVal && a.count > 0 ? (
                    <Link to={cases({ age: filterVal })}>{a.count}</Link>
                  ) : (
                    a.count
                  )}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

// ── Executive KPI strip ───────────────────────────────────────────────────

function KpiCard({
  label,
  value,
  sub,
  to,
  alert = false,
}: {
  label: string;
  value: number;
  sub?: string;
  to: string;
  alert?: boolean;
}) {
  return (
    <Link
      className={`mgmt-kpi-card${alert ? " alert" : ""}`}
      to={to}
      aria-label={`${label}: ${value.toLocaleString("en-IN")}. Click to view list.`}
    >
      <span className="kpi-label">{label}</span>
      <strong className="kpi-value">{value.toLocaleString("en-IN")}</strong>
      {sub && <span className="kpi-sub">{sub}</span>}
    </Link>
  );
}

// ── Bureau workload panel with overdue column ─────────────────────────────

function BureauWorkloadPanel({
  workload,
  cases,
}: {
  workload: {
    bureau__code: string;
    bureau__name?: string;
    count: number;
    overdue: number;
    approaching?: number;
    institutions?: number;
  }[];
  cases: (extra?: Record<string, string>) => string;
}) {
  if (!workload.length) {
    return (
      <section className="mgmt-chart-section">
        <div className="panel-heading">
          <h2>Current Bureau workload — open cases</h2>
        </div>
        <div className="mgmt-chart-body">
          <Empty>No open cases in this cohort.</Empty>
        </div>
      </section>
    );
  }
  return (
    <section className="mgmt-chart-section">
      <div className="panel-heading">
        <h2>Current Bureau workload — open cases</h2>
        <span style={{ fontSize: 11, color: "#69776E" }}>
          Current owning Bureau, not source Bureau
        </span>
      </div>
      <div
        aria-hidden="true"
        style={{ height: Math.max(120, workload.length * 36 + 40) }}
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={workload.map((b) => ({
              name: b.bureau__name || b.bureau__code,
              count: b.count,
              href: cases({ bureau: b.bureau__code, pending: "true" }),
            }))}
            layout="vertical"
            margin={{ top: 8, right: 50, left: 8, bottom: 4 }}
          >
            <CartesianGrid stroke="#e2e8e4" horizontal={false} />
            <XAxis type="number" allowDecimals={false} />
            <YAxis
              type="category"
              dataKey="name"
              width={150}
              tick={{ fontSize: 11, fill: "#1F2D26" }}
            />
            <Tooltip />
            <Bar
              isAnimationActive={false}
              name="Open cases"
              dataKey="count"
              fill="#2F7658"
              radius={[0, 4, 4, 0]}
              onClick={(entry) => {
                const row = (
                  (entry as unknown as { payload?: { href: string } }).payload
                );
                if (row?.href) window.location.assign(row.href);
              }}
            >
              <LabelList
                dataKey="count"
                position="right"
                fill="#1F2D26"
                fontSize={11}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div
        className="table-scroll mgmt-chart-body"
        role="region"
        aria-label="Bureau workload detail"
        tabIndex={0}
      >
        <table>
          <caption>Open cases by current Bureau</caption>
          <thead>
            <tr>
              <th>Bureau</th>
              <th>Open</th>
              <th>Overdue</th>
              <th>Approaching</th>
              <th>Institutions</th>
            </tr>
          </thead>
          <tbody>
            {workload.map((b) => (
              <tr key={b.bureau__code}>
                <th scope="row">{b.bureau__name || b.bureau__code}</th>
                <td>
                  <Link to={cases({ bureau: b.bureau__code, pending: "true" })}>
                    {b.count}
                  </Link>
                </td>
                <td>
                  {b.overdue > 0 ? (
                    <Link
                      to={cases({ bureau: b.bureau__code, overdue: "true" })}
                      style={{ color: "#a85f1a" }}
                    >
                      {b.overdue}
                    </Link>
                  ) : (
                    <span style={{ color: "#69776E" }}>0</span>
                  )}
                </td>
                <td>
                  {b.approaching != null && b.approaching > 0 ? (
                    <Link
                      to={cases({
                        bureau: b.bureau__code,
                        approaching: "true",
                      })}
                    >
                      {b.approaching}
                    </Link>
                  ) : (
                    <span style={{ color: "#69776E" }}>
                      {b.approaching ?? "—"}
                    </span>
                  )}
                </td>
                <td style={{ color: "#69776E" }}>{b.institutions ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

// ── Institution monitoring table ──────────────────────────────────────────

type InstitutionRow = {
  institution_id: string;
  institution__name: string;
  institution__permanent_id: string;
  institution__region: string;
  institution__district?: string;
  count: number;
  /** Number of distinct bureaus with active cases — may be absent in some API versions */
  bureaus?: number;
  bureau_names: string[];
  bureau_details?: { code: string; name: string; count: number }[];
  overdue: number;
  approaching?: number;
  escalations?: number;
  unresolved_escalations?: number;
  coordination: boolean;
};

function InstitutionMonitoringPanel({
  institutions,
  cases,
}: {
  institutions: InstitutionRow[];
  cases: (extra?: Record<string, string>, path?: string) => string;
}) {
  if (!institutions.length) {
    return (
      <section className="panel detail-card">
        <div className="panel-heading">
          <h2>Institution monitoring</h2>
        </div>
        <div className="card-body">
          <Empty>No institutions with active cases in this cohort.</Empty>
        </div>
      </section>
    );
  }
  return (
    <section className="panel detail-card">
      <div className="panel-heading">
        <h2>Institution monitoring</h2>
      </div>
      <p className="card-body muted">
        Highest active workloads in the selected receipt cohort. Coordination
        state uses all-time active ownership.
      </p>
      <div
        className="table-scroll"
        role="region"
        aria-label="Institution workload"
        tabIndex={0}
      >
        <table>
          <caption className="sr-only">Institution monitoring — pending workload</caption>
          <thead>
            <tr>
              <th>Institution / Permanent ID</th>
              <th>Region</th>
              <th>Active</th>
              <th>Current Bureaus</th>
              <th>Overdue</th>
              <th>Approaching</th>
              <th>Escalations</th>
              <th>Coordination</th>
            </tr>
          </thead>
          <tbody>
            {institutions.map((i) => {
              const esc = i.unresolved_escalations ?? i.escalations ?? 0;
              const approaching = i.approaching ?? 0;
              return (
                <tr key={i.institution_id}>
                  <td>
                    <Link to={`/institutions/${i.institution_id}`}>
                      {i.institution__name}
                    </Link>
                    <span className="table-sub">{i.institution__permanent_id}</span>
                  </td>
                  <td>
                    {i.institution__region}
                    {i.institution__district && (
                      <span className="table-sub">{i.institution__district}</span>
                    )}
                  </td>
                  <td>
                    <Link
                      to={cases({
                        institution: i.institution_id,
                        pending: "true",
                      })}
                    >
                      {i.count}
                    </Link>
                  </td>
                  <td>
                    {i.bureau_details
                      ? i.bureau_details.map((b) => `${b.code} (${b.count})`).join(" · ")
                      : i.bureau_names.join(" · ")}
                  </td>
                  <td>
                    {i.overdue > 0 ? (
                      <Link
                        to={cases({
                          institution: i.institution_id,
                          overdue: "true",
                        })}
                        style={{ color: "#a85f1a", fontWeight: 600 }}
                      >
                        {i.overdue}
                      </Link>
                    ) : (
                      <span style={{ color: "#69776E" }}>0</span>
                    )}
                  </td>
                  <td>
                    {approaching > 0 ? (
                      <Link
                        to={cases({
                          institution: i.institution_id,
                          approaching: "true",
                        })}
                      >
                        {approaching}
                      </Link>
                    ) : (
                      <span style={{ color: "#69776E" }}>0</span>
                    )}
                  </td>
                  <td>
                    {esc > 0 ? (
                      <Link
                        to={cases(
                          { institution: i.institution_id, state: "pending", pending: "true" },
                          "/escalations",
                        )}
                        style={{ color: "#a85f1a" }}
                      >
                        {esc}
                      </Link>
                    ) : (
                      <span style={{ color: "#69776E" }}>0</span>
                    )}
                  </td>
                  <td>
                    {i.coordination ? (
                      <Link
                        to={`/coordination/activity?institution=${i.institution_id}`}
                        style={{ color: "#a85f1a", fontWeight: 600 }}
                      >
                        Multi-Bureau ↗
                      </Link>
                    ) : (
                      <span style={{ color: "#69776E" }}>Single Bureau</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="card-body" style={{ paddingTop: 6 }}>
        <Link to="/institutions?with_cases=true">
          View full institution directory →
        </Link>
      </div>
    </section>
  );
}

// ── Management panels (coordinator/auditor only) ──────────────────────────

export function ManagementPanels({
  data: d,
  filters,
}: {
  data: Dashboard;
  filters: string;
}) {
  const m = d.management;
  if (!m) return null;

  function cases(extra: Record<string, string> = {}, path = "/cases") {
    const p = new URLSearchParams(filters);
    p.delete("page");
    Object.entries(extra).forEach(([k, v]) => (v ? p.set(k, v) : p.delete(k)));
    return `${path}?${p}`;
  }

  const geo = new URLSearchParams();
  const current = new URLSearchParams(filters);
  for (const k of ["institution", "region", "district", "district_exact"])
    if (current.get(k)) geo.set(k, current.get(k)!);

  function quarter(start: string, closed = false) {
    const endDate = new Date(`${start}T00:00:00Z`);
    endDate.setUTCMonth(endDate.getUTCMonth() + 3);
    endDate.setUTCDate(endDate.getUTCDate() - 1);
    const end = endDate.toISOString().slice(0, 10);
    return closed
      ? cases({
          disposed_from: [current.get("disposed_from") || start, start]
            .sort()
            .at(-1)!,
          disposed_to: [current.get("disposed_to") || end, end].sort()[0],
        })
      : cases({
          from: [current.get("from") || start, start].sort().at(-1)!,
          to: [current.get("to") || end, end].sort()[0],
        });
  }

  const cards: [string, number, string][] = [
    [
      "Institutions with cases",
      d.institutions,
      cases({ with_cases: "true" }, "/institutions"),
    ],
    ["Total cases received", d.total, cases()],
    ["Approaching deadlines", d.approaching, cases({ approaching: "true" })],
    ["Closed cases", d.disposed, cases({ closed: "true" })],
    [
      "Unresolved escalations",
      d.unresolved_escalations,
      cases({ state: "pending" }, "/escalations"),
    ],
    [
      "Institutions needing coordination — all time",
      d.coordination_institutions || 0,
      `/coordination/activity?${geo}`,
    ],
  ];

  return (
    <>
      <div className="home-summary">
        {cards.map(([label, value, url]) => (
          <Link className="home-stat" key={label} to={url}>
            <span>{label}</span>
            <strong>{value.toLocaleString("en-IN")}</strong>
          </Link>
        ))}
      </div>
      <p className="card-body muted">
        Selected receipt cohort. Closed share:{" "}
        {(d.closed_share * 100).toFixed(1)}%. Under process (under review +
        awaiting response): {(d.under_process ?? 0).toLocaleString("en-IN")}.
        This is not SLA compliance. Approaching: open deadlines from now through
        seven days; overdue cases are excluded.
      </p>

      {/* Institution monitoring table */}
      <InstitutionMonitoringPanel
        institutions={m.institutions}
        cases={cases}
      />

      {/* Charts row: Bureau workload + ageing */}
      <div className="home-charts">
        {/* Bureau workload */}
        <BureauWorkloadPanel workload={d.workload} cases={cases} />

        {/* Ageing distribution */}
        <AgeingPanel
          ageing={d.ageing}
          totalPending={d.pending}
          cases={cases}
        />

        <HorizontalDistribution
          title="Cases by region and district"
          caption="Received cases by region — selected cohort"
          rows={m.regions.map((r) => ({
            name: `${r.institution__region} / ${r.institution__district} (${r.institutions} institutions)`,
            count: r.count,
            url: cases({
              region: r.institution__region,
              district: r.institution__district,
              district_exact: "true",
            }),
          }))}
        />
        <HorizontalDistribution
          title="Case classifications — Unclassified included"
          caption="Classification distribution — selected cohort"
          rows={Object.entries(classifications).map(([value, name]) => ({
            name,
            count:
              m.classifications.find((c) => c.classification === value)
                ?.count || 0,
            url: cases({ classification: value }),
          }))}
        />
      </div>

      {/* Quarterly table */}
      <section className="panel detail-card" style={{ marginTop: 16 }}>
        <div className="panel-heading">
          <h2>Calendar-quarter receipts and closures</h2>
        </div>
        <div
          className="table-scroll card-body"
          role="region"
          aria-label="Quarterly trends"
          tabIndex={0}
        >
          {m.quarters.length ? (
            <table>
              <caption className="sr-only">
                Quarterly received and closed — date semantics differ between
                columns
              </caption>
              <thead>
                <tr>
                  <th>Quarter</th>
                  <th>Received (receipt date)</th>
                  <th>Closed (disposal date)</th>
                </tr>
              </thead>
              <tbody>
                {m.quarters.map((q) => (
                  <tr key={q.start}>
                    <th scope="row">{q.label}</th>
                    <td>
                      {q.received ? (
                        <Link to={quarter(q.start)}>{q.received}</Link>
                      ) : (
                        0
                      )}
                    </td>
                    <td>
                      {q.disposed ? (
                        <Link to={quarter(q.start, true)}>{q.disposed}</Link>
                      ) : (
                        0
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <Empty>No quarterly data in this cohort.</Empty>
          )}
        </div>
        <p style={{ fontSize: 11, color: "#69776E", padding: "6px 20px 14px" }}>
          Received: cases whose receipt date falls in the quarter. Closed:
          cases whose disposal date falls in the quarter. These are independent
          date dimensions.
        </p>
      </section>

      {/* Movement analytics */}
      <section className="panel detail-card" style={{ marginTop: 16 }}>
        <div className="panel-heading">
          <h2>Case movements — action period</h2>
          <Link to={`/movements?${filters}`} style={{ fontSize: 12 }}>
            View complete action history / CSV →
          </Link>
        </div>
        <p style={{ fontSize: 11, color: "#69776E", padding: "8px 20px 0" }}>
          Date filters apply to action timestamps here, not case receipt dates.
          Relationship decisions have one action record per linked case.
        </p>
        <div className="home-charts" style={{ padding: "12px 20px 16px" }}>
          <div
            className="table-scroll"
            role="region"
            aria-label="Movement event totals"
            tabIndex={0}
          >
            <table>
              <caption>Movement event counts — action timestamps</caption>
              <thead>
                <tr>
                  <th>Event</th>
                  <th>Action records</th>
                </tr>
              </thead>
              <tbody>
                {m.movement_counts.map((r) => (
                  <tr key={r.event}>
                    <th scope="row">{r.event.replaceAll("_", " ")}</th>
                    <td>
                      {r.count ? (
                        <Link to={cases({ event: r.event }, "/movements")}>
                          {r.count}
                        </Link>
                      ) : (
                        0
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div>
            <p
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: "#174B38",
                marginBottom: 8,
              }}
            >
              Recent actions
            </p>
            <ol className="timeline" style={{ paddingLeft: 16 }}>
              {m.recent_movements.map((a) => (
                <li key={a.id} style={{ marginBottom: 8 }}>
                  <div style={{ fontSize: 12 }}>
                    <Link to={`/cases/${a.case_id}`}>{a.reference}</Link> ·{" "}
                    {a.event.replaceAll("_", " ")} ·{" "}
                    {new Date(a.created_at).toLocaleString("en-IN")}
                    <p style={{ color: "#69776E", fontSize: 11, margin: "2px 0 0" }}>
                      {a.reason}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </section>
    </>
  );
}

// ── Movements page ────────────────────────────────────────────────────────

export function MovementsPage() {
  const [params, setParams] = useSearchParams();
  const { data, error } = usePoll<Page<Movement>>(
    `/api/movements?${params}`,
    5000,
  );
  return (
    <>
      <Heading
        eyebrow="AUTHORITATIVE CASE ACTIONS"
        title="Case movements"
        subtitle="Action dates are independent of complaint receipt dates. Current case permissions apply."
      >
        <a className="button secondary" href={`/api/movements.csv?${params}`}>
          Download movement CSV
        </a>
      </Heading>
      <ErrorBox message={error} />
      {!data && !error && <Loading />}
      {data && (
        <section className="panel">
          <div
            className="table-scroll"
            role="region"
            aria-label="Case actions"
            tabIndex={0}
          >
            <table>
              <thead>
                <tr>
                  <th>Case / Institution</th>
                  <th>Action</th>
                  <th>When / Actor</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <Link to={`/cases/${a.case_id}`}>{a.reference}</Link>
                      <span className="table-sub">{a.institution}</span>
                    </td>
                    <td>{a.event.replaceAll("_", " ")}</td>
                    <td>
                      {new Date(a.created_at).toLocaleString("en-IN")} ·{" "}
                      {a.actor}<span className="table-sub">Bureau at action: {a.bureau_at_action || "Unknown (historical)"}</span>
                    </td>
                    <td>{a.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination data={data} params={params} setParams={setParams} />
        </section>
      )}
    </>
  );
}
