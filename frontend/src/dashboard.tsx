import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from "recharts";
import {
  ArrowRight,
  Clock,
  WarningCircle,
  Intersect,
  Plus,
  Tray,
  CaretDown,
} from "@phosphor-icons/react";
import { date, categories } from "./api";
import type { Dashboard, Options, User } from "./api";
import { usePoll } from "./imports";

function validDashboard(value: unknown): boolean {
  if (!value || typeof value !== "object") return false;
  const d = value as Dashboard;
  const count = (n: unknown) =>
    typeof n === "number" && Number.isFinite(n) && n >= 0;
  return (
    [d.pending, d.overdue, d.total].every(count) &&
    typeof d.generated_at === "string" &&
    Array.isArray(d.attention) &&
    d.attention.every(
      (c) =>
        typeof c.id === "string" &&
        typeof c.reference === "string" &&
        typeof c.summary === "string" &&
        typeof c.bureau === "string" &&
        typeof c.due_at === "string" &&
        typeof c.institution?.name === "string",
    ) &&
    Array.isArray(d.trend) &&
    d.trend.every(
      (t) =>
        typeof t.month === "string" && count(t.received) && count(t.disposed),
    ) &&
    Array.isArray(d.workload) &&
    d.workload.every(
      (b) => typeof b.bureau__code === "string" && count(b.count),
    ) &&
    Array.isArray(d.active_categories) &&
    d.active_categories.every(
      (c) => typeof c.category === "string" && count(c.count),
    ) &&
    (d.overlap_reviews === undefined || count(d.overlap_reviews)) &&
    (d.coordination_notices === undefined ||
      (Array.isArray(d.coordination_notices) &&
        d.coordination_notices.every(
          (n) =>
            typeof n.institution_id === "string" &&
            typeof n.institution__name === "string" &&
            count(n.bureaus) &&
            count(n.count),
        )))
  );
}
const monthName = (month: string) =>
  new Date(`${month}-01T00:00:00`).toLocaleDateString("en-IN", {
    month: "short",
    year: "2-digit",
  });
