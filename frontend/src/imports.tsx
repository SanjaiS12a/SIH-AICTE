import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { api } from "./api";
import { validDashboard } from "./dashboard-data";
import { ManagementPanels } from "./management";
import { IncidentSummary } from "./incident-summary";
import type { Dashboard, User, Options } from "./api";

type Job = {
  source_system?: string;
  source_bureau?: string | null;
  registered_at?: string | null;
  status_mapping?: Record<string, string>;
  id: string;
  kind: string;
  filename: string;
  state: string;
  error: string;
  total: number;
  counts: Record<string, number>;
  matching: Record<string, number>;
  headers: string[];
  fields: string[];
  required: string[];
  mapping: Record<string, string>;
  preview: {
    number: number;
    raw: Record<string, string>;
    state: string;
    error: string;
  }[];
  created_at: string;
};
type Summary = {
  row_count: number;
  kind: string;
  period: string;
  periods: string[];
  totals: Record<string, number>;
  rows: {
    institution: string;
    institution_id?: string;
    bureau: string;
    category: string;
    period: string;
    counts: Record<string, number>;
  }[];
  generated_at: string;
};
type Facts = {
  total: number;
  pending: number;
  overdue: number;
  disposed: number;
  generated_at: string;
  matching: Record<string, number>;
  workload: { bureau__code: string; count: number }[];
  categories: { category: string; count: number }[];
  ageing: { name: string; count: number }[];
  trend: { month: string; received: number; disposed: number }[];
  overlap_reviews?: number;
};

type PollResult<T> = {
  url: string | null;
  refresh: number;
  data: T | null;
  error: string;
};
export function usePoll<T>(
  url: string | null,
  milliseconds = 0,
  refresh = 0,
  validate?: (value: unknown) => boolean,
) {
  const [result, setResult] = useState<PollResult<T>>({
    url: null,
    refresh: 0,
    data: null,
    error: "",
  });
  useEffect(() => {
    let alive = true,
      loading = false;
    let controller: AbortController | null = null;
    let timer: number | undefined;
    setResult({ url, refresh, data: null, error: "" });
    if (!url) return;
    const requestUrl = url;
    async function load() {
      if (document.hidden || loading) return;
      loading = true;
      controller = new AbortController();
      try {
        const data = await api<T>(requestUrl, { signal: controller.signal });
        if (validate && !validate(data))
          throw new Error(
            "The server returned incomplete or invalid data. Refresh the page or try again later.",
          );
        if (alive) {
          setResult({ url: requestUrl, refresh, data, error: "" });
          if (
            data &&
            typeof data === "object" &&
            "state" in data &&
            ["preview", "complete", "failed", "matching_failed"].includes(
              String(data.state),
            )
          )
            clearInterval(timer);
        }
      } catch (error) {
        if (alive && (error as Error).name !== "AbortError")
          setResult((previous) => ({
            ...previous,
            error: (error as Error).message,
          }));
      } finally {
        loading = false;
      }
    }
    void load();
    timer = milliseconds ? window.setInterval(load, milliseconds) : undefined;
    document.addEventListener("visibilitychange", load);
    return () => {
      alive = false;
      controller?.abort();
      clearInterval(timer);
      document.removeEventListener("visibilitychange", load);
    };
  }, [url, milliseconds, refresh, validate]);
  return result.url === url && result.refresh === refresh
    ? { data: result.data, error: result.error }
    : { data: null, error: "" };
}

