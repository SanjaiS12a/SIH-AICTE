import { useState } from "react";
import { CoordinationNotices } from "./management";
import type { FormEvent } from "react";
import {
  Link,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { ArrowLeft, Plus, ArrowClockwise } from "@phosphor-icons/react";
import {
  api,
  ApiError,
  categories,
  date,
  labels,
  statuses,
  classifications,
} from "./api";
import type {
  Case,
  Dashboard,
  Institution,
  InstitutionAction,
  InstitutionProfile,
  Options,
  Overlap,
  Page,
  User,
} from "./api";
import { ExportButton, Report, usePoll } from "./imports";
import { validDashboard } from "./dashboard-data";
import {
  Badge,
  CaseTable,
  Empty,
  ErrorBox,
  Heading,
  Loading,
  Pagination,
} from "./ui";

function validProfile(value: unknown): boolean {
  const p = value as InstitutionProfile | null;
  return (
    !!p &&
    typeof p.id === "string" &&
    typeof p.name === "string" &&
    typeof p.permanent_id === "string" &&
    typeof p.region === "string" &&
    typeof p.district === "string" &&
    [p.address, p.official_email, p.official_phone].every(
      (x) => typeof x === "string",
    ) &&
    Number.isInteger(p.version) &&
    p.version > 0 &&
    p.history_period === "all_time" &&
    ["all_bureaus", "current_bureau"].includes(p.scope) &&
    !!p.overview &&
    [
      p.overview.total,
      p.overview.open,
      p.overview.overdue,
      p.overview.closed,
      p.overview.unresolved_escalations,
    ].every((x) => typeof x === "number") &&
    Array.isArray(p.classifications) &&
    p.classifications.every(
      (row) =>
        row.classification in classifications &&
        Number.isInteger(row.count) &&
        row.count >= 0,
    ) &&
    Array.isArray(p.bureaus) &&
    p.bureaus.every(
      (b) =>
        typeof b.bureau__code === "string" &&
        typeof b.bureau__name === "string" &&
        typeof b.count === "number",
    )
  );
}

function validPage(value: unknown): boolean {
  const p = value as Page<unknown> | null;
  return (
    !!p &&
    typeof p.count === "number" &&
    Array.isArray(p.results) &&
    (p.next === null || typeof p.next === "string") &&
    (p.previous === null || typeof p.previous === "string")
  );
}

export function InstitutionDirectory({
  user,
  options,
}: {
  user: User;
  options: Options;
}) {
  const [params, setParams] = useSearchParams();
  const { data, error } = usePoll<Page<Institution>>(
    `/api/institution-registry?${params}`,
    0,
    0,
    validPage,
  );
  function change(key: string, value: string) {
    const next = new URLSearchParams(params);
    value ? next.set(key, value) : next.delete(key);
    next.delete("page");
    setParams(next, { replace: true });
  }
  return (
    <>
      <Heading
        eyebrow="INSTITUTION REGISTRY"
        title="Institutions"
        subtitle="Find an institution and open its consolidated case history."
      >
        {user.role === "coordinator" && (
          <Link className="button" to="/institutions/new">
            <Plus size={17} />
            Register institution
          </Link>
        )}
      </Heading>
      <section className="panel" aria-label="Institution directory">
        <div className="institution-filters">
          <label className="institution-search">
            Search institutions
            <input
              type="search"
              placeholder="Institution name or Permanent ID"
              value={params.get("q") || ""}
              maxLength={200}
              onChange={(e) => change("q", e.target.value)}
            />
          </label>
          <label>
            Region
            <select
              value={params.get("region") || ""}
              onChange={(e) => change("region", e.target.value)}
            >
              <option value="">All regions</option>
              {options.regions.map((region) => (
                <option key={region}>{region}</option>
              ))}
            </select>
          </label>
          <label>
            District
            <input
              type="search"
              placeholder="Search district"
              value={params.get("district") || ""}
              maxLength={80}
              onChange={(e) => change("district", e.target.value)}
            />
          </label>
          <label>
            Responsible bureau
            <select
              value={params.get("bureau") || ""}
              onChange={(e) => change("bureau", e.target.value)}
            >
              <option value="">All authorized bureaus</option>
              {options.bureaus.map((b) => (
                <option key={b.code} value={b.code}>
                  {b.name}
                </option>
              ))}
            </select>
          </label>
          <button
            className="button secondary small"
            onClick={() => setParams({})}
          >
            Clear filters
          </button>
        </div>
        <ErrorBox message={error} />
        {!data && !error && <Loading />}
        {data && (
          <>
            {data.results.length ? (
              <div
                className="table-scroll"
                role="region"
                aria-label="Institution directory table"
                tabIndex={0}
              >
                <table>
                  <thead>
                    <tr>
                      <th>Institution</th>
                      <th>Permanent ID</th>
                      <th>Region</th>
                      <th>District</th>
                      <th>Profile</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.results.map((i) => (
                      <tr key={i.id}>
                        <td>
                          <Link
                            className="institution-link"
                            to={`/institutions/${i.id}`}
                          >
                            {i.name}
                          </Link>
                        </td>
                        <td>{i.permanent_id}</td>
                        <td>{i.region}</td>
                        <td>{i.district}</td>
                        <td>
                          <Link
                            className="text-button"
                            to={`/institutions/${i.id}`}
                            aria-label={`Open profile for ${i.name}`}
                          >
                            Open profile →
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <Empty>No institutions match these filters.</Empty>
            )}
            <Pagination data={data} params={params} setParams={setParams} />
          </>
        )}
      </section>
    </>
  );
}

export function InstitutionEditor({ user }: { user: User }) {
  const { id } = useParams();
  const [refresh, setRefresh] = useState(0);
  const permitted = user.role === "coordinator";
  const { data, error } = usePoll<InstitutionProfile>(
    permitted && id ? `/api/institutions/${id}` : null,
    0,
    refresh,
    validProfile,
  );
  if (!permitted)
    return (
      <>
        <ErrorBox message="Only coordinators can register or edit institutions. Your access is read-only." />
        <Link to={id ? `/institutions/${id}` : "/institutions"}>
          Return to institutions
        </Link>
      </>
    );
  return (
    <>
      <Link
        className="back-link"
        to={id ? `/institutions/${id}` : "/institutions"}
      >
        <ArrowLeft size={16} />
        Back to {id ? "institution profile" : "institutions"}
      </Link>
      <Heading
        eyebrow="CANONICAL INSTITUTION IDENTITY"
        title={id ? "Edit institution" : "Register institution"}
        subtitle="Permanent IDs cannot be changed. Every registration and profile edit is audited."
      />
      <ErrorBox message={error} />
      {id && !data && !error && <Loading />}
      {(!id || data) && (
        <InstitutionForm
          key={`${id || "new"}-${refresh}`}
          institution={data}
          onReload={() => setRefresh((n) => n + 1)}
        />
      )}
    </>
  );
}

function InstitutionForm({
  institution,
  onReload,
}: {
  institution: InstitutionProfile | null;
  onReload: () => void;
}) {
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [conflict, setConflict] = useState(false);
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const values: Record<string, string | number> = Object.fromEntries(
      [...form].map(([key, value]) => [key, String(value).trim()]),
    );
    if (institution) {
      delete values.permanent_id;
      values.expected_version = institution.version;
    }
    setBusy(true);
    setError("");
    try {
      const saved = await api<Institution>(
        institution
          ? `/api/institutions/${institution.id}`
          : "/api/institution-registry",
        {
          method: institution ? "PATCH" : "POST",
          body: JSON.stringify(values),
        },
      );
      navigate(`/institutions/${saved.id}`, {
        state: { institutionSaved: true },
      });
    } catch (e) {
      if (e instanceof ApiError && e.status === 409 && institution) {
        setConflict(true);
        setError(
          "This institution was changed by another user. Your entries are still here. Reload the latest profile before editing again; reloading discards these unsaved entries.",
        );
      } else setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form
      className="panel form-panel"
      onSubmit={save}
      aria-label="Institution form"
    >
      <ErrorBox message={error} />
      {conflict && (
        <button type="button" className="button secondary" onClick={onReload}>
          Reload latest profile (discard unsaved entries)
        </button>
      )}
      {institution && (
        <p className="muted">
          Editing version {institution.version}. A concurrent change will be
          rejected.
        </p>
      )}
      <div className="form-grid">
        <label className="wide">
          Institution name
          <input
            name="name"
            required
            maxLength={180}
            defaultValue={institution?.name || ""}
          />
        </label>
        <label>
          AICTE Permanent ID
          <input
            name="permanent_id"
            required
            readOnly={!!institution}
            maxLength={40}
            defaultValue={institution?.permanent_id || ""}
          />
          <small>Unique and permanent once registered.</small>
        </label>
        <label>
          Region
          <input
            name="region"
            required
            maxLength={60}
            defaultValue={institution?.region || ""}
          />
        </label>
        <label>
          District
          <input
            name="district"
            required
            maxLength={80}
            defaultValue={institution?.district || ""}
          />
        </label>
        <label>
          Official email (optional)
          <input
            name="official_email"
            type="email"
            maxLength={254}
            defaultValue={institution?.official_email || ""}
          />
        </label>
        <label>
          Official phone (optional)
          <input
            name="official_phone"
            type="tel"
            maxLength={30}
            defaultValue={institution?.official_phone || ""}
          />
        </label>
        <label className="wide">
          Official address (optional)
          <textarea
            name="address"
            rows={3}
            maxLength={500}
            defaultValue={institution?.address || ""}
          />
        </label>
        <label className="wide">
          Reason for {institution ? "edit" : "registration"}
          <textarea name="reason" required maxLength={4000} rows={3} />
        </label>
      </div>
      <div className="form-actions">
        <Link
          className="button secondary"
          to={institution ? `/institutions/${institution.id}` : "/institutions"}
        >
          Cancel
        </Link>
        <button disabled={busy || conflict}>
          {busy
            ? "Saving…"
            : institution
              ? "Save institution"
              : "Register institution"}
        </button>
      </div>
    </form>
  );
}

export function InstitutionProfilePage({
  user,
  options,
}: {
  user: User;
  options: Options;
}) {
  const { id } = useParams();
  const [params] = useSearchParams();
  const [refresh, setRefresh] = useState(0);
  const { state } = useLocation();
  const { data: institution, error } = usePoll<InstitutionProfile>(
    `/api/institutions/${id}`,
    0,
    refresh,
    validProfile,
  );
  const section = params.get("section") || "overview";
  const base = `/institutions/${id}`;
  return (
    <>
      <Link className="back-link no-print" to="/institutions">
        <ArrowLeft size={16} />
        Back to institutions
      </Link>
      <ErrorBox message={error} />
      {!institution && !error && <Loading />}
      {institution && (
        <>
          <Heading
            eyebrow={institution.permanent_id}
            title={institution.name}
            subtitle={`${institution.region} · ${institution.district}`}
          >
            <button
              className="button secondary no-print"
              onClick={() => setRefresh((n) => n + 1)}
            >
              <ArrowClockwise size={16} />
              Refresh profile
            </button>
            {user.role === "coordinator" && (
              <Link className="button no-print" to={`${base}/edit`}>
                Edit institution
              </Link>
            )}
          </Heading>
          {state?.institutionSaved && (
            <p className="success" role="status">
              Institution saved. The change has been recorded in the audit
              history.
            </p>
          )}
          <div className="info-note">
            <span>
              <strong>All-time institution profile.</strong>{" "}
              {institution.scope === "all_bureaus"
                ? "Cases across all authorized bureaus."
                : "Cases and totals are limited to your current bureau."}{" "}
              Dashboard date filters do not change these totals.
            </span>
          </div>
          <nav
            className="tabs institution-tabs no-print"
            aria-label="Institution sections"
          >
            {["overview", "cases", "history", "coordination", "reports"].map(
              (tab) => (
                <Link
                  key={tab}
                  className={section === tab ? "active" : ""}
                  aria-current={section === tab ? "page" : undefined}
                  to={`${base}?section=${tab}`}
                >
                  {tab[0].toUpperCase() + tab.slice(1)}
                </Link>
              ),
            )}
          </nav>
          {section === "overview" && (
            <InstitutionOverview institution={institution} />
          )}
          {section === "cases" && (
            <InstitutionCases
              key={id}
              id={id!}
              options={options}
              refresh={refresh}
            />
          )}
          {section === "history" && (
            <InstitutionHistory key={id} id={id!} refresh={refresh} />
          )}
          {section === "coordination" &&
            (institution.scope === "all_bureaus" &&
            ["coordinator", "auditor"].includes(user.role) ? (
              <InstitutionCoordination
                key={id}
                id={id!}
                user={user}
                options={options}
                refresh={refresh}
              />
            ) : (
              <section className="panel card-body">
                <h2>Coordination access</h2>
                <p>
                  Cross-bureau coordination is available to coordinators and
                  auditors.
                </p>
              </section>
            ))}
          {section === "reports" && (
            <section className="institution-report">
              <Report
                filters={new URLSearchParams({ institution: id! }).toString()}
                embedded
              />
            </section>
          )}
          {![
            "overview",
            "cases",
            "history",
            "coordination",
            "reports",
          ].includes(section) && (
            <ErrorBox message="Unknown institution section. Choose a section above." />
          )}
        </>
      )}
    </>
  );
}

function InstitutionOverview({
  institution: i,
}: {
  institution: InstitutionProfile;
}) {
  const stats = [
    ["All cases", i.overview.total, ""],
    ["Open cases", i.overview.open, "pending=true"],
    ["Overdue cases", i.overview.overdue, "overdue=true"],
    ["Closed cases", i.overview.closed, "status=disposed"],
    [
      "Unresolved escalations",
      i.overview.unresolved_escalations,
      "escalated=true",
    ],
  ] as const;
  return (
    <>
      <div className="institution-stats">
        {stats.map(([label, value, filter]) => (
          <Link
            key={label}
            className="home-stat"
            to={`/institutions/${i.id}?section=cases${filter ? `&${filter}` : ""}`}
          >
            <span>{label}</span>
            <strong>{value.toLocaleString("en-IN")}</strong>
            {label === "Overdue cases" && <small>Included in open cases</small>}
          </Link>
        ))}
      </div>
      <div className="institution-overview">
        <section className="panel" aria-label="All-time case classifications">
          <div className="panel-heading">
            <h2>Cases by classification</h2>
          </div>
          <dl className="metadata card-body">
            {i.classifications.map((row) => (
              <div key={row.classification}>
                <dt>{classifications[row.classification]}</dt>
                <dd>
                  <Link
                    className="institution-link"
                    to={`/institutions/${i.id}?section=cases&classification=${row.classification}`}
                  >
                    {row.count}
                  </Link>
                </dd>
              </div>
            ))}
          </dl>
        </section>
        <section className="panel">
          <div className="panel-heading">
            <h2>Institution identity</h2>
          </div>
          <dl className="metadata card-body">
            {[
              ["Permanent ID", i.permanent_id],
              ["Region", i.region],
              ["District", i.district],
              ["Official email", i.official_email],
              ["Official phone", i.official_phone],
              ["Official address", i.address],
            ].map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{value || "Not recorded"}</dd>
              </div>
            ))}
          </dl>
        </section>
        <section className="panel">
          <div className="panel-heading">
            <h2>Cases by responsible bureau</h2>
          </div>
          <p className="card-body muted">
            All cases, including closed cases, within your access.
          </p>
          {i.bureaus.length ? (
            <div
              className="table-scroll"
              role="region"
              tabIndex={0}
              aria-label="Institution bureau totals"
            >
              <table>
                <thead>
                  <tr>
                    <th>Bureau</th>
                    <th>Cases</th>
                  </tr>
                </thead>
                <tbody>
                  {i.bureaus.map((b) => (
                    <tr key={b.bureau__code}>
                      <td>{b.bureau__name}</td>
                      <td>
                        <Link
                          className="institution-link"
                          to={`/institutions/${i.id}?section=cases&bureau=${encodeURIComponent(b.bureau__code)}`}
                        >
                          {b.count}
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty>No cases are visible within your access.</Empty>
          )}
        </section>
      </div>
    </>
  );
}

function InstitutionCases({
  id,
  options,
  refresh,
}: {
  id: string;
  options: Options;
  refresh: number;
}) {
  const [params, setParams] = useSearchParams();
  const query = new URLSearchParams();
  for (const key of [
    "page",
    "q",
    "status",
    "category",
    "classification",
    "bureau",
    "pending",
    "overdue",
    "escalated",
  ])
    if (params.get(key)) query.set(key, params.get(key)!);
  const { data, error } = usePoll<Page<Case>>(
    `/api/institutions/${id}/cases?${query}`,
    0,
    refresh,
    validPage,
  );
  function change(key: string, value: string) {
    const next = new URLSearchParams(query);
    next.set("section", "cases");
    next.delete("page");
    if (key === "status") {
      next.delete("pending");
      next.delete("overdue");
    }
    value ? next.set(key, value) : next.delete(key);
    setParams(next, { replace: true });
  }
  return (
    <section className="panel" aria-label="Institution cases">
      <div className="panel-heading">
        <h2>Institution cases</h2>
        <ExportButton
          filters={new URLSearchParams({
            ...Object.fromEntries(query),
            institution: id,
          }).toString()}
        />
      </div>
      <div className="institution-filters">
        <label>
          Classification
          <select
            value={query.get("classification") || ""}
            onChange={(e) => change("classification", e.target.value)}
          >
            <option value="">All classifications</option>
            {Object.entries(classifications).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label className="institution-search">
          Search cases
          <input
            type="search"
            value={query.get("q") || ""}
            maxLength={200}
            onChange={(e) => change("q", e.target.value)}
          />
        </label>
        <label>
          Status
          <select
            value={query.get("status") || ""}
            onChange={(e) => change("status", e.target.value)}
          >
            <option value="">All statuses</option>
            {statuses.map((s) => (
              <option key={s} value={s}>
                {labels[s]}
              </option>
            ))}
          </select>
        </label>
        <label>
          Category
          <select
            value={query.get("category") || ""}
            onChange={(e) => change("category", e.target.value)}
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
        <label>
          Bureau
          <select
            value={query.get("bureau") || ""}
            onChange={(e) => change("bureau", e.target.value)}
          >
            <option value="">All authorized bureaus</option>
            {options.bureaus.map((b) => (
              <option key={b.code} value={b.code}>
                {b.name}
              </option>
            ))}
          </select>
        </label>
        <Link className="text-button" to={`/institutions/${id}?section=cases`}>
          Clear case filters
        </Link>
      </div>
      {(query.has("pending") || query.has("overdue")) && (
        <p className="card-body muted">
          Showing {query.has("overdue") ? "overdue" : "open"} cases.
        </p>
      )}
      <ErrorBox message={error} />
      {!data && !error && <Loading />}
      {data && (
        <>
          <CaseTable rows={data.results} />
          <Pagination data={data} params={params} setParams={setParams} />
        </>
      )}
    </section>
  );
}

function InstitutionHistory({ id, refresh }: { id: string; refresh: number }) {
  const [params, setParams] = useSearchParams();
  const page = params.get("page") || "1";
  const { data, error } = usePoll<Page<InstitutionAction>>(
    `/api/institutions/${id}/history?page=${encodeURIComponent(page)}`,
    0,
    refresh,
    validPage,
  );
  return (
    <section className="panel" aria-label="Institution action history">
      <div className="panel-heading">
        <h2>Institution action history</h2>
        <span className="muted">
          Newest first · All time · Within your access
        </span>
      </div>
      <ErrorBox message={error} />
      {!data && !error && <Loading />}
      {data && (
        <>
          {data.results.length ? (
            <ol className="timeline institution-timeline">
              {data.results.map((a) => (
                <li key={a.id}>
                  <span className="timeline-dot" />
                  <div>
                    <div className="timeline-title">
                      <strong>{a.kind.replaceAll("_", " ")}</strong>
                      <time dateTime={a.created_at}>
                        {new Date(a.created_at).toLocaleString("en-IN")}
                      </time>
                    </div>
                    <Link className="case-ref" to={`/cases/${a.case_id}`}>
                      {a.reference}
                    </Link>
                    <p>{a.reason}</p>
                    <small>{a.actor} · Bureau at action: {a.bureau_at_action || "Unknown (historical)"}</small>
                    {Object.keys(a.changes).length > 0 && (
                      <div className="change-details">
                        {Object.entries(a.changes).map(([key, value]) => (
                          <span key={key}>
                            {key.replaceAll("_", " ")}:{" "}
                            {typeof value === "object" && value
                              ? `${(value as { before?: unknown }).before ?? "None"} → ${(value as { after?: unknown }).after ?? "None"}`
                              : String(value)}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          ) : (
            <Empty>
              No recorded case actions are visible within your access.
            </Empty>
          )}
          <Pagination data={data} params={params} setParams={setParams} />
        </>
      )}
    </section>
  );
}

function InstitutionCoordination({
  id,
  user,
  options,
  refresh,
}: {
  id: string;
  user: User;
  options: Options;
  refresh: number;
}) {
  const [params, setParams] = useSearchParams();
  const { data: dashboard, error: dashboardError } = usePoll<Dashboard>(
    `/api/dashboard?institution=${id}`,
    0,
    refresh,
    validDashboard,
  );
  const { data, error } = usePoll<Page<Overlap>>(
    `/api/overlaps?institution=${id}&decision=all&page=${encodeURIComponent(params.get("page") || "1")}`,
    0,
    refresh,
    validPage,
  );
  const notice = dashboard?.coordination_notices?.[0];
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Institution coordination</h2>
        <Link
          className="button secondary"
          to={`/coordination/workspace?institution=${id}`}
        >
          Agreed responsibilities and follow-up
        </Link>
        {user.role === "coordinator" && (
          <Link
            className="button secondary"
            to={`/relationships/new?institution=${id}`}
          >
            Create manual relationship
          </Link>
        )}
        <Link className="text-button" to={`/coordination?institution=${id}`}>
          {user.role === "coordinator"
            ? "Review suggestions"
            : "Inspect suggestions"}{" "}
          →
        </Link>
      </div>
      <ErrorBox message={dashboardError || error} />
      <CoordinationNotices filters={`institution=${id}`} />
      {!dashboard && !dashboardError && <Loading />}
      {dashboard && (
        <div className="card-body">
          <h3>
            {notice
              ? "Cross-bureau attention needed"
              : "No cross-bureau notice"}
          </h3>
          <p>
            {notice
              ? `${notice.count} open cases are currently owned by ${notice.bureaus} distinct bureaus.`
              : "This institution does not currently have active cases in two or more responsible bureaus."}
          </p>
          <p className="muted">
            Based on current ownership of all active cases, independently of
            semantic similarity. A notice is not a confirmed duplicate incident.
          </p>
          {dashboard.workload.map((b) => (
            <p key={b.bureau__code}>
              {options.bureaus.find((x) => x.code === b.bureau__code)?.name ||
                b.bureau__code}
              : {b.count} open cases
            </p>
          ))}
        </div>
      )}
      <div className="panel-heading">
        <h3>Suggestions and recorded relationships</h3>
      </div>
      {!data && !error && <Loading />}
      {data && (
        <>
          {data.results.length ? (
            <div
              className="table-scroll"
              role="region"
              aria-label="Institution relationships"
              tabIndex={0}
            >
              <table>
                <thead>
                  <tr>
                    <th>Cases</th>
                    <th>Relationship</th>
                    <th>Evidence</th>
                    <th>Review reason</th>
                  </tr>
                </thead>
                <tbody>
                  {data.results.map((pair) => (
                    <tr key={pair.id}>
                      <td>
                        <Link to={`/cases/${pair.left.id}`}>
                          {pair.left.reference}
                        </Link>{" "}
                        /{" "}
                        <Link to={`/cases/${pair.right.id}`}>
                          {pair.right.reference}
                        </Link>
                      </td>
                      <td>
                        <Badge status={pair.decision} />
                      </td>
                      <td>
                        {typeof pair.score === "number"
                          ? `Cosine similarity ${pair.score.toFixed(3)}`
                          : "Not model-scored"}
                        <span className="table-sub">Human review required</span>
                      </td>
                      <td>
                        {pair.reason || "Awaiting review"}
                        {pair.reviewed_at && (
                          <span className="table-sub">
                            {pair.reviewer} · {date(pair.reviewed_at)}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty>
              No suggestions or recorded relationships for this institution.
            </Empty>
          )}
          <Pagination data={data} params={params} setParams={setParams} />
        </>
      )}
    </section>
  );
}
