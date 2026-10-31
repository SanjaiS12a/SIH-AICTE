import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, ApiError, date } from "./api";
import type { Escalation, Page, User } from "./api";
import { usePoll } from "./imports";
import { Heading, ErrorBox, Loading, Empty, Pagination } from "./ui";

function validEscalations(value: unknown): boolean {
  const p = value as Page<Escalation> | null;
  return (
    !!p &&
    Number.isInteger(p.count) &&
    p.count >= 0 &&
    Array.isArray(p.results) &&
    p.results.every(
      (e) =>
        typeof e.id === "string" &&
        typeof e.case?.id === "string" &&
        typeof e.case?.institution?.name === "string" &&
        typeof e.reason === "string" &&
        typeof e.created_by === "string" &&
        typeof e.created_at === "string" &&
        ["pending", "resolved"].includes(e.status) &&
        typeof e.resolution_reason === "string" &&
        Number.isInteger(e.version) &&
        e.version > 0,
    )
  );
}

function ResolutionForm({
  escalation,
  close,
  saved,
}: {
  escalation: Escalation;
  close: () => void;
  saved: () => void;
}) {
  const [reason, setReason] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [conflict, setConflict] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(`/api/escalations/${escalation.id}/resolve`, {
        method: "POST",
        body: JSON.stringify({ expected_version: escalation.version, reason }),
      });
      saved();
    } catch (e) {
      setError((e as Error).message);
      if (e instanceof ApiError && e.status === 409) setConflict(true);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form
      className="card-body action-form"
      onSubmit={submit}
      aria-label="Resolve escalation"
    >
      <h3>Resolve escalation for {escalation.case.reference}</h3>
      <p>{escalation.reason}</p>
      <ErrorBox message={error} />
      <label>
        Resolution reason
        <textarea
          required
          maxLength={4000}
          rows={3}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
      </label>
      {conflict && (
        <p role="alert">
          This escalation changed. Your draft is retained. Reload to review the
          latest decision before continuing.
        </p>
      )}
      <div className="form-actions">
        <button
          type="button"
          className="secondary"
          disabled={busy}
          onClick={close}
        >
          {conflict
            ? "Reload escalation and discard draft"
            : "Cancel resolution"}
        </button>
        <button disabled={busy || conflict}>
          {busy ? "Resolving…" : "Confirm resolution"}
        </button>
      </div>
      <small className="muted">
        Resolves the supervisory request only. Case ownership, status, deadline
        and next action remain unchanged.
      </small>
    </form>
  );
}