function record(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === "object" && !Array.isArray(value);
}
function number(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value) && value >= 0;
}
function numbers(value: unknown) {
  return record(value) && Object.values(value).every(number);
}
function strings(value: unknown) {
  return Array.isArray(value) && value.every((x) => typeof x === "string");
}
function rows(value: unknown, keys: string[], amounts: string[]) {
  return (
    Array.isArray(value) &&
    value.every(
      (x) =>
        record(x) &&
        keys.every((key) => typeof x[key] === "string") &&
        amounts.every((key) => number(x[key])),
    )
  );
}
function isJob(value: unknown): boolean {
  return (
    record(value) &&
    ["id", "filename", "state", "kind", "error", "created_at"].every(
      (key) => typeof value[key] === "string",
    ) &&
    ["complaints", "monthly", "snapshot"].includes(String(value.kind)) &&
    [
      "preview",
      "importing",
      "matching",
      "complete",
      "failed",
      "matching_failed",
    ].includes(String(value.state)) &&
    number(value.total) &&
    numbers(value.counts) &&
    numbers(value.matching) &&
    strings(value.headers) &&
    strings(value.fields) &&
    strings(value.required) &&
    record(value.mapping) &&
    Object.values(value.mapping).every((x) => typeof x === "string") &&
    Array.isArray(value.preview) &&
    value.preview.every(
      (x) =>
        record(x) &&
        number(x.number) &&
        typeof x.state === "string" &&
        typeof x.error === "string" &&
        record(x.raw) &&
        Object.values(x.raw).every((v) => typeof v === "string"),
    )
  );
}
const isExport = (value: unknown) =>
  record(value) &&
  ["pending", "complete", "failed"].includes(String(value.state)) &&
  typeof value.error === "string";
