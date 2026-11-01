import { useState } from "react";
import type { FormEvent } from "react";
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { api, ApiError, date } from "./api";
import type { User, Options, Case, Page, CaseAction } from "./api";
import { usePoll } from "./imports";
import { Heading, ErrorBox, Loading, Empty, Pagination, CaseTable } from "./ui";

type Participant = {
  bureau_code: string;
  officer_id: number;
  id: number;
  bureau: string;
  officer_name: string;
  instruction: string;
  action_date: string | null;
  acknowledged_at: string | null;
  completed_at: string | null;
  completion_note: string;
};
type Record = {
  id: string;
  institution_id: string;
  institution_name: string;
  lead_bureau_name: string;
  lead_officer_name: string;
  reason: string;
  state: string;
  outcome: string;
  version: number;
  participants: Participant[];
  cases?: Case[];
};
type Request = {
  id: number;
  coordination_id: string;
  version: number;
  state: string;
  instruction: string;
  action_date: string | null;
  acknowledged_at: string | null;
  completed_at: string | null;
  completion_note: string;
};
function validPage(value: unknown) {
  const p = value as Page<unknown> | null;
  return !!p && Number.isInteger(p.count) && Array.isArray(p.results);
}
function validRecord(value: unknown): boolean {
  const r = value as Record | null;
  return (
    !!r &&
    typeof r.id === "string" &&
    typeof r.institution_id === "string" &&
    typeof r.institution_name === "string" &&
    typeof r.reason === "string" &&
    Number.isInteger(r.version) &&
    ["in_coordination", "closed"].includes(r.state) &&
    Array.isArray(r.participants) &&
    r.participants.every(
      (p) =>
        !!p &&
        typeof p.instruction === "string" &&
        typeof p.bureau_code === "string" &&
        typeof p.bureau === "string" &&
        Number.isInteger(p.officer_id),
    )
  );
}
function validRecords(value: unknown) {
  return validPage(value) && (value as Page<Record>).results.every(validRecord);
}
function validHistory(value: unknown) {
  return (
    validPage(value) &&
    (value as Page<CaseAction>).results.every(
      (a) =>
        !!a &&
        typeof a.kind === "string" &&
        typeof a.reason === "string" &&
        typeof a.actor === "string",
    )
  );
}
function validRequests(value: unknown) {
  return (
    validPage(value) &&
    (value as Page<Request>).results.every(
      (r) =>
        !!r &&
        typeof r.instruction === "string" &&
        typeof r.coordination_id === "string" &&
        Number.isInteger(r.version) &&
        ["in_coordination", "closed"].includes(r.state),
    )
  );
}

