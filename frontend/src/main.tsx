import React, { useEffect, useState } from "react";
import { CaseIntelligence } from "./intelligence";
import type { FormEvent } from "react";
import { createRoot } from "react-dom/client";
import {
  BrowserRouter,
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

import {
  api,
  ApiError,
  csrf,
  date,
  labels,
  categories,
  statuses,
  classifications,
} from "./api";
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
import { PageBoundary } from "./page-boundary";
import { MyWork } from "./my-work";
import { PairEvidence, ReviewEvidence } from "./evidence";
import { CaseEscalations, EscalationQueue } from "./escalations";
import { ManualRelationship } from "./relationships";
import { SourceIntake, SourceRows, SourceJobs } from "./source-intake";
import {
  CoordinationWorkspace,
  CoordinationRecordPage,
  CoordinationRequests,
} from "./coordination-workflow";
import { CoordinationNotices, MovementsPage } from "./management";
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
  const { data: alerts, error: alertsError } = useLoad<{
    unread: number;
    results: {
      id: number;
      case_id: string;
      reference: string;
      kind: string;
      deadline: string | null;
      created_at: string;
      escalation_id: string | null;
      escalation_status: string | null;
      read: boolean;
    }[];
  }>("/api/notifications", alertsVersion);
  const { data: options } = useLoad<Options>("/api/options");
  const isCoord = ["coordinator", "auditor"].includes(user.role);
  const location = useLocation();
  const path = location.pathname;
  const section = path.startsWith("/institutions") ? "Institutions"
    : path.startsWith("/imports") ? "Data Imports"
      : path === "/reports" || path === "/movements" || path === "/coordination/activity" ? "Reports"
        : path === "/" ? "Home" : "My Work";
  const primary = [
    { label: "Home", to: "/", icon: SquaresFour },
    { label: "Institutions", to: "/institutions", icon: Buildings },
    { label: "My Work", to: "/work", icon: Files },
    { label: "Data Imports", to: "/imports", icon: Tray },
    { label: "Reports", to: "/reports", icon: Files },
  ];
  const parent = primary.find((item) => item.label === section)!;
  const pageLabel: Record<string, string> = {
    "/cases": "Case registry", "/cases/new": "Register case",
    "/coordination": "Coordination queue", "/coordination/workspace": "Coordination workspace",
    "/coordination/requests": "Coordination actions", "/relationships/new": "Manual relationship",
    "/escalations": "Escalations", "/movements": "Case movements",
    "/coordination/activity": "Cross-bureau activity", "/imports/sources": "Source intake",
    "/imports/source-jobs": "Source-upload history", "/institutions/new": "Register institution",
  };
  const currentLabel = pageLabel[path] || (path.startsWith("/cases/") ? "Case detail"
    : path.startsWith("/coordination/workspace/") ? "Coordination record"
      : path.endsWith("/edit") ? "Edit institution"
        : path.startsWith("/institutions/") ? "Institution profile"
          : path.startsWith("/imports/") ? (path.endsWith("/rows") ? "Source rows and conflicts" : "Import detail") : section);
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
        <nav aria-label="Primary navigation">
          {primary.map(({ label, to, icon: Icon }) => (
            <Link key={to} to={to} className={section === label ? "active" : ""}
              aria-current={section === label ? "page" : undefined}>
              <Icon size={21} />{label}
            </Link>
          ))}
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
          <div className="breadcrumb" aria-label="Breadcrumb">
            AICTE portal <CaretRight size={12} />
            {path !== parent.to && <><Link to={parent.to} aria-label={`Back to ${section}`}>{section}</Link><CaretRight size={12} /></>}
            <strong>{currentLabel}</strong>
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
                onClick={() => {
                  if (!showAlerts) setAlertsVersion((x) => x + 1);
                  setShowAlerts(!showAlerts);
                }}
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
                  {alertsError ? (
                    <ErrorBox message={alertsError} />
                  ) : !alerts ? (
                    <Loading />
                  ) : alerts.results.length ? (
                    alerts.results.map((n) => (
                      <Link
                        key={n.id}
                        to={`/cases/${n.case_id}${n.escalation_id ? "#escalations" : ""}`}
                      >
                        <strong>{n.reference}</strong>
                        <span>
                          {n.kind === "escalation"
                            ? `Supervisory review · ${n.escalation_status}`
                            : typeof n.kind === "string"
                              ? n.kind.replaceAll("_", " ")
                              : "Notification"}{" "}
                          ·{" "}
                          {date(
                            n.kind === "escalation" ? n.created_at : n.deadline,
                          )}
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
          {section === "My Work" && path !== "/work" && (
            <nav className="section-links" aria-label="Work navigation">
              <Link to="/work">Work overview</Link>
              <Link to="/cases">Case registry</Link>
              {isCoord ? <>
                <Link to="/coordination/workspace">Coordination workspace</Link>
                <Link to="/coordination">Coordination queue</Link>
                <Link to="/escalations">Escalations</Link>
              </> : user.role === "officer" && <Link to="/coordination/requests">Coordination actions</Link>}
            </nav>
          )}
          {section === "Data Imports" && (
            <nav className="section-links" aria-label="Import navigation">
              <Link to="/imports">Spreadsheets</Link>
              <Link to="/imports/sources">Source intake</Link>
              <Link to="/imports/source-jobs">Source-upload history</Link>
            </nav>
          )}
          {section === "Reports" && isCoord && (
            <nav className="section-links" aria-label="Report navigation">
              <Link to="/reports">Complaint reports</Link>
              <Link to="/movements">Case movements</Link>
              <Link to="/coordination/activity">Cross-bureau activity</Link>
            </nav>
          )}
          <PageBoundary>
            <Routes>
              <Route path="/work" element={<MyWork user={user} />} />
              <Route
                path="/coordination/workspace"
                element={
                  <CoordinationWorkspace
                    user={user}
                    options={options || emptyOptions}
                  />
                }
              />
              <Route
                path="/coordination/workspace/:id"
                element={
                  <CoordinationRecordPage
                    user={user}
                    options={options || emptyOptions}
                  />
                }
              />
              <Route
                path="/coordination/requests"
                element={<CoordinationRequests user={user} />}
              />
              <Route path="/movements" element={<MovementsPage />} />
              <Route
                path="/coordination/activity"
                element={
                  isCoord ? (
                    <CoordinationNotices filters={location.search.slice(1)} />
                  ) : (
                    <ErrorBox message="Coordination access is required." />
                  )
                }
              />
              <Route
                path="/relationships/new"
                element={<ManualRelationship user={user} />}
              />
              <Route
                path="/escalations"
                element={<EscalationQueue user={user} />}
              />
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
              <Route
                path="/imports"
                element={
                  <Imports user={user} options={options || emptyOptions} />
                }
              />
              <Route path="/imports/sources" element={<SourceIntake />} />
              <Route path="/imports/source-jobs" element={<SourceJobs />} />
              <Route
                path="/imports/:id/rows"
                element={<SourceRows user={user} />}
              />
              <Route
                path="/imports/:id"
                element={<ImportDetail user={user} />}
              />
              <Route
                path="/reports"
                element={<Report filters={location.search.slice(1)} />}
              />
              <Route
                path="/"
                element={
                  <DashboardHome
                    user={user}
                    options={options || emptyOptions}
                  />
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
                element={
                  <Detail user={user} options={options || emptyOptions} />
                }
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
          </PageBoundary>
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
          <select
            aria-label="Classification filter"
            value={params.get("classification") || ""}
            onChange={(e) => filter("classification", e.target.value)}
          >
            <option value="">All classifications</option>
            {Object.entries(classifications).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
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
          <label>
            <input type="checkbox" checked={params.get("approaching") === "true"}
              onChange={(e) => filter("approaching", e.target.checked ? "true" : "")} />{" "}
            Due in next seven days
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
  const [institutionSearch,setInstitutionSearch] = useState('');
  const [institutionId,setInstitutionId] = useState('');
  const { data: institutions, error: institutionError } = useLoad<Institution[]>(institutionSearch ? `/api/institutions?q=${encodeURIComponent(institutionSearch)}` : '/api/institutions');
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
        <ErrorBox message={institutionError} />
        {!institutions && !institutionError && <Loading />}
        {institutions?.length === 0 && <p role="status">No registry institution matches. Check the name or Permanent ID.</p>}
        <h2>Institution & ownership</h2>
        <div className="form-grid">
          <label className="wide">Find institution by name or Permanent ID
            <input type="search" value={institutionSearch} onChange={e=>{setInstitutionSearch(e.target.value);setInstitutionId('');}} />
            <small>Search the complete registry. Up to 100 matching institutions are shown; choose the canonical record below.</small>
          </label>
          <label>
            Classification
            <select name="classification" required defaultValue="">
              <option value="" disabled>
                Select classification
              </option>
              {Object.entries(classifications).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label className="wide">
            Institution
            <select name="institution" required value={institutionId} onChange={e=>setInstitutionId(e.target.value)}>
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
  const { hash } = useLocation();
  const [refresh, setRefresh] = useState(0);
  const { data: c, error } = useLoad<CaseDetail>(`/api/cases/${id}`, refresh);
  useEffect(() => {
    if (c?.id === id && ["#case-history", "#case-actions", "#case-attachments"].includes(hash)) {
      const target = document.getElementById(hash.slice(1));
      target?.scrollIntoView();
      target?.focus({ preventScroll: true });
    }
  }, [c?.id, id, hash]);
  const [action, setAction] = useState("note"),
    [status, setStatus] = useState("under_review"),
    [bureau, setBureau] = useState(""),
    [officer, setOfficer] = useState(""),
    [due, setDue] = useState(""),
    [reason, setReason] = useState(""),
    [actionError, setActionError] = useState(""),
    [busy, setBusy] = useState(false),
    [success, setSuccess] = useState("");
  const [classification, setClassification] = useState("unclassified"),
    [nextAction, setNextAction] = useState(""),
    [nextDate, setNextDate] = useState(""),
    [savedVersion, setSavedVersion] = useState(0),
    [editingVersion, setEditingVersion] = useState<number | null>(null),
    [conflict, setConflict] = useState(false);
  const [escalationSubmission, setEscalationSubmission] = useState(() =>
      crypto.randomUUID(),
    ),
    [escalationEditing, setEscalationEditing] = useState(false);
  useEffect(() => {
    setAction("note");
    setReason("");
    setNextAction("");
    setNextDate("");
    setSavedVersion(0);
    setEditingVersion(null);
    setConflict(false);
    setActionError("");
    setSuccess("");
    setEscalationSubmission(crypto.randomUUID());
    setEscalationEditing(false);
  }, [id]);
  useEffect(() => {
    if (
      c?.matching_state === "pending" &&
      editingVersion === null &&
      !escalationEditing
    ) {
      const timer = setTimeout(() => setRefresh((x) => x + 1), 4000);
      return () => clearTimeout(timer);
    }
  }, [c, editingVersion, escalationEditing]);
  const writable = ["officer", "coordinator"].includes(user.role);
  async function act(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setActionError("");
    setSuccess("");
    try {
      await api(
        `/api/cases/${id}/${action === "escalate" ? "escalations" : "actions"}`,
        {
          method: "POST",
          body: JSON.stringify({
            ...(action === "escalate"
              ? { submission_id: escalationSubmission }
              : { kind: action }),
            expected_version: editingVersion ?? c!.version,
            reason,
            ...(action === "classification" ? { classification } : {}),
            ...(action === "next_action"
              ? { next_action: nextAction, next_action_date: nextDate || null }
              : {}),
            ...(action === "status" ? { status } : {}),
            ...(action === "transfer" ? { bureau } : {}),
            ...(action === "assign"
              ? { assigned_to: officer ? Number(officer) : null }
              : {}),
            ...(action === "deadline"
              ? { due_at: new Date(due).toISOString() }
              : {}),
          }),
        },
      );
      setReason("");
      setSavedVersion((editingVersion ?? c!.version) + 1);
      if (action === "escalate") {
        setAction("note");
        setEscalationSubmission(crypto.randomUUID());
      }
      setEditingVersion(null);
      setConflict(false);
      setSuccess("Action recorded in the case history.");
      setRefresh((x) => x + 1);
    } catch (e) {
      setActionError((e as Error).message);
      if (e instanceof ApiError && e.status === 409) setConflict(true);
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
      {id && <CaseIntelligence key={id} id={id} user={user} />}
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
            {c.has_unresolved_escalation && (
              <span className="bureau-tag">Unresolved escalation</span>
            )}
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
                      <dt>Classification</dt>
                      <dd>{classifications[c.classification]}</dd>
                    </div>
                    <div>
                      <dt>Next action</dt>
                      <dd>{c.next_action || "No next action recorded"}</dd>
                    </div>
                    <div>
                      <dt>Expected action date</dt>
                      <dd>{date(c.next_action_date)}</dd>
                    </div>
                    <div>
                      <dt>Source</dt>
                      <dd>
                        {c.source_system} · {c.source_reference}
                        {c.source_status && (
                          <span className="table-sub">
                            Original source status: {c.source_status} · Source
                            Bureau: {c.source_bureau}
                          </span>
                        )}
                        {c.source_last_seen_at && (
                          <span className="table-sub">
                            Last accepted source upload:{" "}
                            {new Date(c.source_last_seen_at).toLocaleString()}
                          </span>
                        )}
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
                    The expected action date is independent of the case disposal
                    deadline. Matching examines the original allegation summary.
                    Suggestions require human review.
                  </small>
                </div>
              </section>
              <section className="panel detail-card" id="case-history" tabIndex={-1}>
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
                        <small>{a.actor} · Bureau at action: {a.bureau_at_action || "Unknown (historical)"}</small>
                        <ReviewEvidence snapshot={a.changes.review_snapshot} />
                        {Object.keys(a.changes).length > 0 && (
                          <div className="change-details">
                            {Object.entries(a.changes).filter(([key]) => key !== "review_snapshot").map(([key, value]) => (
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
              <CaseEscalations
                key={c.id}
                caseId={c.id}
                user={user}
                onChanged={() => setRefresh((x) => x + 1)}
                onEditing={setEscalationEditing}
              />
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
                  <form
                    className="card-body action-form"
                    id="case-actions"
                    tabIndex={-1}
                    onSubmit={act}
                    onChangeCapture={() => {
                      if (editingVersion === null) setEditingVersion(c.version);
                    }}
                  >
                    <fieldset disabled={busy || c.version < savedVersion} style={{border:0, padding:0, margin:0, minWidth:0, display:'grid', gap:16}}>
                    <legend className="sr-only">Case action</legend>
                    <ErrorBox message={actionError} />
                    {conflict && (
                      <div role="alert">
                        <p>
                          This case changed. Your draft is retained; reload
                          before making another update.
                        </p>
                        <button
                          type="button"
                          className="button secondary"
                          onClick={() => {
                            setAction("note");
                            setReason("");
                            setNextAction("");
                            setNextDate("");
                            setEditingVersion(null);
                            setConflict(false);
                            setActionError("");
                            setRefresh((x) => x + 1);
                          }}
                        >
                          Reload case and discard draft
                        </button>
                      </div>
                    )}
                    {success && (
                      <p role="status" className="success">
                        {success}
                      </p>
                    )}
                    <label>
                      Action
                      <select
                        value={action}
                        onChange={(e) => {
                          setAction(e.target.value);
                          if (e.target.value === "next_action") {
                            setNextAction(c.next_action);
                            setNextDate(c.next_action_date || "");
                          }
                          if (e.target.value === "classification")
                            setClassification(c.classification);
                        }}
                      >
                        <option value="note">Add a note / correction</option>
                        <option value="status">Update status</option>
                        {c.status !== "disposed" &&
                          !c.has_unresolved_escalation && (
                            <option value="escalate">
                              Escalate for supervisory review
                            </option>
                          )}
                        {c.status !== "disposed" && (
                          <option value="next_action">
                            Set / clear next action
                          </option>
                        )}
                        {user.role === "coordinator" && (
                          <>
                            <option value="classification">
                              Correct classification
                            </option>
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
                    {action === "classification" && (
                      <label>
                        New classification
                        <select
                          value={classification}
                          onChange={(e) => setClassification(e.target.value)}
                        >
                          {Object.entries(classifications).map(
                            ([value, label]) => (
                              <option key={value} value={value}>
                                {label}
                              </option>
                            ),
                          )}
                        </select>
                      </label>
                    )}
                    {action === "next_action" && (
                      <>
                        <label>
                          Next action description
                          <textarea
                            rows={3}
                            maxLength={1000}
                            value={nextAction}
                            onChange={(e) => setNextAction(e.target.value)}
                          />
                        </label>
                        <label>
                          Expected action date (optional)
                          <input
                            type="date"
                            value={nextDate}
                            onChange={(e) => setNextDate(e.target.value)}
                          />
                        </label>
                        <small className="muted">
                          Independent of the disposal deadline. Clear both
                          fields to remove the next action. Closing preserves
                          the previous values in history.
                        </small>
                      </>
                    )}
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
                      {action === "escalate"
                        ? "Escalation reason"
                        : action === "status" && status === "disposed"
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
                    <button disabled={busy || conflict || escalationEditing}>
                      {busy ? "Saving…" : "Record action"}
                      <ArrowRight size={17} />
                    </button>
                    <small className="muted">
                      Actions are timestamped and preserved. Version {c.version}
                      .
                    </small>
                    </fieldset>
                  </form>
                ) : (
                  <p className="card-body muted">
                    Your audit access is read-only.
                  </p>
                )}
              </section>
              <section className="panel detail-card">
                <div className="panel-heading">
                  <h2 id="case-attachments" tabIndex={-1}>Supporting documents</h2>
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
      >
        {user.role === "coordinator" && (
          <Link
            className="button"
            to={
              params.get("institution")
                ? `/relationships/new?institution=${params.get("institution")}`
                : "/institutions"
            }
          >
            Create manual relationship
          </Link>
        )}
      </Heading>
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
        <a
          className="button secondary"
          href={`/api/relationships.csv?${params}`}
        >
          Download relationship CSV
        </a>
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
                      <strong>
                        {typeof o.score === "number"
                          ? `${o.score.toFixed(3)} cosine`
                          : "Not model-scored"}
                      </strong>
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
      p.decision === "pending" ? "" : p.decision,
    ),
    [reason, setReason] = useState(p.reason),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [conflict, setConflict] = useState(false);
  async function save(e: FormEvent) {
    e.preventDefault();
    if (!decision || !reason.trim()) {
      setError("Choose a relationship and enter a review reason.");
      return;
    }
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
      if (e instanceof ApiError && e.status === 409) setConflict(true);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="panel pair-review" aria-label="Case comparison">
      <div className="panel-heading">
        <div>
          <h2>Review potential relationship</h2>
          <p>
            <Link
              className="institution-link"
              to={`/institutions/${p.left.institution.id}`}
            >
              {p.left.institution.name}
            </Link>
          </p>
        </div>
        <Badge status={p.decision} />
      </div>
      <div className="comparison">
        {[p.left, p.right].map((c, i) => (
          <article key={c.id} aria-label={`Complaint ${i === 0 ? "A" : "B"}`}>
            <h3 className="eyebrow">Complaint {i === 0 ? "A" : "B"}</h3>
            <Link className="case-ref" to={`/cases/${c.id}`}>
              {c.reference}
              <ArrowUpRight size={15} />
            </Link>
            <dl>
              <dt>Institution</dt>
              <dd><Link className="institution-link" to={`/institutions/${c.institution.id}`}>{c.institution.name}</Link></dd>
              <dt>Permanent ID</dt>
              <dd>{c.institution.permanent_id || "Not recorded"}</dd>
              <dt>Current Bureau</dt>
              <dd>{c.bureau || "Not recorded"}</dd>
              <dt>Source system</dt>
              <dd>{c.source_system || "Not recorded"}</dd>
              <dt>Source reference</dt>
              <dd>{c.source_reference || "Not recorded"}</dd>
              <dt>Category</dt>
              <dd className="capitalize">{c.category || "Not recorded"}</dd>
              <dt>Classification</dt>
              <dd>{classifications[c.classification] || "Not recorded"}</dd>
              <dt>Received</dt>
              <dd>{date(c.received_at)}</dd>
              <dt>Incident date</dt>
              <dd>{date(c.incident_date)}</dd>
              <dt>Status</dt>
              <dd>
                <Badge status={c.status} />
              </dd>
            </dl>
            <h4>Original allegation summary</h4>
            <p className="description">{c.summary || "Not recorded"}</p>
            <h4>Original complaint description</h4>
            <p className="description">{c.description || "Not recorded"}</p>
            <div className="comparison-links">
              <Link to={`/cases/${c.id}`}>Open original case</Link>
              <Link to={`/cases/${c.id}#case-history`}>Case actions and history</Link>
              <Link to={`/cases/${c.id}#case-attachments`}>Attachments</Link>
            </div>
          </article>
        ))}
      </div>
      <PairEvidence pair={p} />
      {p.decision !== "pending" && (p.review_snapshot ? <ReviewEvidence snapshot={p.review_snapshot} /> : <p className="card-body muted">Legacy review: no decision-time evidence snapshot recorded.</p>)}
      {user.role === "coordinator" ? (
        <form className="review-form" onSubmit={save}>
          <h3>Your coordination decision</h3>
          <ErrorBox message={error} />
          {conflict && (
            <button type="button" className="secondary" onClick={onSaved}>
              Reload relationship and discard draft
            </button>
          )}
          <fieldset className="decision-fieldset">
            <legend>Choose a relationship (required)</legend>
            <div className="decision-options">
            {["same_incident", "related_issue", "unrelated"].map((d) => (
              <label key={d} className={decision === d ? "selected" : ""}>
                <input
                  type="radio"
                  name="decision"
                  required
                  value={d}
                  checked={decision === d}
                  onChange={() => setDecision(d)}
                />
                {labels[d]}
              </label>
            ))}
            </div>
          </fieldset>
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
            <button disabled={busy || conflict}>
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