const isJobs = (value: unknown) => Array.isArray(value) && value.every(isJob);
function isReport(value: unknown): boolean {
  if (
    !record(value) ||
    typeof value.generated_at !== "string" ||
    !Number.isFinite(Date.parse(value.generated_at))
  )
    return false;
  if ("kind" in value)
    return (
      ["monthly", "snapshot"].includes(String(value.kind)) &&
      number(value.row_count) &&
      typeof value.period === "string" &&
      strings(value.periods) &&
      numbers(value.totals) &&
      rows(value.rows, ["institution", "bureau", "category", "period"], []) &&
      (value.rows as Record<string, unknown>[]).every((x) => numbers(x.counts))
    );
  if ("management" in value && !validDashboard(value)) return false;
  return (
    ["total", "pending", "overdue", "disposed"].every((key) =>
      number(value[key]),
    ) &&
    numbers(value.matching) &&
    rows(value.workload, ["bureau__code"], ["count"]) &&
    rows(value.categories, ["category"], ["count"]) &&
    rows(value.ageing, ["name"], ["count"]) &&
    rows(value.trend, ["month"], ["received", "disposed"])
  );
}
function ErrorNotice({ text }: { text: string }) {
  return text ? (
    <div className="error" role="alert">
      {text}
    </div>
  ) : null;
}
export function ExportButton({ filters }: { filters: string }) {
  const [id, setId] = useState(""),
    [error, setError] = useState("");
  useEffect(() => {
    setId("");
    setError("");
  }, [filters]);
  const { data } = usePoll<{ state: string; error: string }>(
    id ? `/api/exports/${id}` : null,
    id ? 2000 : 0,
    0,
    isExport,
  );
  async function start() {
    try {
      setError("");
      const job = await api<{ id: string }>("/api/exports", {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(new URLSearchParams(filters))),
      });
      if (typeof job.id !== "string" || !job.id)
        throw new Error("The server did not return a valid export identifier.");
      setId(job.id);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  return (
    <>
      <button
        className="button secondary"
        disabled={
          !!id && data?.state !== "failed" && data?.state !== "complete"
        }
        onClick={start}
      >
        {data?.state === "complete"
          ? "Export again"
          : id && data?.state !== "failed"
            ? "Preparing CSV…"
            : "Export report"}
      </button>
      {data?.state === "complete" && (
        <a className="button" href={`/api/exports/${id}/download`}>
          Download CSV
        </a>
      )}
      <ErrorNotice text={error || data?.error || ""} />
    </>
  );
}
export function Imports({ user, options }: { user: User; options: Options }) {
  const { data: jobs, error } = usePoll<Job[]>("/api/imports", 5000, 0, isJobs);
  const [kind, setKind] = useState("complaints"),
    [busy, setBusy] = useState(false),
    [failure, setFailure] = useState("");
  const [sourceMode, setSourceMode] = useState(false);
  const [statusPairs, setStatusPairs] = useState([
    { source: "", target: "registered" },
  ]);
  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setFailure("");
    try {
      const form = new FormData(event.currentTarget);
      form.set("kind", kind);
      if (sourceMode && kind === "complaints") {
        const mapped = statusPairs.filter((p) => p.source.trim());
        if (new Set(mapped.map((p) => p.source.trim())).size !== mapped.length)
          throw new Error("Use each source status label only once.");
        form.set(
          "status_mapping",
          JSON.stringify(
            Object.fromEntries(mapped.map((p) => [p.source.trim(), p.target])),
          ),
        );
      }
      const job = await api<Job>("/api/imports", {
        method: "POST",
        body: form,
      });
      window.location.assign(`/imports/${job.id}`);
    } catch (e) {
      setFailure((e as Error).message);
      setBusy(false);
    }
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow">DATA & REPORTING</div>
          <h1>Import data</h1>
          <p>
            Turn complaint records or official summaries into traceable reports.
          </p>
        </div>
      </div>
      <ErrorNotice text={failure || error} />
      <Link className="button secondary" to="/imports/sources">
        Bureau-source uploads and reconciliation
      </Link>
      {["officer", "coordinator"].includes(user.role) && (
        <section className="panel import-upload">
          <h2>Upload a spreadsheet</h2>
          <p>
            One sheet per upload · CSV or XLSX · 10,000 rows · 20 MB maximum
          </p>
          <form onSubmit={upload} className="import-form">
            <label>
              Dataset type
              <select value={kind} onChange={(e) => setKind(e.target.value)}>
                <option value="complaints">Individual complaints</option>
                <option value="monthly">Monthly receipts and disposals</option>
                <option value="snapshot">Status snapshot</option>
              </select>
            </label>
            <label>
              Spreadsheet
              <input name="file" type="file" accept=".xlsx,.csv" required />
            </label>
            {kind === "complaints" && (
              <>
                <label>
                  <input
                    type="checkbox"
                    checked={sourceMode}
                    onChange={(e) => setSourceMode(e.target.checked)}
                  />
                  This is a Bureau source upload
                </label>
                {sourceMode && (
                  <fieldset className="wide">
                    <legend>Source identity and status mapping</legend>
                    <label>
                      Source ID
                      <input
                        required
                        name="source_system"
                        maxLength={40}
                        pattern="[A-Za-z0-9._-]+"
                        placeholder="e.g. demo-rb"
                      />
                    </label>
                    <label>
                      Source Bureau
                      <select
                        name="source_bureau"
                        required
                        aria-label="Source Bureau"
                        defaultValue={user.bureau || ""}
                      >
                        <option value="">Choose Bureau</option>
                        {options.bureaus.map((b) => (
                          <option key={b.code} value={b.code}>
                            {b.name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <p>
                      Keep the same Source ID on repeat uploads. Source
                      references identify records within that source. Unknown
                      institutions must be corrected; changed records are
                      reviewed without overwriting portal data.
                    </p>
                    <p>
                      Map source status labels to portal statuses. Canonical
                      status values also work without a mapping. A source status
                      does not change case ownership.
                    </p>
                    {statusPairs.map((p, i) => (
                      <div className="form-grid" key={i}>
                        <label>
                          Source status {i + 1}
                          <input
                            value={p.source}
                            maxLength={80}
                            onChange={(e) =>
                              setStatusPairs((old) =>
                                old.map((p, n) =>
                                  n === i
                                    ? { ...p, source: e.target.value }
                                    : p,
                                ),
                              )
                            }
                          />
                        </label>
                        <label>
                          Portal status {i + 1}
                          <select
                            aria-label={`Portal status ${i + 1}`}
                            value={p.target}
                            onChange={(e) =>
                              setStatusPairs((old) =>
                                old.map((p, n) =>
                                  n === i
                                    ? { ...p, target: e.target.value }
                                    : p,
                                ),
                              )
                            }
                          >
                            <option value="registered">Registered</option>
                            <option value="under_review">Under review</option>
                            <option value="awaiting_response">
                              Awaiting response
                            </option>
                            <option value="disposed">Closed</option>
                          </select>
                        </label>
                      </div>
                    ))}
                    <button
                      type="button"
                      className="secondary"
                      disabled={statusPairs.length >= 50}
                      onClick={() =>
                        setStatusPairs((old) => [
                          ...old,
                          { source: "", target: "registered" },
                        ])
                      }
                    >
                      Add status mapping
                    </button>
                  </fieldset>
                )}
              </>
            )}
            <button disabled={busy}>
              {busy ? "Validating…" : "Upload and preview"}
            </button>
            <a className="text-button" href={`/api/imports/templates/${kind}`}>
              Download template
            </a>
          </form>
          <p className="policy-note">
            Summaries stay separate from case records. Uploading data never
            retrains the model.
          </p>
        </section>
      )}
      <section className="panel">
        <div className="panel-heading">
          <h2>Recent imports</h2>
          <span>Refreshes every 5 seconds</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Source file</th>
                <th>Dataset</th>
                <th>Rows</th>
                <th>Progress</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {jobs?.map((j) => (
                <tr key={j.id}>
                  <td>
                    <Link to={`/imports/${j.id}`}>{j.filename} →</Link>
                  </td>
                  <td>{j.kind}</td>
                  <td>{j.total}</td>
                  <td>{j.state.replaceAll("_", " ")}</td>
                  <td>{new Date(j.created_at).toLocaleString("en-IN")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {jobs?.length === 0 && (
          <p className="empty">No imports yet. Download a template to begin.</p>
        )}
        {!jobs && !error && <p>Loading imports…</p>}
      </section>
    </>
  );
}
export function ImportDetail({ user }: { user: User }) {
  const { id } = useParams();
  const [refresh, setRefresh] = useState(0),
    [mapping, setMapping] = useState<Record<string, string> | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const { data: job, error: loadError } = usePoll<Job>(
    `/api/imports/${id}`,
    2000,
    refresh,
    isJob,
  );
  async function act(action: string) {
    setBusy(true);
    setError("");
    try {
      await api(`/api/imports/${id}`, {
        method: "POST",
        body: JSON.stringify({ action, mapping: mapping || job?.mapping }),
      });
      setMapping(null);
      setRefresh((x) => x + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  if (!job)
    return (
      <>
        <ErrorNotice text={loadError} />
        <p>Loading import…</p>
      </>
    );
  const processed =
    (job.counts.imported || 0) +
    (job.counts.duplicate || 0) +
    (job.counts.conflict || 0) +
    (job.counts.resolved || 0) +
    (job.counts.rejected || 0);
  return (
    <>
      <Link to="/imports" className="text-button">
        ← All imports
      </Link>
      <div className="page-heading">
        <div>
          <div className="eyebrow">{job.kind.toUpperCase()} DATASET</div>
          <h1>{job.filename}</h1>
          <p>
            {job.state.replaceAll("_", " ")} ·{" "}
            {job.total.toLocaleString("en-IN")} rows · Refreshes every 2 seconds
          </p>
        </div>
        <Link className="button secondary" to={`/reports?import_id=${id}`}>
          Open report
        </Link>
      </div>
      <ErrorNotice text={error || loadError || job.error} />
      {job.source_system && (
        <section className="panel card-body">
          <h2>Bureau source: {job.source_system}</h2>
          <p>
            Original Bureau: {job.source_bureau}. Status labels are normalized
            using the recorded upload mapping; source references and original
            statuses remain preserved.
          </p>
          <p>
            Intake completed:{" "}
            {job.registered_at
              ? new Date(job.registered_at).toLocaleString()
              : "Not yet completed"}
            . This is a file upload, not a live connection to a Bureau system.
          </p>
        </section>
      )}
      <Link className="button secondary" to={`/imports/${id}/rows`}>
        View all rows and source conflicts
      </Link>
      <div className="import-stats" aria-live="polite">
        {[
          ["Validated", job.total - (job.counts.pending || 0)],
          ["Ready", job.counts.ready || 0],
          ["Imported", job.counts.imported || 0],
          ["Duplicates", job.counts.duplicate || 0],
          ["Rejected", job.counts.rejected || 0],
          ["Source conflicts", job.counts.conflict || 0],
          ["Conflicts reviewed", job.counts.resolved || 0],
          ["Matched", job.matching.complete || 0],
        ].map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      {job.state !== "preview" && (
        <section className="panel import-progress">
          <label>
            Import progress
            <progress max={job.total || 1} value={processed} />
          </label>
          <p>
            {processed} / {job.total} rows processed. Matching pending:{" "}
            {job.matching.pending || 0}; failed: {job.matching.failed || 0}.
          </p>
        </section>
      )}
      {job.state === "preview" && (
        <section className="panel mapping">
          <h2>Map and validate columns</h2>
          <p>
            Required fields are marked *. Confirming imports valid rows;
            rejected rows remain available in the error report.
          </p>
          <div className="mapping-grid">
            {job.fields.map((field) => (
              <label key={field}>
                {field.replaceAll("_", " ")}
                {job.required.includes(field) ? " *" : ""}
                <select
                  value={(mapping || job.mapping)[field] || ""}
                  onChange={(e) => {
                    const next = { ...(mapping || job.mapping) };
                    if (e.target.value) next[field] = e.target.value;
                    else delete next[field];
                    setMapping(next);
                  }}
                >
                  <option value="">Not mapped</option>
                  {job.headers.map((h) => (
                    <option key={h}>{h}</option>
                  ))}
                </select>
              </label>
            ))}
          </div>
          <div className="actions">
            <button
              className="secondary"
              disabled={busy}
              onClick={() => act("preview")}
            >
              Validate mapping
            </button>
            <button
              disabled={
                busy ||
                !!mapping ||
                !job.mapping ||
                Object.keys(job.mapping).length === 0 ||
                (job.counts.ready || 0) +
                  (job.counts.duplicate || 0) +
                  (job.counts.conflict || 0) ===
                  0
              }
              onClick={() => act("confirm")}
            >
              Confirm import
            </button>
          </div>
          {mapping && <p>Validate the changed mapping before confirming.</p>}
        </section>
      )}
      {["failed", "matching_failed"].includes(job.state) &&
        ["coordinator", "officer"].includes(user.role) && (
          <button disabled={busy} onClick={() => act("retry")}>
            Retry unfinished work
          </button>
        )}
      <section className="panel">
        <div className="panel-heading">
          <h2>Row preview</h2>
          <a className="text-button" href={`/api/imports/${id}/errors.csv`}>
            Download errors CSV
          </a>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Row</th>
                <th>Source values</th>
                <th>State / validation</th>
              </tr>
            </thead>
            <tbody>
              {job.preview.map((row) => (
                <tr key={row.number}>
                  <td>{row.number}</td>
                  <td>
                    <div className="row-values">
                      {Object.entries(row.raw)
                        .slice(0, 6)
                        .map(([k, v]) => (
                          <span key={k}>
                            <small>{k}</small>
                            {v}
                          </span>
                        ))}
                    </div>
                  </td>
                  <td>
                    {row.state}
                    <p>{row.error}</p>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
function Bars({
  title,
  rows,
}: {
  title: string;
  rows: { name: string; count: number }[];
}) {
  return (
    <section className="panel report-chart">
      <h2>{title}</h2>
      <div style={{ height: 240 }}>
        <ResponsiveContainer>
          <BarChart
            data={rows}
            layout="vertical"
            margin={{ left: 20, right: 30 }}
          >
            <CartesianGrid stroke="#d0e6d2" horizontal={false} />
            <XAxis type="number" allowDecimals={false} />
            <YAxis type="category" dataKey="name" width={110} />
            <Tooltip />
            <Bar dataKey="count" fill="#138808" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <table className="accessible-data">
        <caption>{title} values</caption>
        <tbody>
          {rows.map((r) => (
            <tr key={r.name}>
              <th>{r.name}</th>
              <td>{r.count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
export function Report({
  filters,
  embedded = false,
  incidentGroups = false,
}: {
  filters: string;
  embedded?: boolean;
  incidentGroups?: boolean;
}) {
  const ReportHeading = embedded ? "h2" : "h1";
  const params = new URLSearchParams(filters),
    id = params.get("import_id");
  const [period, setPeriod] = useState("");
  useEffect(() => setPeriod(""), [id]);
  const { data: job, error: jobError } = usePoll<Job>(
    id ? `/api/imports/${id}` : null,
    id ? 5000 : 0,
    0,
    isJob,
  );
  const url = id
    ? `/api/imports/${id}/report?${period ? `period=${period}&` : ""}${params}`
    : `/api/dashboard?${params}`;
  const { data, error } = usePoll<Facts | Summary>(url, 5000, 0, isReport);
  const summary = data && "kind" in data ? data : null;
  const facts = data && "total" in data ? data : null;
  return (
    <div className="report-workspace">
      <div className="page-heading">
        <div>
          <div className="eyebrow">AICTE · FACTUAL ANALYSIS</div>
          <ReportHeading>Data report</ReportHeading>
          <p>
            {id
              ? job?.filename ||
                (jobError
                  ? "Import source unavailable"
                  : "Loading import source…")
              : "Authorized complaint records"}{" "}
            ·{" "}
            {summary
              ? "Summary statistics — separate from individual cases"
              : "Individual complaints"}
          </p>
        </div>
        <div className="actions no-print">
          <button className="secondary" onClick={() => window.print()}>
            Print / Save PDF
          </button>
          {!summary && <ExportButton filters={filters} />}{" "}
          {summary && (
            <a
              className="button secondary"
              href={`/api/imports/${id}/report.csv?period=${period || summary.period}`}
            >
              Download summary CSV
            </a>
          )}
        </div>
      </div>
      <ErrorNotice text={error || jobError} />
      {facts && incidentGroups && <IncidentSummary filters={filters} allTime={embedded} />}
      {!data && !error && <p>Preparing report…</p>}
      {job && (
        <div className="policy-note">
          Import {job.state.replaceAll("_", " ")} · {job.counts.imported || 0}{" "}
          imported · {job.counts.duplicate || 0} duplicates ·{" "}
          {job.counts.rejected || 0} rejected · {job.matching.complete || 0}{" "}
          matching complete · {job.matching.pending || 0} pending ·{" "}
          {job.matching.failed || 0} failed.{" "}
          <Link to={`/imports/${id}`}>Review data quality →</Link>
        </div>
      )}
      <p className="report-filter">
        Applied filters:{" "}
        {params.toString() || "All records within your authorized scope"}
      </p>
      {facts && (
        <>
          <div className="import-stats">
            {[
              ["Total", facts.total],
              ["Pending", facts.pending],
              ["Overdue", facts.overdue],
              ["Closed", facts.disposed],
              ["Pending pair reviews — either endpoint in scope", facts.overlap_reviews ?? "Restricted"],
            ].map(([label, value]) => (
              <div key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
          <p>
            Matching coverage: {facts.matching?.complete || 0} complete,{" "}
            {facts.matching?.pending || 0} pending,{" "}
            {facts.matching?.failed || 0} failed. Suggestions require human
            review.
          </p>
          {"management" in facts && <ManagementPanels data={facts as unknown as Dashboard} filters={filters} />}
          <div className="report-grid">
            <Bars
              title="Active bureau workload"
              rows={facts.workload.map((x) => ({
                name: x.bureau__code,
                count: x.count,
              }))}
            />
            <Bars
              title="Complaint categories"
              rows={facts.categories.map((x) => ({
                name: x.category,
                count: x.count,
              }))}
            />
            <Bars
              title="Active case ageing (days)"
              rows={facts.ageing.map((x) => ({ name: x.name, count: x.count }))}
            />
            <section className="panel">
              <h2>Monthly receipts and disposals</h2>
              <table>
                <thead>
                  <tr>
                    <th>Month</th>
                    <th>Received</th>
                    <th>Closed</th>
                  </tr>
                </thead>
                <tbody>
                  {facts.trend.map((x) => (
                    <tr key={x.month}>
                      <td>{x.month}</td>
                      <td>{x.received}</td>
                      <td>{x.disposed}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>
          {id && (
            <Link className="text-button" to={`/cases?${filters}`}>
              Open filtered cases →
            </Link>
          )}
        </>
      )}
      {summary && summary.rows.length > 0 && (
        <>
          <div className="filter-bar">
            <label>
              {summary.kind === "snapshot"
                ? "Snapshot date (one date at a time)"
                : "Reporting periods"}
              {summary.kind === "snapshot" ? (
                <select
                  value={period || summary.period}
                  onChange={(e) => setPeriod(e.target.value)}
                >
                  {summary.periods.map((x) => (
                    <option key={x}>{x}</option>
                  ))}
                </select>
              ) : (
                <span>All uploaded months</span>
              )}
            </label>
          </div>
          <div className="import-stats">
            {Object.entries(summary.totals).map(([k, v]) => (
              <div key={k}>
                <span>
                  {k === "disposed" ? "Closed" : k.replaceAll("_", " ")}
                </span>
                <strong>{v.toLocaleString("en-IN")}</strong>
              </div>
            ))}
          </div>
          <Bars
            title={
              summary.kind === "snapshot"
                ? "Cases at selected snapshot"
                : "Monthly flows"
            }
            rows={Object.entries(summary.totals).map(([name, count]) => ({
              name,
              count,
            }))}
          />
          <section className="panel">
            <h2>Source summary rows</h2>
            <p>
              Showing {summary.rows.length} of {summary.row_count} rows.
              Download the CSV for every row.
            </p>
            <p>
              Aggregate data has no complaint text or individual case
              drill-down. Snapshot dates are never summed together.
            </p>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Institution</th>
                    <th>Bureau</th>
                    <th>Category</th>
                    <th>Counts</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.rows.map((x, i) => (
                    <tr key={i}>
                      <td>{x.period}</td>
                      <td>
                        {x.institution_id ? (
                          <Link
                            className="institution-link"
                            to={`/institutions/${x.institution_id}`}
                          >
                            {x.institution}
                          </Link>
                        ) : (
                          x.institution
                        )}
                      </td>
                      <td>{x.bureau}</td>
                      <td>{x.category}</td>
                      <td>
                        {Object.entries(x.counts)
                          .map(([k, v]) => `${k}: ${v}`)
                          .join(" · ")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
      {summary && summary.rows.length === 0 && (
        <p className="empty">
          No imported summary rows yet. This report updates as the import
          completes.
        </p>
      )}
      {data && (
        <p className="updated">
          Refreshed {new Date(data.generated_at).toLocaleString("en-IN")} ·
          Descriptive statistics; no AI-generated findings. 30-day deadlines are
          demonstration policy.
        </p>
      )}
    </div>
  );
}
