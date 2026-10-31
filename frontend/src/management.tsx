import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  LabelList,
  Tooltip,
} from "recharts";
import { date, classifications } from "./api";
import type { Dashboard, Case, Page, Movement } from "./api";
import { usePoll } from "./imports";
import { Heading, ErrorBox, Loading, Empty, Pagination, Badge } from "./ui";

type Notice = {
  institution_id: string;
  institution__name: string;
  institution__permanent_id: string;
  institution__region: string;
  institution__district: string;
  count: number;
  bureaus: number;
  bureau_details: { name: string; count: number }[];
  officers: { name: string; count: number }[];
  cases: Case[];
  reviewed_relationships: number;
};
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

type ChartRow = { name: string; count: number; url: string };
function Distribution({ title, rows }: { title: string; rows: ChartRow[] }) {
  const navigate = useNavigate();
  return (
    <section className="panel home-chart">
      <div className="panel-heading">
        <h2>{title}</h2>
      </div>
      {rows.length ? (
        <>
          <div style={{ height: 240 }} aria-hidden="true">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={rows}
                margin={{ top: 25, right: 20, bottom: 15, left: 0 }}
              >
                <XAxis dataKey="name" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar
                  dataKey="count"
                  fill="#147b3b"
                  cursor="pointer"
                  onClick={(value) => {
                    const row =
                      (value as unknown as { payload?: ChartRow }).payload ||
                      (value as unknown as ChartRow);
                    if (row.url) navigate(row.url);
                  }}
                >
                  <LabelList dataKey="count" position="top" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div
            className="table-scroll"
            role="region"
            aria-label={`${title} data`}
            tabIndex={0}
          >
            <table>
              <caption>{title} — selected receipt cohort</caption>
              <thead>
                <tr>
                  <th>Group</th>
                  <th>Cases</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.name}>
                    <th>{r.name}</th>
                    <td>{r.count ? <Link to={r.url}>{r.count}</Link> : 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <Empty>No cases in this cohort.</Empty>
      )}
    </section>
  );
}

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
        {(d.closed_share * 100).toFixed(1)}%. This is not SLA compliance.
        Approaching: open deadlines from now through seven days; overdue cases
        are excluded.
      </p>
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
            <thead>
              <tr>
                <th>Institution / Permanent ID</th>
                <th>Region</th>
                <th>Active cases</th>
                <th>Current Bureaus</th>
                <th>Overdue</th>
                <th>Unresolved escalations</th>
                <th>Coordination</th>
              </tr>
            </thead>
            <tbody>
              {m.institutions.map((i) => (
                <tr key={i.institution_id}>
                  <td>
                    <Link to={`/institutions/${i.institution_id}`}>
                      {i.institution__name}
                    </Link>
                    <span className="table-sub">
                      {i.institution__permanent_id}
                    </span>
                  </td>
                  <td>{i.institution__region}</td>
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
                  <td>{i.bureau_names.join(" · ")}</td>
                  <td>
                    <Link
                      to={cases({
                        institution: i.institution_id,
                        overdue: "true",
                      })}
                    >
                      {i.overdue}
                    </Link>
                  </td>
                  <td>
                    <Link
                      to={cases(
                        { institution: i.institution_id, state: "pending" },
                        "/escalations",
                      )}
                    >
                      {i.escalations}
                    </Link>
                  </td>
                  <td>
                    {i.coordination
                      ? "Review required (all time)"
                      : "Single active Bureau"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <div className="home-charts">
        <Distribution
          title="Cases by region and district"
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
        <Distribution
          title="Case classifications — Unclassified included"
          rows={Object.entries(classifications).map(([value, name]) => ({
            name,
            count:
              m.classifications.find((c) => c.classification === value)
                ?.count || 0,
            url: cases({ classification: value }),
          }))}
        />
        <Distribution
          title="Complaint categories"
          rows={d.categories.map((r) => ({
            name: r.category,
            count: r.count,
            url: cases({ category: r.category }),
          }))}
        />
        <section className="panel home-chart">
          <div className="panel-heading">
            <h2>Calendar-quarter receipts and closures</h2>
          </div>
          <div
            className="table-scroll"
            role="region"
            aria-label="Quarter trends"
            tabIndex={0}
          >
            <table>
              <thead>
                <tr>
                  <th>Quarter</th>
                  <th>Received</th>
                  <th>Closed</th>
                </tr>
              </thead>
              <tbody>
                {m.quarters.map((q) => (
                  <tr key={q.start}>
                    <th>{q.label}</th>
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
          </div>
        </section>
      </div>
      <section className="panel detail-card">
        <div className="panel-heading">
          <h2>Case movements — action period</h2>
          <Link to={`/movements?${filters}`}>
            View complete action history / CSV →
          </Link>
        </div>
        <p className="card-body muted">
          Date filters apply to action timestamps here, not case receipt dates.
          Relationship decisions have one action record per linked case.
        </p>
        <div
          className="table-scroll"
          role="region"
          aria-label="Movement totals"
          tabIndex={0}
        >
          <table>
            <thead>
              <tr>
                <th>Event</th>
                <th>Action records</th>
              </tr>
            </thead>
            <tbody>
              {m.movement_counts.map((r) => (
                <tr key={r.event}>
                  <th>{r.event.replaceAll("_", " ")}</th>
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
        <ol className="timeline">
          {m.recent_movements.map((a) => (
            <li key={a.id}>
              <div>
                <Link to={`/cases/${a.case_id}`}>{a.reference}</Link> ·{" "}
                {a.event.replaceAll("_", " ")} ·{" "}
                {new Date(a.created_at).toLocaleString("en-IN")}
                <p>{a.reason}</p>
              </div>
            </li>
          ))}
        </ol>
      </section>
    </>
  );
}

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
                      {a.actor}
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