export function DashboardHome({
  user,
  options,
}: {
  user: User;
  options: Options;
}) {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const { data: d, error } = usePoll<Dashboard>(
    `/api/dashboard?${params}`,
    5000,
    0,
    validDashboard,
  );
  const coordinator = ["coordinator", "auditor"].includes(user.role),
    writable = ["coordinator", "officer"].includes(user.role);
  const bureauName = (code: string) =>
    options.bureaus.find((b) => b.code === code)?.name || code;
  function change(key: string, value: string) {
    const q = new URLSearchParams(params);
    if (value) q.set(key, value);
    else q.delete(key);
    q.delete("page");
    setParams(q);
  }
  function cases(values: Record<string, string> = {}) {
    const q = new URLSearchParams(params);
    q.delete("page");
    Object.entries(values).forEach(([k, v]) => (v ? q.set(k, v) : q.delete(k)));
    return `/cases?${q}`;
  }
  function reviews(institution?: string) {
    const q = new URLSearchParams(params);
    q.delete("page");
    q.set("decision", "pending");
    if (institution) q.set("institution", institution);
    return `/coordination?${q}`;
  }
  function monthCases(month: string, closed = false) {
    const q = new URLSearchParams(params);
    q.delete("page");
    const start = `${month}-01`;
    const end = `${month}-${new Date(Number(month.slice(0, 4)), Number(month.slice(5)), 0).getDate()}`;
    const startKey = closed ? "disposed_from" : "from";
    const endKey = closed ? "disposed_to" : "to";
    q.set(
      startKey,
      q.get(startKey) && q.get(startKey)! > start ? q.get(startKey)! : start,
    );
    q.set(endKey, q.get(endKey) && q.get(endKey)! < end ? q.get(endKey)! : end);
    if (closed && !q.get("status")) q.set("status", "disposed");
    return `/cases?${q}`;
  }
  const work = coordinator
    ? d?.workload.map((b) => ({
        name: bureauName(b.bureau__code),
        count: b.count,
        href: cases({ bureau: b.bureau__code, pending: "true", status: "" }),
      }))
    : d?.active_categories.map((c) => ({
        name: c.category,
        count: c.count,
        href: cases({ category: c.category, pending: "true", status: "" }),
      }));
  return (
    <div className="home-dashboard">
      <div className="home-heading">
        <div>
          <p className="eyebrow">AICTE · COMPLAINT COORDINATION</p>
          <h1>Complaint Monitoring Dashboard</h1>
          <p>See what needs attention. Help the right bureaus work together.</p>
        </div>
        <div className="actions">
          {writable && (
            <>
              <Link className="button" to="/cases/new">
                <Plus size={17} />
                Register case
              </Link>
              <Link className="button secondary" to="/imports">
                <Tray size={17} />
                Upload Excel
              </Link>
            </>
          )}
          <Link className="text-button" to={`/reports?${params}`}>
            View report <ArrowRight size={16} />
          </Link>
        </div>
      </div>
      <div className="home-filterbar">
        <label>
          Bureau
          <select
            value={params.get("bureau") || ""}
            onChange={(e) => change("bureau", e.target.value)}
          >
            <option value="">
              {coordinator ? "All bureaus" : "My bureau"}
            </option>
            {options.bureaus.map((b) => (
              <option value={b.code} key={b.code}>
                {b.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Received from
          <input
            type="date"
            value={params.get("from") || ""}
            onChange={(e) => change("from", e.target.value)}
          />
        </label>
        <label>
          Received to
          <input
            type="date"
            value={params.get("to") || ""}
            onChange={(e) => change("to", e.target.value)}
          />
        </label>
        <details className="home-more">
          <summary>
            More filters <CaretDown size={13} />
          </summary>
          <div>
            <label>
              Category
              <select
                value={params.get("category") || ""}
                onChange={(e) => change("category", e.target.value)}
              >
                <option value="">All categories</option>
                {categories.map((c) => (
                  <option key={c}>{c}</option>
                ))}
              </select>
            </label>
            <label>
              Region
              <select
                value={params.get("region") || ""}
                onChange={(e) => change("region", e.target.value)}
              >
                <option value="">All regions</option>
                {options.regions.map((r) => (
                  <option key={r}>{r}</option>
                ))}
              </select>
            </label>
          </div>
        </details>
        {params.size > 0 && (
          <button className="text-button" onClick={() => setParams({})}>
            Clear filters
          </button>
        )}
      </div>
      {error && (
        <div className="error" role="alert">
          {error}
          {d && " Showing the last successful update."}
        </div>
      )}
      {!d && !error && (
        <p role="status" className="loading">
          Loading complaints…
        </p>
      )}
      {d && (
        <>
          <div className={`home-metrics ${coordinator ? "" : "officer"}`}>
            <button
              className="home-stat"
              onClick={() =>
                navigate(cases({ pending: "true", overdue: "", status: "" }))
              }
            >
              <span>
                <Clock size={19} />
                Open complaints
              </span>
              <strong>{d.pending.toLocaleString("en-IN")}</strong>
              <small>Waiting for action, including overdue complaints.</small>
              <ArrowRight className="stat-arrow" size={20} />
            </button>
            <button
              className="home-stat overdue"
              onClick={() =>
                navigate(cases({ overdue: "true", pending: "", status: "" }))
              }
            >
              <span>
                <WarningCircle size={19} />
                Overdue complaints
              </span>
              <strong>{d.overdue.toLocaleString("en-IN")}</strong>
              <small>Part of open complaints. The deadline has passed.</small>
              <ArrowRight className="stat-arrow" size={20} />
            </button>
            {coordinator && (
              <button className="home-stat" onClick={() => navigate(reviews())}>
                <span>
                  <Intersect size={19} />
                  Possible overlaps
                </span>
                <strong>
                  {(d.overlap_reviews || 0).toLocaleString("en-IN")}
                </strong>
                <small>
                  Case pairs to check. These are not confirmed duplicates.
                </small>
                <ArrowRight className="stat-arrow" size={20} />
              </button>
            )}
          </div>
          <section
            className="panel home-attention"
            aria-labelledby="attention-title"
          >
            <div className="home-section-heading">
              <div>
                <h2 id="attention-title">Cases needing attention</h2>
                <p>
                  Open complaints, earliest deadline first. Showing up to eight.
                </p>
              </div>
              <Link
                className="text-button"
                to={cases({ pending: "true", status: "" })}
              >
                View all open complaints <ArrowRight size={16} />
              </Link>
            </div>
            {d.attention.length ? (
              <div
                className="table-wrap"
                role="region"
                aria-label="Cases needing attention list"
                tabIndex={0}
              >
                <table>
                  <thead>
                    <tr>
                      <th>Complaint</th>
                      <th>Institution</th>
                      <th>Responsible bureau</th>
                      <th>Deadline</th>
                      <th>
                        <span className="sr-only">Action</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.attention.map((c) => (
                      <tr key={c.id}>
                        <td>
                          <strong>{c.reference}</strong>
                          <span className="attention-summary" title={c.summary}>
                            {c.summary}
                          </span>
                        </td>
                        <td>{c.institution.name}</td>
                        <td>{bureauName(c.bureau)}</td>
                        <td>
                          <span className={c.overdue ? "deadline-overdue" : ""}>
                            {date(c.due_at)}
                          </span>
                          {c.overdue && (
                            <small className="deadline-overdue">Overdue</small>
                          )}
                        </td>
                        <td>
                          <Link
                            className="button secondary small"
                            aria-label={`Open case ${c.reference}`}
                            to={`/cases/${c.id}`}
                          >
                            Open case <ArrowRight size={14} />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="home-empty">
                No open complaints match these filters.
              </div>
            )}
          </section>
          {coordinator && (
            <section
              className="panel home-coordination"
              aria-labelledby="coordination-title"
            >
              <div className="home-section-heading">
                <div>
                  <h2 id="coordination-title">Needs coordination</h2>
                  <p>
                    These institutions have open complaints with more than one
                    bureau.
                  </p>
                </div>
                <Link className="text-button" to={reviews()}>
                  Review possible overlaps <ArrowRight size={16} />
                </Link>
              </div>
              {d.coordination_notices?.length ? (
                <div className="coordination-cards">
                  {d.coordination_notices.slice(0, 3).map((n) => (
                    <article key={n.institution_id}>
                      <div className="coordination-icon">
                        <Intersect size={22} />
                      </div>
                      <div>
                        <h3>{n.institution__name}</h3>
                        <p>
                          {n.count} open complaints · {n.bureaus} bureaus
                        </p>
                        <div className="actions">
                          <Link
                            to={cases({
                              institution: n.institution_id,
                              pending: "true",
                              status: "",
                            })}
                          >
                            View complaints →
                          </Link>
                          <Link to={reviews(n.institution_id)}>
                            Review overlaps →
                          </Link>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="home-empty">
                  No institutions need cross-bureau coordination within these
                  filters.
                </div>
              )}
              <p className="home-guidance">
                Check the case history, compare the evidence, then record the
                decision. Each complaint keeps its own history.
              </p>
            </section>
          )}
          <div className="home-charts">
            <section className="panel home-chart">
              <div className="home-section-heading">
                <div>
                  <h2>Complaints received and closed</h2>
                  <p>Monthly counts within your filters.</p>
                </div>
                <div className="home-legend">
                  <span>
                    <i />
                    Received
                  </span>
                  <span>
                    <i />
                    Closed
                  </span>
                </div>
              </div>
              {d.trend.length ? (
                <>
                  <div className="home-chart-canvas">
                    <ResponsiveContainer>
                      <BarChart
                        data={d.trend}
                        margin={{ top: 28, right: 20, bottom: 4, left: 0 }}
                      >
                        <CartesianGrid stroke="#d0e6d2" vertical={false} />
                        <XAxis dataKey="month" tickFormatter={monthName} />
                        <YAxis allowDecimals={false} />
                        <Tooltip
                          labelFormatter={(label) => monthName(String(label))}
                        />
                        <Bar
                          isAnimationActive={false}
                          name="Received"
                          dataKey="received"
                          fill="#138808"
                          radius={[3, 3, 0, 0]}
                          onClick={(entry) =>
                            entry.payload.received > 0 &&
                            navigate(monthCases(String(entry.payload.month)))
                          }
                        >
                          <LabelList
                            dataKey="received"
                            position="top"
                            fill="#145526"
                            fontSize={11}
                          />
                        </Bar>
                        <Bar
                          isAnimationActive={false}
                          name="Closed"
                          dataKey="disposed"
                          fill="#e87500"
                          radius={[3, 3, 0, 0]}
                          onClick={(entry) =>
                            navigate(
                              monthCases(String(entry.payload.month), true),
                            )
                          }
                        >
                          <LabelList
                            dataKey="disposed"
                            position="top"
                            fill="#a74400"
                            fontSize={11}
                          />
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <details className="home-chart-data">
                    <summary>View monthly values and complaints</summary>
                    <table>
                      <caption className="sr-only">
                        Monthly received and closed complaints
                      </caption>
                      <thead>
                        <tr>
                          <th>Month</th>
                          <th>Received</th>
                          <th>Closed</th>
                        </tr>
                      </thead>
                      <tbody>
                        {d.trend.map((t) => (
                          <tr key={t.month}>
                            <th>{monthName(t.month)}</th>
                            <td>
                              {t.received > 0 ? (
                                <Link
                                  to={monthCases(t.month)}
                                  aria-label={`${monthName(t.month)} received complaints: ${t.received}`}
                                >
                                  {t.received}
                                </Link>
                              ) : (
                                0
                              )}
                            </td>
                            <td>
                              {t.disposed > 0 ? (
                                <Link
                                  to={monthCases(t.month, true)}
                                  aria-label={`${monthName(t.month)} closed complaints: ${t.disposed}`}
                                >
                                  {t.disposed}
                                </Link>
                              ) : (
                                0
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </details>
                </>
              ) : (
                <div className="home-empty">
                  No complaints were received in this period.
                </div>
              )}
            </section>
            <section className="panel home-chart">
              <div className="home-section-heading">
                <div>
                  <h2>
                    {coordinator
                      ? "Open complaints by bureau"
                      : "Open complaints by category"}
                  </h2>
                  <p>Where work is waiting for action.</p>
                </div>
              </div>
              {work?.length ? (
                <>
                  <div className="home-chart-canvas">
                    <ResponsiveContainer>
                      <BarChart
                        data={work}
                        layout="vertical"
                        margin={{ top: 8, right: 40, left: 8, bottom: 4 }}
                      >
                        <CartesianGrid stroke="#d0e6d2" horizontal={false} />
                        <XAxis type="number" allowDecimals={false} />
                        <YAxis
                          type="category"
                          dataKey="name"
                          width={140}
                          tick={{ fontSize: 11 }}
                          tickFormatter={(name) =>
                            String(name).length > 24
                              ? String(name).slice(0, 22) + "…"
                              : String(name)
                          }
                        />
                        <Tooltip />
                        <Bar
                          isAnimationActive={false}
                          name="Open complaints"
                          dataKey="count"
                          fill="#138808"
                          radius={[0, 3, 3, 0]}
                          onClick={(entry) =>
                            navigate(String(entry.payload.href))
                          }
                        >
                          <LabelList
                            dataKey="count"
                            position="right"
                            fill="#145526"
                            fontSize={12}
                          />
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <div
                    className="home-work-links"
                    aria-label="Open complaint chart values"
                  >
                    {work.map((w) => (
                      <Link to={w.href} key={w.name}>
                        <span>{w.name}</span>
                        <strong>{w.count}</strong>
                        <ArrowRight size={14} />
                      </Link>
                    ))}
                  </div>
                </>
              ) : (
                <div className="home-empty">
                  No open complaints match these filters.
                </div>
              )}
            </section>
          </div>
          <div className="home-footer-note">
            <span>
              Updated{" "}
              {new Date(d.generated_at).toLocaleTimeString("en-IN", {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })}{" "}
              · Refreshes every 5 seconds
            </span>
            <span>
              30-day demonstration deadline; not an official AICTE rule.
            </span>
          </div>
        </>
      )}
    </div>
  );
}