export function CoordinationWorkspace({
  user,
  options,
}: {
  user: User;
  options: Options;
}) {
  const [params, setParams] = useSearchParams();
  const institution = params.get("institution");
  const [chosen, setChosen] = useState<Case[]>([]),
    [reason, setReason] = useState(""),
    [lead, setLead] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const [participants, setParticipants] = useState<
    {
      bureau: string;
      officer: string;
      instruction: string;
      action_date: string;
    }[]
  >([]);
  const [submission] = useState(() => crypto.randomUUID());
  const [refresh, setRefresh] = useState(0);
  const management = ["coordinator", "auditor"].includes(user.role);
  const { data, error: loadError } = usePoll<Page<Record>>(
    management
      ? `/api/coordination-records?${params}`
      : null,
    5000,
    refresh,
    validRecords,
  );
  const { data: cases, error: caseError } = usePoll<Page<Case>>(
    user.role === "coordinator" && institution
      ? `/api/institutions/${institution}/cases?page=${params.get("case_page") || 1}`
      : null,
    0,
    0,
    validPage,
  );
  const navigate = useNavigate();
  if (!management)
    return <ErrorBox message="Coordination management access is required." />;
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const selectedLead = participants.find((p) => p.bureau === lead);
      const result = await api<Record>("/api/coordination-records", {
        method: "POST",
        body: JSON.stringify({
          submission_id: submission,
          institution,
          cases: chosen.map((c) => c.id),
          reason,
          lead_bureau: lead,
          lead_officer: Number(selectedLead?.officer),
          participants: participants.map((p) => ({
            ...p,
            officer: Number(p.officer),
            action_date: p.action_date || null,
          })),
        }),
      });
      navigate(`/coordination/workspace/${result.id}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Heading
        eyebrow="ACCOUNTABLE CROSS-BUREAU WORK"
        title="Coordination workspace"
        subtitle="Agree who will act, obtain each Bureau’s acknowledgment, and record completion. This demonstration workflow does not merge cases or change ownership."
      />
      <p className="muted">
        Relationship review describes how cases are connected. A coordination
        record assigns agreed work; closing it does not close its cases.
        Instructions below are explicitly shared with their designated officer;
        other evidence stays restricted.
      </p>
      <ErrorBox message={loadError} />
      {!data && !loadError && <Loading />}
      {data && (
        <section className="panel detail-card">
          <h2 className="card-body">Recorded coordination</h2>
          {data.results.length ? (
            data.results.map((r) => (
              <article className="card-body" key={r.id}>
                <h3>
                  <Link to={`/coordination/workspace/${r.id}`}>
                    {r.institution_name}
                  </Link>
                </h3>
                <p>
                  {r.state === "closed" ? "Closed" : "In coordination"} · Lead:{" "}
                  {r.lead_bureau_name} / {r.lead_officer_name}
                </p>
                <p>
                  {r.participants.filter((p) => !!p.acknowledged_at).length}/
                  {r.participants.length} acknowledged ·{" "}
                  {r.participants.filter((p) => !!p.completed_at).length}/
                  {r.participants.length} completed
                </p>
              </article>
            ))
          ) : (
            <Empty>No coordination records yet.</Empty>
          )}
          <Pagination data={data} params={params} setParams={setParams} />
        </section>
      )}
      {user.role === "coordinator" &&
        (!institution ? (
          <Empty>
            <Link to="/institutions">
              Choose an institution to open coordination
            </Link>
          </Empty>
        ) : (
          <form
            className="panel detail-card card-body form-panel"
            aria-label="Open coordination"
            onSubmit={submit}
          >
            <h2>Open agreed coordination</h2>
            <Link to={`/institutions/${institution}?section=coordination`}>
              Institution profile and evidence
            </Link>
            <ErrorBox message={caseError || error} />
            <fieldset>
              <legend>Linked cases — select one or more</legend>
              {!cases && !caseError && <Loading />}
              {cases?.results.map((c) => (
                <label key={c.id}>
                  <input
                    type="checkbox"
                    checked={chosen.some((x) => x.id === c.id)}
                    onChange={(e) =>
                      setChosen((old) =>
                        e.target.checked
                          ? [...old, c]
                          : old.filter((x) => x.id !== c.id),
                      )
                    }
                  />
                  {c.reference} · {c.bureau} · {c.summary}
                </label>
              ))}
              {cases && (
                <>
                  <p>{chosen.length} selected across all pages.</p>
                  <div className="form-actions">
                    <button
                      type="button"
                      className="secondary"
                      disabled={!cases.previous}
                      onClick={() => {
                        const p = new URLSearchParams(params);
                        p.set(
                          "case_page",
                          String(Number(params.get("case_page") || 1) - 1),
                        );
                        setParams(p);
                      }}
                    >
                      Previous cases
                    </button>
                    <button
                      type="button"
                      className="secondary"
                      disabled={!cases.next}
                      onClick={() => {
                        const p = new URLSearchParams(params);
                        p.set(
                          "case_page",
                          String(Number(params.get("case_page") || 1) + 1),
                        );
                        setParams(p);
                      }}
                    >
                      Next cases
                    </button>
                  </div>
                </>
              )}
            </fieldset>
            <label>
              Private coordination reason
              <textarea
                required
                maxLength={4000}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </label>
            <fieldset>
              <legend>
                Participating Bureaus and explicitly shared actions
              </legend>
              {options.bureaus.map((b) => {
                const p = participants.find((p) => p.bureau === b.code);
                const change = (key: string, value: string) =>
                  setParticipants((old) =>
                    old.map((p) =>
                      p.bureau === b.code ? { ...p, [key]: value } : p,
                    ),
                  );
                return (
                  <div className="card-body" key={b.code}>
                    <label>
                      <input
                        type="checkbox"
                        checked={!!p}
                        onChange={(e) =>
                          setParticipants((old) =>
                            e.target.checked
                              ? [
                                  ...old,
                                  {
                                    bureau: b.code,
                                    officer: "",
                                    instruction: "",
                                    action_date: "",
                                  },
                                ]
                              : old.filter((p) => p.bureau !== b.code),
                          )
                        }
                      />
                      {b.name}
                    </label>
                    {p && (
                      <>
                        <label>
                          Responsible officer — {b.name}
                          <select
                            aria-label={`Responsible officer — ${b.name}`}
                            required
                            value={p.officer}
                            onChange={(e) => change("officer", e.target.value)}
                          >
                            <option value="">Select current officer</option>
                            {options.officers
                              .filter((o) => o.bureau === b.code)
                              .map((o) => (
                                <option key={o.id} value={o.id}>
                                  {o.name}
                                </option>
                              ))}
                          </select>
                        </label>
                        <label>
                          Shared instruction — {b.name}
                          <textarea
                            required
                            maxLength={2000}
                            value={p.instruction}
                            onChange={(e) =>
                              change("instruction", e.target.value)
                            }
                          />
                        </label>
                        <label>
                          Coordination action date — {b.name}
                          <input
                            type="date"
                            value={p.action_date}
                            onChange={(e) =>
                              change("action_date", e.target.value)
                            }
                          />
                        </label>
                      </>
                    )}
                  </div>
                );
              })}
            </fieldset>
            <label>
              Lead Bureau
              <select
                aria-label="Lead Bureau"
                required
                value={lead}
                onChange={(e) => setLead(e.target.value)}
              >
                <option value="">Select lead participant</option>
                {participants.map((p) => (
                  <option key={p.bureau} value={p.bureau}>
                    {options.bureaus.find((b) => b.code === p.bureau)?.name}
                  </option>
                ))}
              </select>
            </label>
            <p className="muted">
              The selected Bureau’s designated officer is the lead. At least two
              Bureaus must participate, including all current case owners.
              Coordination dates are separate from case deadlines.
            </p>
            <button
              disabled={busy || !chosen.length || participants.length < 2}
            >
              {busy ? "Recording…" : "Record agreed coordination"}
            </button>
          </form>
        ))}
      <button
        type="button"
        className="text-button"
        onClick={() => setRefresh((x) => x + 1)}
      >
        Refresh coordination records
      </button>
    </>
  );
}

function CoordinationAction({
  record,
  action,
  saved,
  participant,
  options,
}: {
  record: { id: string; version: number };
  action: "acknowledge" | "complete" | "close" | "revise";
  saved: () => void;
  participant?: Participant;
  options?: Options;
}) {
  const [officer, setOfficer] = useState(String(participant?.officer_id || ""));
  const [instruction, setInstruction] = useState(
    participant?.instruction || "",
  );
  const [actionDate, setActionDate] = useState(participant?.action_date || "");
  const [note, setNote] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [conflict, setConflict] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api(`/api/coordination-records/${record.id}/actions`, {
        method: "POST",
        body: JSON.stringify({
          expected_version: record.version,
          action,
          note: note || undefined,
          ...(action === "revise"
            ? {
                participant: participant?.id,
                officer: Number(officer),
                instruction,
                action_date: actionDate || null,
              }
            : {}),
        }),
      });
      setNote("");
      saved();
    } catch (e) {
      setError((e as Error).message);
      if (e instanceof ApiError && e.status === 409) setConflict(true);
    } finally {
      setBusy(false);
    }
  }
  return (
    <form className="card-body action-form" onSubmit={submit}>
      <ErrorBox message={error} />
      {action === "revise" && (
        <>
          <label>
            New responsible officer
            <select
              aria-label="New responsible officer"
              required
              value={officer}
              onChange={(e) => setOfficer(e.target.value)}
            >
              <option value="">Select current officer</option>
              {options?.officers
                .filter((o) => o.bureau === participant?.bureau_code)
                .map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.name}
                  </option>
                ))}
            </select>
          </label>
          <label>
            Revised shared instruction
            <textarea
              required
              maxLength={2000}
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
            />
          </label>
          <label>
            Revised coordination action date
            <input
              type="date"
              value={actionDate}
              onChange={(e) => setActionDate(e.target.value)}
            />
          </label>
          <p>
            Revising an agreed action clears its previous acknowledgment and
            completion. The designated officer must acknowledge it again.
          </p>
        </>
      )}
      {action !== "acknowledge" && (
        <label>
          {action === "revise"
            ? "Reason for revision"
            : action === "close"
              ? "Coordination outcome"
              : "Completion note"}
          <textarea
            required
            rows={3}
            maxLength={2000}
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
        </label>
      )}
      {conflict && (
        <p role="alert">
          The record changed. Your draft is retained. Refresh and review current
          responsibilities before retrying.
        </p>
      )}
      <div className="form-actions">
        {conflict && (
          <button
            type="button"
            className="secondary"
            onClick={() => {
              saved();
              setConflict(false);
            }}
          >
            Reload record and discard draft
          </button>
        )}
        <button disabled={busy || conflict}>
          {busy
            ? "Saving…"
            : action === "acknowledge"
              ? "Acknowledge agreed action"
              : action === "complete"
                ? "Complete agreed action"
                : action === "revise"
                  ? "Save revised responsibility"
                  : "Close coordination"}
        </button>
      </div>
    </form>
  );
}

export function CoordinationRecordPage({
  user,
  options,
}: {
  user: User;
  options: Options;
}) {
  const { id } = useParams();
  const [refresh, setRefresh] = useState(0);
  const [params, setParams] = useSearchParams();
  const management = ["coordinator", "auditor"].includes(user.role);
  const { data: record, error } = usePoll<Record>(
    management ? `/api/coordination-records/${id}` : null,
    0,
    refresh,
    validRecord,
  );
  const { data: history, error: historyError } = usePoll<Page<CaseAction>>(
    management
      ? `/api/coordination-records/${id}/history?page=${params.get("page") || 1}`
      : null,
    0,
    refresh,
    validHistory,
  );
  if (!management)
    return <ErrorBox message="Coordination management access is required." />;
  return (
    <>
      <Heading
        eyebrow="COORDINATION RECORD"
        title={record?.institution_name || "Coordination record"}
        subtitle="Shared responsibilities, acknowledgments and outcome. Case statuses, ownership and human relationship labels remain independent."
      />
      <ErrorBox message={error} />
      {!record && !error && <Loading />}
      {record && (
        <>
          <Link
            to={`/institutions/${record.institution_id}?section=coordination`}
          >
            Institution profile
          </Link>
          <section className="panel card-body">
            <h2>
              {record.state === "closed"
                ? "Coordination closed"
                : "In coordination"}
            </h2>
            <p>
              Lead: {record.lead_bureau_name} / {record.lead_officer_name}
            </p>
            <p>{record.reason}</p>
            {record.outcome && <p>Outcome: {record.outcome}</p>}
            {record.participants.map((p) => (
              <article className="card-body" key={p.id}>
                <h3>
                  {p.bureau} — {p.officer_name}
                </h3>
                <p>{p.instruction}</p>
                <p>
                  Action date: {date(p.action_date)} · Acknowledged:{" "}
                  {date(p.acknowledged_at)} · Completed: {date(p.completed_at)}
                </p>
                {p.completion_note && <p>{p.completion_note}</p>}
                {record.state !== "closed" && user.role === "coordinator" && (
                  <details>
                    <summary>Revise this Bureau’s agreed action</summary>
                    <CoordinationAction
                      record={record}
                      action="revise"
                      participant={p}
                      options={options}
                      saved={() => setRefresh((x) => x + 1)}
                    />
                  </details>
                )}
              </article>
            ))}
            <p className="muted">
              A participant acknowledges and completes only the instruction
              assigned to their current Bureau membership. Requests appear in
              their Coordination actions inbox.
            </p>
          </section>
          <section className="panel card-body">
            <h2>Linked independent cases</h2>
            <CaseTable rows={record.cases || []} />
          </section>
          {record.state !== "closed" && user.role === "coordinator" && (
            <CoordinationAction
              record={record}
              action="close"
              saved={() => setRefresh((x) => x + 1)}
            />
          )}
          <section className="panel card-body">
            <h2>Authoritative case action history</h2>
            <p className="muted">
              Each coordination event is recorded on every linked case. Counts
              are case actions, not distinct coordination decisions.
            </p>
            <ErrorBox message={historyError} />
            {!history && !historyError && <Loading />}
            {history?.results.map((a) => (
              <article key={a.id}>
                <h3>{a.kind.replaceAll("_", " ")}</h3>
                <p>
                  {date(a.created_at)} · {a.actor}
                </p>
                <p>{a.reason}</p>
              </article>
            ))}
            {history && (
              <Pagination
                data={history}
                params={params}
                setParams={setParams}
              />
            )}
          </section>
        </>
      )}
      <button
        type="button"
        className="text-button"
        onClick={() => setRefresh((x) => x + 1)}
      >
        Refresh coordination record
      </button>
    </>
  );
}

export function CoordinationRequests({ user }: { user: User }) {
  const [params, setParams] = useSearchParams(),
    [refresh, setRefresh] = useState(0);
  const { data, error } = usePoll<Page<Request>>(
    user.role === "officer"
      ? `/api/coordination-requests?page=${params.get("page") || 1}`
      : null,
    5000,
    refresh,
    validRequests,
  );
  if (user.role !== "officer")
    return <ErrorBox message="This inbox is for designated Bureau officers." />;
  return (
    <>
      <Heading
        eyebrow="YOUR BUREAU RESPONSIBILITIES"
        title="Coordination actions"
        subtitle="Only instructions explicitly addressed to you are shown. Other Bureau cases, evidence and decisions remain restricted."
      />
      <ErrorBox message={error} />
      {!data && !error && <Loading />}
      {data && (
        <>
          {data.results.length ? (
            data.results.map((r) => (
              <section className="panel card-body" key={r.id}>
                <h2>Agreed Bureau action</h2>
                <p>{r.instruction}</p>
                <p>
                  Action date: {date(r.action_date)} ·{" "}
                  {r.state === "closed"
                    ? "Coordination closed"
                    : "In coordination"}
                </p>
                {r.completed_at ? (
                  <p>Completed: {r.completion_note}</p>
                ) : (
                  r.state !== "closed" && (
                    <CoordinationAction
                      record={{ id: r.coordination_id, version: r.version }}
                      action={r.acknowledged_at ? "complete" : "acknowledge"}
                      saved={() => setRefresh((x) => x + 1)}
                    />
                  )
                )}
              </section>
            ))
          ) : (
            <Empty>
              No coordination actions assigned to your current Bureau
              membership.
            </Empty>
          )}
          <Pagination data={data} params={params} setParams={setParams} />
        </>
      )}
    </>
  );
}