function EscalationList({
  url,
  user,
  params,
  setParams,
  onChanged,
  onEditing,
}: {
  url: string;
  user: User;
  params: URLSearchParams;
  setParams: (params: URLSearchParams) => void;
  onChanged?: () => void;
  onEditing?: (editing: boolean) => void;
}) {
  const [refresh, setRefresh] = useState(0),
    [editing, setEditing] = useState<Escalation | null>(null),
    [message, setMessage] = useState("");
  const { data, error } = usePoll<Page<Escalation>>(
    url,
    editing ? 0 : 5000,
    refresh,
    validEscalations,
  );
  useEffect(() => {
    onEditing?.(!!editing);
    return () => onEditing?.(false);
  }, [editing, onEditing]);
  function finish(saved: boolean) {
    setEditing(null);
    setRefresh((x) => x + 1);
    if (saved) {
      setMessage("Escalation resolved and recorded in case history.");
      onChanged?.();
    }
  }
  return (
    <section
      className="panel detail-card"
      id="escalations"
      aria-label="Escalation history"
    >
      <div className="panel-heading">
        <h2>Escalation history</h2>
        <span className="muted">{data ? `${data.count} requests` : ""}</span>
      </div>
      <p className="card-body muted">
        Supervisory requests remain visible after transfer or case closure. They
        require a separate coordinator resolution.
      </p>
      <ErrorBox message={error} />
      {message && (
        <p role="status" className="card-body success">
          {message}
        </p>
      )}
      {!data && !error && <Loading />}
      {data && (
        <>
          {data.results.length ? (
            <div
              className="table-scroll"
              role="region"
              aria-label="Escalations"
              tabIndex={0}
            >
              <table>
                <thead>
                  <tr>
                    <th>Case / institution</th>
                    <th>Request</th>
                    <th>Status / resolution</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {data.results.map((e) => (
                    <tr key={e.id}>
                      <td>
                        <Link className="case-ref" to={`/cases/${e.case.id}`}>
                          {e.case.reference}
                        </Link>
                        <Link
                          className="table-sub institution-link"
                          to={`/institutions/${e.case.institution.id}`}
                        >
                          {e.case.institution.name}
                        </Link>
                        <span className="table-sub">{e.case.bureau}</span>
                      </td>
                      <td>
                        <p className="description">{e.reason}</p>
                        <span className="table-sub">
                          {e.created_by} ·{" "}
                          {new Date(e.created_at).toLocaleString("en-IN")}
                        </span>
                      </td>
                      <td>
                        <strong>
                          {e.status === "pending"
                            ? "Pending review"
                            : "Resolved"}
                        </strong>
                        {e.status === "resolved" && (
                          <>
                            <p>{e.resolution_reason}</p>
                            <span className="table-sub">
                              {e.resolved_by} · {date(e.resolved_at)}
                            </span>
                          </>
                        )}
                      </td>
                      <td>
                        {user.role === "coordinator" &&
                        e.status === "pending" ? (
                          <button
                            className="secondary small"
                            disabled={!!editing}
                            onClick={() => {
                              setEditing(e);
                              setMessage("");
                            }}
                          >
                            Resolve escalation
                          </button>
                        ) : (
                          <span className="muted">
                            {e.status === "resolved"
                              ? "Recorded"
                              : "Coordinator review required"}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty>No escalations match this view.</Empty>
          )}
          {!editing && (
            <Pagination data={data} params={params} setParams={setParams} />
          )}
        </>
      )}
      {editing && (
        <ResolutionForm
          escalation={editing}
          close={() => finish(false)}
          saved={() => finish(true)}
        />
      )}
    </section>
  );
}

export function CaseEscalations({
  caseId,
  user,
  onChanged,
  onEditing,
}: {
  caseId: string;
  user: User;
  onChanged: () => void;
  onEditing: (editing: boolean) => void;
}) {
  const [params, setParams] = useState(new URLSearchParams());
  return (
    <EscalationList
      url={`/api/cases/${caseId}/escalations?${params}`}
      user={user}
      params={params}
      setParams={setParams}
      onChanged={onChanged}
      onEditing={onEditing}
    />
  );
}

export function EscalationQueue({ user }: { user: User }) {
  const [params, setParams] = useSearchParams(),
    [editing, setEditing] = useState(false);
  function change(key: string, value: string) {
    const next = new URLSearchParams(params);
    next.delete("page");
    value ? next.set(key, value) : next.delete(key);
    setParams(next);
  }
  if (!["coordinator", "auditor"].includes(user.role))
    return (
      <ErrorBox message="The escalation queue requires coordination access." />
    );
  return (
    <>
      <Heading
        eyebrow="SUPERVISORY ATTENTION"
        title="Escalations"
        subtitle="Review requests independently of case ownership and disposal decisions."
      />
      <div className="institution-filters">
        <label>
          Escalation state
          <select
            value={params.get("state") || "pending"}
            onChange={(e) => change("state", e.target.value)}
            disabled={editing}
          >
            <option value="pending">Pending review</option>
            <option value="resolved">Resolved</option>
            <option value="all">All requests</option>
          </select>
        </label>
        <label>
          Search case or institution
          <input
            type="search"
            maxLength={200}
            value={params.get("q") || ""}
            onChange={(e) => change("q", e.target.value)}
            disabled={editing}
          />
        </label>
      </div>
      <EscalationList
        url={`/api/escalations?${params}`}
        user={user}
        params={params}
        setParams={setParams}
        onEditing={setEditing}
      />
    </>
  );
}
