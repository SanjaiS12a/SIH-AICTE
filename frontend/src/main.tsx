import React, { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
  NavLink,
  Link,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import {
  SquaresFour,
  Files,
  Intersect,
  Bell,
  ArrowUpRight,
  Plus,
  MagnifyingGlass,
  ArrowRight,
  ArrowLeft,
  CheckCircle,
  DownloadSimple,
  ShieldCheck,
  SignOut,
  Buildings,
  CaretRight,
  Tray,
  Paperclip,
  ArrowsLeftRight,
  FunnelSimple,
} from "@phosphor-icons/react";

import { api, csrf, date, labels, categories, statuses } from "./api";
import type {
  User,
  Institution,
  Case,
  CaseDetail,
  Page,
  Options,
  Overlap,
} from "./api";
import "./style.css";
import { DashboardHome } from "./dashboard";
import {
  ErrorBox,
  Loading,
  Empty,
  Badge,
  Heading,
  CaseTable,
  Pagination,
} from "./ui";
import { Imports, ImportDetail, Report, ExportButton } from "./imports";
import {
  InstitutionDirectory,
  InstitutionEditor,
  InstitutionProfilePage,
} from "./institutions";

const emptyOptions: Options = { bureaus: [], officers: [], regions: [] };
function GovernmentHeader() {
  return (
    <header className="government-header">
      <div className="government-utility">
        <span>AICTE · Smart India Hackathon 26264</span>
        <span>
          English <span aria-hidden="true">|</span>{" "}
          <a href="#main">Skip to main content</a>
        </span>
      </div>
      <div className="government-identity">
        <Link
          className="council-wordmark"
          to="/"
          aria-label="AICTE portal home"
        >
          <Buildings size={35} weight="regular" />
          <strong>AICTE</strong>
        </Link>
        <div className="council-name">
          <p lang="hi">अखिल भारतीय तकनीकी शिक्षा परिषद</p>
          <strong>All India Council for Technical Education</strong>
          <span>
            Institution-related complaints · Cross-bureau coordination
          </span>
        </div>
        <span className="prototype-stamp">
          SIH 26264<span>PROJECT PROTOTYPE</span>
        </span>
      </div>
      <div className="government-portal-title">
        <span>Integrated Complaint Monitoring Portal</span>
        <span className="portal-motto">
          Transparency · Coordination · Accountability
        </span>
      </div>
    </header>
  );
}
function useLoad<T>(url: string, refresh = 0) {
  const [data, setData] = useState<T | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    setData(null);
    setError("");
    api<T>(url, { signal: controller.signal })
      .then(setData)
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      });
    return () => controller.abort();
  }, [url, refresh]);
  return { data, error };
}
function App() {
  const { data, error } = useLoad<{ user: User | null }>("/api/session");
  if (error)
    return (
      <main className="login">
        <ErrorBox message={error} />
        <button onClick={() => location.reload()}>Try again</button>
      </main>
    );
  if (!data) return <Loading />;
  if (!data.user)
    return (
      <div className="public-portal">
        <GovernmentHeader />
        <main id="main" className="login">
          <div className="brand-mark">
            <Intersect size={27} />
          </div>
          <span className="eyebrow">
            AICTE · INSTITUTION COMPLAINT SERVICES
          </span>
          <h1>
            Integrated Complaint
            <br />
            Monitoring Portal
          </h1>
          <p>
            Track institution complaints, connect related cases, and keep every
            action accountable.
          </p>
          <a className="button" href="/accounts/login/?next=/">
            Sign in to workspace <ArrowRight size={18} />
          </a>
          <small>
            SIH project prototype · Fictional institutions and synthetic
            complaints.
          </small>
        </main>
        <div className="public-footer">
          All India Council for Technical Education · SIH 26264 project
          prototype
        </div>
      </div>
    );
  return <Shell user={data.user} />;
}
function Shell({ user }: { user: User }) {
  const [showAlerts, setShowAlerts] = useState(false),
    [alertsVersion, setAlertsVersion] = useState(0);
  const { data: alerts } = useLoad<{
    unread: number;
    results: {
      id: number;
      case_id: string;
      reference: string;
      kind: string;
      deadline: string;
      read: boolean;
    }[];
  }>("/api/notifications", alertsVersion);
  const { data: options } = useLoad<Options>("/api/options");
  const isCoord = ["coordinator", "auditor"].includes(user.role);
  const location = useLocation();
  useEffect(() => {
    setShowAlerts(false);
    setAlertsVersion((x) => x + 1);
  }, [location.pathname]);
  return (
    <div className="app">
      <a className="skip" href="#main">
        Skip to content
      </a>
      <GovernmentHeader />
      <aside className="sidebar">
        <Link className="brand" to="/">
          <span className="brand-mark">
            <Buildings weight="regular" size={25} />
          </span>
          <span>
            AICTE<span className="brand-sub">COMPLAINT MONITORING</span>
          </span>
        </Link>
        <div className="workspace-label">PORTAL SERVICES</div>
        <nav>
          <NavLink to="/" end>
            <SquaresFour size={21} />
            Dashboard
          </NavLink>
          <NavLink to="/cases">
            <Files size={21} />
            Case registry
          </NavLink>
          <NavLink to="/institutions">
            <Buildings size={21} />
            Institutions
          </NavLink>
          <NavLink to="/imports">
            <Tray size={21} />
            Import data
          </NavLink>
          <NavLink to="/reports">
            <Files size={21} />
            Reports
          </NavLink>
          {isCoord && (
            <NavLink to="/coordination">
              <Intersect size={21} />
              Coordination queue
            </NavLink>
          )}
        </nav>
        <div className="sidebar-bottom">
          <div className="demo-note">
            <span className="live-dot" /> SIH PROJECT PROTOTYPE
            <p>Integrated monitoring of institution-related complaint cases.</p>
            <small>
              Seed records are synthetic. Imported data retains its source.
            </small>
          </div>
          <div className="profile">
            <span className="avatar">
              {user.name
                .split(" ")
                .map((x) => x[0])
                .slice(0, 2)
                .join("")}
            </span>
            <span>
              <strong>{user.name}</strong>
              <small>
                {user.role} {user.bureau && `· ${user.bureau}`}
              </small>
            </span>
            <form action="/accounts/logout/" method="post">
              <input type="hidden" name="csrfmiddlewaretoken" value={csrf()} />
              <button className="icon-button" aria-label="Sign out">
                <SignOut size={19} />
              </button>
            </form>
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="breadcrumb">
            AICTE portal <CaretRight size={12} />
            <strong>
              {location.pathname === "/coordination"
                ? "Coordination queue"
                : location.pathname.startsWith("/institutions")
                  ? "Institutions"
                  : location.pathname.startsWith("/cases")
                    ? "Case registry"
                    : "Dashboard"}
            </strong>
          </div>
          <div className="top-actions">
            <span className="scope">
              <ShieldCheck size={16} />
              {isCoord ? "All bureaus" : user.bureau || "No bureau"}
            </span>
            <div className="alerts-wrap">
              <button
                className="icon-button alert-button"
                aria-label="Notifications"
                aria-expanded={showAlerts}
                onClick={() => setShowAlerts(!showAlerts)}
              >
                <Bell size={21} />
                {!!alerts?.unread && <i />}
              </button>
              {showAlerts && (
                <div className="alerts">
                  <div className="panel-heading">
                    <strong>
                      Notifications {alerts?.unread ? `(${alerts.unread})` : ""}
                    </strong>
                    <button
                      className="text-button"
                      onClick={async () => {
                        await api("/api/notifications", {
                          method: "POST",
                          body: "{}",
                        });
                        setAlertsVersion((x) => x + 1);
                      }}
                    >
                      Mark read
                    </button>
                  </div>
                  {alerts?.results.length ? (
                    alerts.results.map((n) => (
                      <Link key={n.id} to={`/cases/${n.case_id}`}>
                        <strong>{n.reference}</strong>
                        <span>
                          {typeof n.kind === "string"
                            ? n.kind.replaceAll("_", " ")
                            : "Notification"}{" "}
                          · {date(n.deadline)}
                        </span>
                      </Link>
                    ))
                  ) : (
                    <p className="muted">You’re all caught up.</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </header>
        <main id="main">
          <Routes>
            <Route
              path="/institutions"
              element={
                <InstitutionDirectory
                  user={user}
                  options={options || emptyOptions}
                />
              }
            />
            <Route
              path="/institutions/new"
              element={<InstitutionEditor user={user} />}
            />
            <Route
              path="/institutions/:id/edit"
              element={<InstitutionEditor user={user} />}
            />
            <Route
              path="/institutions/:id"
              element={
                <InstitutionProfilePage
                  user={user}
                  options={options || emptyOptions}
                />
              }
            />
            <Route path="/imports" element={<Imports user={user} />} />
            <Route path="/imports/:id" element={<ImportDetail user={user} />} />
            <Route
              path="/reports"
              element={<Report filters={location.search.slice(1)} />}
            />
            <Route
              path="/"
              element={
                <DashboardHome user={user} options={options || emptyOptions} />
              }
            />
            <Route
              path="/cases"
              element={
                <Registry user={user} options={options || emptyOptions} />
              }
            />
            <Route
              path="/cases/new"
              element={
                <NewCase options={options || emptyOptions} user={user} />
              }
            />
            <Route
              path="/cases/:id"
              element={<Detail user={user} options={options || emptyOptions} />}
            />
            <Route
              path="/coordination"
              element={
                isCoord ? (
                  <Coordination user={user} />
                ) : (
                  <ErrorBox message="Coordination access is required." />
                )
              }
            />
            <Route
              path="*"
              element={
                <Empty>
                  Page not found. <Link to="/">Return to overview</Link>
                </Empty>
              }
            />
          </Routes>
          <footer>
            AICTE · SIH 26264{" "}
            <span>
              Integrated Complaint Monitoring Portal · Project prototype
            </span>
            <span>
              <span className="live-dot" /> Local environment
            </span>
          </footer>
        </main>
      </div>
    </div>
  );
}
function Registry({ user, options }: { user: User; options: Options }) {
  const [params, setParams] = useSearchParams();
  const { data, error } = useLoad<Page<Case>>(`/api/cases?${params}`);
  const [search, setSearch] = useState(params.get("q") || "");
  function filter(key: string, value: string) {
    const p = new URLSearchParams(params);
    p.delete("page");
    if (value) p.set(key, value);
    else p.delete(key);
    setParams(p);
  }
  return (
    <>
      <Heading
        eyebrow="INSTITUTION COMPLAINTS"
        title="Case registry"
        subtitle="One place for every complaint, its ownership, and the next action."
      >
        <ExportButton filters={params.toString()} />
        {["officer", "coordinator"].includes(user.role) && (
          <Link className="button" to="/cases/new">
            <Plus size={18} />
            Register case
          </Link>
        )}
      </Heading>
      <section className="panel">
        <div className="filters">
          <form
            className="search"
            onSubmit={(e) => {
              e.preventDefault();
              filter("q", search);
            }}
          >
            <MagnifyingGlass size={19} />
            <input
              aria-label="Search cases"
              placeholder="Search institution, permanent ID, case reference…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <button className="text-button">Search</button>
          </form>
          <select
            aria-label="Bureau filter"
            value={params.get("bureau") || ""}
            onChange={(e) => filter("bureau", e.target.value)}
          >
            <option value="">All bureaus</option>
            {options.bureaus.map((b) => (
              <option key={b.code}>{b.code}</option>
            ))}
          </select>
          <select
            aria-label="Status filter"
            value={params.get("status") || ""}
            onChange={(e) => filter("status", e.target.value)}
          >
            <option value="">All statuses</option>
            {statuses.map((s) => (
              <option value={s} key={s}>
                {labels[s]}
              </option>
            ))}
          </select>
          <select
            aria-label="Category filter"
            value={params.get("category") || ""}
            onChange={(e) => filter("category", e.target.value)}
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </div>
        <div className="filter-secondary">
          <FunnelSimple size={16} />
          <select
            aria-label="Region filter"
            value={params.get("region") || ""}
            onChange={(e) => filter("region", e.target.value)}
          >
            <option value="">All regions</option>
            {options.regions.map((r) => (
              <option key={r}>{r}</option>
            ))}
          </select>
          <label>
            From{" "}
            <input
              type="date"
              value={params.get("from") || ""}
              onChange={(e) => filter("from", e.target.value)}
            />
          </label>
          <label>
            To{" "}
            <input
              type="date"
              value={params.get("to") || ""}
              onChange={(e) => filter("to", e.target.value)}
            />
          </label>
          <label>
            <input
              type="checkbox"
              checked={params.get("overdue") === "true"}
              onChange={(e) =>
                filter("overdue", e.target.checked ? "true" : "")
              }
            />{" "}
            Overdue only
          </label>
          {params.size > 0 && (
            <button
              className="text-button"
              onClick={() => {
                setParams({});
                setSearch("");
              }}
            >
              Clear filters
            </button>
          )}
        </div>
        <ErrorBox message={error} />
        {!data && !error ? (
          <Loading />
        ) : (
          data && (
            <>
              <CaseTable rows={data.results} />
              <Pagination data={data} params={params} setParams={setParams} />
            </>
          )
        )}
      </section>
    </>
  );
}
function NewCase({ options, user }: { options: Options; user: User }) {
  const { data: institutions } = useLoad<Institution[]>("/api/institutions");
  const [error, setError] = useState(""),
    [saving, setSaving] = useState(false),
    [submissionId] = useState(() => crypto.randomUUID());
  const navigate = useNavigate();
  if (!["officer", "coordinator"].includes(user.role))
    return <ErrorBox message="Your account cannot register complaints." />;
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSaving(true);
    setError("");
    const d = Object.fromEntries(new FormData(e.currentTarget));
    if (!d.incident_date) delete d.incident_date;
    try {
      const c = await api<Case>("/api/cases", {
        method: "POST",
        body: JSON.stringify({ ...d, submission_id: submissionId }),
      });
      navigate(`/cases/${c.id}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }
  return (
    <>
      <Heading
        eyebrow="A CLEAR START"
        title="Register a complaint"
        subtitle="Capture the original allegation. Every subsequent action will stay in its history."
      />
      <form className="panel form-panel" onSubmit={submit}>
        <ErrorBox message={error} />
        <h2>Institution & ownership</h2>
        <div className="form-grid">
          <label className="wide">
            Institution
            <select name="institution" required defaultValue="">
              <option value="" disabled>
                Select a verified registry institution
              </option>
              {institutions?.map((i) => (
                <option key={i.id} value={i.id}>
                  {i.name} · {i.permanent_id}
                </option>
              ))}
            </select>
          </label>
          <label>
            Receiving bureau
            <select name="bureau" required defaultValue={user.bureau || ""}>
              <option value="" disabled>
                Select bureau
              </option>
              {options.bureaus.map((b) => (
                <option key={b.code}>{b.code}</option>
              ))}
            </select>
          </label>
          <label>
            Category
            <select name="category" required defaultValue="">
              <option value="" disabled>
                Select category
              </option>
              {categories.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
          <label>
            Source system
            <input
              name="source_system"
              required
              maxLength={40}
              defaultValue="manual"
            />
          </label>
          <label>
            Source reference
            <input
              name="source_reference"
              required
              maxLength={100}
              placeholder="Original complaint / receipt reference"
            />
          </label>
          <label>
            Incident date (optional)
            <input
              type="date"
              name="incident_date"
              max={new Date().toLocaleDateString("en-CA")}
            />
          </label>
        </div>
        <div className="form-divider" />
        <h2>The allegation</h2>
        <label>
          Short allegation summary
          <textarea
            name="summary"
            rows={3}
            required
            maxLength={2000}
            placeholder="What happened, when, and what remedy is being requested?"
          />
          <small>
            Matching uses this original summary only (maximum 256 model
            wordpieces). Add supporting detail below.
          </small>
        </label>
        <label>
          Full complaint
          <textarea
            name="description"
            rows={6}
            required
            maxLength={10000}
            placeholder="Record the complaint and supporting context in full."
          />
        </label>
        <div className="info-note">
          <ShieldCheck size={20} />
          Original allegations are preserved. Corrections are added as notes. A
          30-calendar-day demonstration deadline is applied at registration.
        </div>
        <div className="form-actions">
          <Link className="button secondary" to="/cases">
            Cancel
          </Link>
          <button disabled={saving}>
            {saving ? "Registering…" : "Register case"}
            <ArrowRight size={17} />
          </button>
        </div>
      </form>
    </>
  );
}
function Detail({ user, options }: { user: User; options: Options }) {
  const { id } = useParams();
  const [refresh, setRefresh] = useState(0);
  const { data: c, error } = useLoad<CaseDetail>(`/api/cases/${id}`, refresh);
  const [action, setAction] = useState("note"),
    [status, setStatus] = useState("under_review"),
    [bureau, setBureau] = useState(""),
    [officer, setOfficer] = useState(""),
    [due, setDue] = useState(""),
    [reason, setReason] = useState(""),
    [actionError, setActionError] = useState(""),
    [busy, setBusy] = useState(false),
    [success, setSuccess] = useState("");
  useEffect(() => {
    if (c?.matching_state === "pending") {
      const timer = setTimeout(() => setRefresh((x) => x + 1), 4000);
      return () => clearTimeout(timer);
    }
  }, [c]);
  const writable = ["officer", "coordinator"].includes(user.role);
  async function act(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setActionError("");
    setSuccess("");
    try {
      await api(`/api/cases/${id}/actions`, {
        method: "POST",
        body: JSON.stringify({
          kind: action,
          expected_version: c!.version,
          reason,
          ...(action === "status" ? { status } : {}),
          ...(action === "transfer" ? { bureau } : {}),
          ...(action === "assign"
            ? { assigned_to: officer ? Number(officer) : null }
            : {}),
          ...(action === "deadline"
            ? { due_at: new Date(due).toISOString() }
            : {}),
        }),
      });
      setReason("");
      setSuccess("Action recorded in the case history.");
      setRefresh((x) => x + 1);
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function upload(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setBusy(true);
    setActionError("");
    const form = e.currentTarget;
    try {
      await api(`/api/cases/${id}/attachments`, {
        method: "POST",
        body: new FormData(form),
      });
      form.reset();
      setRefresh((x) => x + 1);
      setSuccess("Supporting document uploaded.");
    } catch (e) {
      setActionError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Link className="back-link" to="/cases">
        <ArrowLeft size={16} />
        Back to case registry
      </Link>
      <ErrorBox message={error} />
      {!c && !error && <Loading />}
      {c && (
        <>
          <Heading
            eyebrow={`${c.reference} · ${c.bureau}`}
            title={
              <Link
                className="institution-link"
                to={`/institutions/${c.institution.id}`}
              >
                {c.institution.name}
              </Link>
            }
            subtitle={`${c.institution.permanent_id} · ${c.institution.region} · ${c.institution.district}`}
          >
            <Badge status={c.status} />
          </Heading>
          <div className="detail-grid">
            <div>
              <section className="panel detail-card">
                <div className="panel-heading">
                  <h2>Original complaint</h2>
                  <span className="bureau-tag capitalize">{c.category}</span>
                </div>
                <div className="card-body">
                  <h3 className="allegation">{c.summary}</h3>
                  <p className="description">{c.description}</p>
                  <dl className="metadata">
                    <div>
                      <dt>Source</dt>
                      <dd>
                        {c.source_system} · {c.source_reference}
                      </dd>
                    </div>
                    <div>
                      <dt>Incident date</dt>
                      <dd>{date(c.incident_date)}</dd>
                    </div>
                    <div>
                      <dt>Received</dt>
                      <dd>{date(c.received_at)}</dd>
                    </div>
                    <div>
                      <dt>Due date</dt>
                      <dd className={c.overdue ? "overdue-text" : ""}>
                        {date(c.due_at)}
                        {c.overdue ? " · Overdue" : ""}
                      </dd>
                    </div>
                    <div>
                      <dt>Assigned officer</dt>
                      <dd>{c.assigned_name || "Unassigned"}</dd>
                    </div>
                    <div>
                      <dt>Matching</dt>
                      <dd>
                        {c.matching_state === "pending"
                          ? "Processing in background"
                          : c.matching_state === "complete"
                            ? "Scan complete"
                            : "Scan failed"}
                      </dd>
                    </div>
                  </dl>
                  {c.matching_error && <ErrorBox message={c.matching_error} />}
                  <small className="muted">
                    Matching examines the original allegation summary.
                    Suggestions require human review.
                  </small>
                </div>
              </section>
              <section className="panel detail-card">
                <div className="panel-heading">
                  <h2>Case history</h2>
                  <span className="muted">{c.actions.length} actions</span>
                </div>
                <ol className="timeline">
                  {c.actions.map((a) => (
                    <li key={a.id}>
                      <span className="timeline-dot" />
                      <div>
                        <div className="timeline-title">
                          <strong>
                            {typeof a.kind === "string"
                              ? a.kind.replaceAll("_", " ")
                              : "Unknown action"}
                          </strong>
                          <time>
                            {new Date(a.created_at).toLocaleString("en-IN")}
                          </time>
                        </div>
                        <p>{a.reason}</p>
                        <small>{a.actor}</small>
                        {Object.keys(a.changes).length > 0 && (
                          <div className="change-details">
                            {Object.entries(a.changes).map(([key, value]) => (
                              <span key={key}>
                                {key.replaceAll("_", " ")}:{" "}
                                {typeof value === "object" && value
                                  ? `${(value as any).before ?? "None"} → ${(value as any).after ?? "None"}`
                                  : String(value)}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </li>
                  ))}
                </ol>
              </section>
              <section className="panel detail-card">
                <div className="panel-heading">
                  <h2>Institution history</h2>
                  <span className="muted">Within your access</span>
                </div>
                <div className="card-body">
                  <Link
                    className="text-button"
                    to={`/institutions/${c.institution.id}?section=cases`}
                  >
                    View complete institution case list →
                  </Link>
                  <p className="muted">
                    Recent preview below. Open the complete list for every page
                    of authorized cases.
                  </p>
                </div>
                {c.institution_history.length ? (
                  <CaseTable rows={c.institution_history} />
                ) : (
                  <Empty>No other cases visible for this institution.</Empty>
                )}
              </section>
            </div>
            <div>
              <section className="panel detail-card">
                <div className="panel-heading">
                  <h2>Record an action</h2>
                  <ShieldCheck size={19} />
                </div>
                {writable ? (
                  <form className="card-body action-form" onSubmit={act}>
                    <ErrorBox message={actionError} />
                    {success && (
                      <p role="status" className="success">
                        {success}
                      </p>
                    )}
                    <label>
                      Action
                      <select
                        value={action}
                        onChange={(e) => setAction(e.target.value)}
                      >
                        <option value="note">Add a note / correction</option>
                        <option value="status">Update status</option>
                        {user.role === "coordinator" && (
                          <>
                            <option value="transfer">
                              Transfer to a bureau
                            </option>
                            <option value="assign">Assign an officer</option>
                            <option value="deadline">Change deadline</option>
                            <option value="retry_matching">
                              Retry matching
                            </option>
                          </>
                        )}
                      </select>
                    </label>
                    {action === "status" && (
                      <label>
                        New status
                        <select
                          value={status}
                          onChange={(e) => setStatus(e.target.value)}
                        >
                          {statuses.map((s) => (
                            <option value={s} key={s}>
                              {labels[s]}
                            </option>
                          ))}
                        </select>
                      </label>
                    )}
                    {action === "transfer" && (
                      <label>
                        Receiving bureau
                        <select
                          required
                          value={bureau}
                          onChange={(e) => setBureau(e.target.value)}
                        >
                          <option value="" disabled>
                            Select bureau
                          </option>
                          {options.bureaus
                            .filter((b) => b.code !== c.bureau)
                            .map((b) => (
                              <option key={b.code}>{b.code}</option>
                            ))}
                        </select>
                      </label>
                    )}
                    {action === "assign" && (
                      <label>
                        Officer
                        <select
                          value={officer}
                          onChange={(e) => setOfficer(e.target.value)}
                        >
                          <option value="">Unassigned</option>
                          {options.officers
                            .filter((o) => o.bureau === c.bureau)
                            .map((o) => (
                              <option key={o.id} value={o.id}>
                                {o.name}
                              </option>
                            ))}
                        </select>
                      </label>
                    )}
                    {action === "deadline" && (
                      <label>
                        New deadline
                        <input
                          type="datetime-local"
                          required
                          value={due}
                          onChange={(e) => setDue(e.target.value)}
                        />
                      </label>
                    )}
                    <label>
                      {action === "status" && status === "disposed"
                        ? "Resolution note"
                        : "Reason / note"}
                      <textarea
                        rows={4}
                        required
                        maxLength={4000}
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        placeholder="Explain the action for the next person reviewing this case."
                      />
                    </label>
                    <button disabled={busy}>
                      {busy ? "Saving…" : "Record action"}
                      <ArrowRight size={17} />
                    </button>
                    <small className="muted">
                      Actions are timestamped and preserved. Version {c.version}
                      .
                    </small>
                  </form>
                ) : (
                  <p className="card-body muted">
                    Your audit access is read-only.
                  </p>
                )}
              </section>
              <section className="panel detail-card">
                <div className="panel-heading">
                  <h2>Supporting documents</h2>
                  <Paperclip size={20} />
                </div>
                <div className="card-body">
                  {c.attachments.length ? (
                    c.attachments.map((a) => (
                      <a
                        className="attachment"
                        key={a.id}
                        href={`/api/attachments/${a.id}`}
                      >
                        <Paperclip size={19} />
                        <span>
                          {a.original_name}
                          <small>
                            {Math.ceil(a.size / 1024)} KB · Private attachment
                          </small>
                        </span>
                        <DownloadSimple size={16} />
                      </a>
                    ))
                  ) : (
                    <p className="muted">No documents attached.</p>
                  )}
                  {writable && (
                    <form onSubmit={upload} className="upload">
                      <label>
                        Attach evidence
                        <input
                          name="file"
                          type="file"
                          required
                          accept=".pdf,.png,.jpg,.jpeg"
                        />
                      </label>
                      <small>PDF, PNG or JPEG · up to 5 MB</small>
                      <button
                        disabled={busy}
                        className="button secondary small"
                      >
                        Upload document
                      </button>
                    </form>
                  )}
                </div>
              </section>
            </div>
          </div>
        </>
      )}
    </>
  );
}
function Coordination({ user }: { user: User }) {
  const [params, setParams] = useSearchParams();
  const [refresh, setRefresh] = useState(0);
  const { data, error } = useLoad<Page<Overlap>>(
    `/api/overlaps?${params}`,
    refresh,
  );
  const [selected, setSelected] = useState<number | null>(null);
  const pair = data?.results.find((o) => o.id === selected) || data?.results[0];
  return (
    <>
      <Heading
        eyebrow="CONNECT THE CONTEXT"
        title="Coordination queue"
        subtitle="Potential overlaps, explained. Review the evidence before deciding the relationship."
      />
      <div className="info-note">
        <ShieldCheck size={21} />
        <span>
          Similarity is a retrieval signal, not a finding. Complaints stay
          independent, whatever the review decision.
        </span>
      </div>
      {params.get("institution") && (
        <div className="info-note">
          <span>
            Institution filter:{" "}
            {pair ? (
              <Link
                className="institution-link"
                to={`/institutions/${pair.left.institution.id}`}
              >
                {pair.left.institution.name}
              </Link>
            ) : (
              params.get("institution")
            )}
          </span>
          <button
            className="text-button"
            onClick={() => {
              const next = new URLSearchParams(params);
              next.delete("institution");
              next.delete("page");
              setParams(next);
            }}
          >
            Clear institution filter
          </button>
        </div>
      )}
      <div className="queue-toolbar">
        <div className="tabs">
          {[
            "pending",
            "all",
            "same_incident",
            "related_issue",
            "unrelated",
          ].map((d) => (
            <button
              className={
                (params.get("decision") || "pending") === d ? "active" : ""
              }
              onClick={() => {
                const next = new URLSearchParams(params);
                next.set("decision", d);
                next.delete("page");
                setParams(next);
                setSelected(null);
              }}
              key={d}
            >
              {d === "all" ? "All reviews" : labels[d]}
            </button>
          ))}
        </div>
        <span className="muted">{data?.count || 0} pairs</span>
      </div>
      <ErrorBox message={error} />
      {!data && !error && <Loading />}
      {data &&
        (data.results.length ? (
          <>
            <div className="queue-layout">
              <section
                className="pair-list"
                aria-label="Potential case pairs"
                tabIndex={0}
              >
                {data.results.map((o) => (
                  <article
                    key={o.id}
                    className={`pair-item ${pair?.id === o.id ? "selected" : ""}`}
                  >
                    <span className="pair-top">
                      <span>
                        {o.left.bureau} <ArrowsLeftRight size={13} />{" "}
                        {o.right.bureau}
                      </span>
                      <strong>{o.score.toFixed(3)} cosine</strong>
                    </span>
                    <Link
                      className="institution-link"
                      to={`/institutions/${o.left.institution.id}`}
                    >
                      {o.left.institution.name}
                    </Link>
                    <button
                      className="text-button"
                      onClick={() => setSelected(o.id)}
                      aria-pressed={pair?.id === o.id}
                    >
                      {o.left.reference} / {o.right.reference}
                    </button>
                    <Badge status={o.decision} />
                  </article>
                ))}
              </section>
              {pair && (
                <PairReview
                  key={`${pair.id}-${pair.version}`}
                  pair={pair}
                  user={user}
                  onSaved={() => {
                    setRefresh((x) => x + 1);
                    setSelected(null);
                  }}
                />
              )}
            </div>
            <Pagination data={data} params={params} setParams={setParams} />
          </>
        ) : (
          <section className="panel">
            <Empty>
              No pairs in this review category. New scans appear here after
              processing.
            </Empty>
          </section>
        ))}
    </>
  );
}
function PairReview({
  pair: p,
  user,
  onSaved,
}: {
  pair: Overlap;
  user: User;
  onSaved: () => void;
}) {
  const [decision, setDecision] = useState(
      p.decision === "pending" ? "same_incident" : p.decision,
    ),
    [reason, setReason] = useState(p.reason),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function save(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(`/api/overlaps/${p.id}/review`, {
        method: "POST",
        body: JSON.stringify({ decision, reason, expected_version: p.version }),
      });
      onSaved();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel pair-review">
      <div className="panel-heading">
        <div>
          <h2>Review potential relationship</h2>
          <p>
            <Link
              className="institution-link"
              to={`/institutions/${p.left.institution.id}`}
            >
              {p.evidence.institution}
            </Link>
          </p>
        </div>
        <Badge status={p.decision} />
      </div>
      <div className="comparison">
        {[p.left, p.right].map((c, i) => (
          <article key={c.id}>
            <span className="eyebrow">
              COMPLAINT {i === 0 ? "A" : "B"} · {c.bureau}
            </span>
            <Link className="case-ref" to={`/cases/${c.id}`}>
              {c.reference}
              <ArrowUpRight size={15} />
            </Link>
            <h3>{c.summary}</h3>
            <p className="description">{c.description}</p>
            <dl>
              <dt>Category</dt>
              <dd className="capitalize">{c.category}</dd>
              <dt>Incident date</dt>
              <dd>{date(c.incident_date)}</dd>
              <dt>Status</dt>
              <dd>
                <Badge status={c.status} />
              </dd>
              <dt>Source reference</dt>
              <dd>{c.source_reference}</dd>
            </dl>
          </article>
        ))}
      </div>
      <div className="evidence">
        <h3>Why this pair was surfaced</h3>
        <div>
          <span>
            <Buildings size={17} />
            Same registry institution
          </span>
          <span>
            <Intersect size={17} />
            Cosine similarity: {p.score.toFixed(3)}
          </span>
          {p.evidence.shared_reference && (
            <span>Shared explicit source reference</span>
          )}
        </div>
        <small>
          {p.evidence.scope}. Model: {p.model_revision}.
        </small>
      </div>
      {user.role === "coordinator" ? (
        <form className="review-form" onSubmit={save}>
          <h3>Your coordination decision</h3>
          <ErrorBox message={error} />
          <div className="decision-options">
            {["same_incident", "related_issue", "unrelated"].map((d) => (
              <label key={d} className={decision === d ? "selected" : ""}>
                <input
                  type="radio"
                  name="decision"
                  value={d}
                  checked={decision === d}
                  onChange={() => setDecision(d)}
                />
                {labels[d]}
              </label>
            ))}
          </div>
          <label>
            Review reason
            <textarea
              required
              rows={3}
              maxLength={4000}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain what links or distinguishes these complaints."
            />
          </label>
          <div className="form-actions">
            <small>No records will be merged or closed.</small>
            <button disabled={busy}>
              {busy ? "Recording…" : "Record decision"}
              <CheckCircle size={18} />
            </button>
          </div>
        </form>
      ) : (
        <p className="card-body muted">
          Read-only audit access.{" "}
          {p.reason || "Awaiting a coordinator decision."}
        </p>
      )}
      {p.reviewer && (
        <p className="review-attribution">
          Last reviewed by {p.reviewer} · {date(p.reviewed_at)}
        </p>
      )}
    </section>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
