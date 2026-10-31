import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api, labels } from "./api";
import type { Case, Page, Overlap, User } from "./api";
import { usePoll } from "./imports";
import { Heading, Loading, ErrorBox, Empty, Pagination } from "./ui";

export function ManualRelationship({ user }: { user: User }) {
  const [params, setParams] = useSearchParams();
  const institution = params.get("institution");
  const [chosen, setChosen] = useState<Case[]>([]),
    [decision, setDecision] = useState("related_issue"),
    [reason, setReason] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const { data, error: loadError } = usePoll<Page<Case>>(
    user.role === "coordinator" && institution
      ? `/api/institutions/${institution}/cases?page=${params.get("page") || 1}&q=${encodeURIComponent(params.get("q") || "")}`
      : null,
  );
  const navigate = useNavigate();
  if (user.role !== "coordinator")
    return <ErrorBox message="Only coordinators can create relationships." />;
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (chosen.length !== 2) return;
    setBusy(true);
    setError("");
    try {
      const result = await api<Overlap>("/api/relationships", {
        method: "POST",
        body: JSON.stringify({
          left: chosen[0].id,
          right: chosen[1].id,
          decision,
          reason,
        }),
      });
      navigate(
        `/coordination?institution=${institution}&decision=all&pair=${result.id}`,
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <Heading
        eyebrow="HUMAN COORDINATION"
        title="Create manual relationship"
        subtitle="Select two cases at the same canonical institution. No model inference or similarity score is required."
      />
      {!institution ? (
        <Empty>
          <Link to="/institutions">
            Choose an institution from the registry first
          </Link>
        </Empty>
      ) : (
        <>
          <Link to={`/institutions/${institution}?section=coordination`}>
            Institution coordination
          </Link>
          <section className="panel">
            <div className="institution-filters">
              <label>
                Search institution cases
                <input
                  type="search"
                  maxLength={200}
                  value={params.get("q") || ""}
                  onChange={(e) => {
                    const p = new URLSearchParams(params);
                    p.set("q", e.target.value);
                    p.delete("page");
                    setParams(p);
                  }}
                />
              </label>
            </div>
            <ErrorBox message={loadError} />
            {!data && !loadError && <Loading />}
            {data && (
              <>
                <div
                  className="table-scroll"
                  role="region"
                  aria-label="Select related cases"
                  tabIndex={0}
                >
                  <table>
                    <thead>
                      <tr>
                        <th>Select two</th>
                        <th>Case</th>
                        <th>Summary</th>
                        <th>Bureau</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.results.map((c) => (
                        <tr key={c.id}>
                          <td>
                            <input
                              type="checkbox"
                              aria-label={`Select ${c.reference}`}
                              checked={chosen.some((x) => x.id === c.id)}
                              disabled={
                                chosen.length === 2 &&
                                !chosen.some((x) => x.id === c.id)
                              }
                              onChange={(e) =>
                                setChosen(
                                  e.target.checked
                                    ? [...chosen, c]
                                    : chosen.filter((x) => x.id !== c.id),
                                )
                              }
                            />
                          </td>
                          <td>
                            <Link to={`/cases/${c.id}`}>{c.reference}</Link>
                          </td>
                          <td>{c.summary}</td>
                          <td>{c.bureau}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <Pagination data={data} params={params} setParams={setParams} />
              </>
            )}
          </section>
          <form className="panel card-body" onSubmit={submit}>
            <h2>Compare selected cases ({chosen.length}/2)</h2>
            <div className="comparison">
              {chosen.map((c) => (
                <article key={c.id}>
                  <Link to={`/cases/${c.id}`}>
                    {c.reference} · {c.bureau}
                  </Link>
                  <h3>{c.summary}</h3>
                  <p className="description">{c.description}</p>
                  <p>
                    {labels[c.status]} · {c.source_reference}
                  </p>
                </article>
              ))}
            </div>
            <p>
              Not model-scored. Cases remain independent; this decision does not
              transfer, merge or close either case.
            </p>
            <ErrorBox message={error} />
            <label>
              Relationship decision
              <select
                value={decision}
                onChange={(e) => setDecision(e.target.value)}
              >
                {["same_incident", "related_issue", "unrelated"].map((d) => (
                  <option key={d} value={d}>
                    {labels[d]}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Relationship explanation
              <textarea
                required
                rows={3}
                maxLength={4000}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </label>
            <button disabled={chosen.length !== 2 || busy}>
              {busy ? "Recording…" : "Record manual relationship"}
            </button>
            {error && (
              <Link
                className="text-button"
                to={`/coordination?institution=${institution}&decision=all`}
              >
                Inspect existing relationships before changing a decision
              </Link>
            )}
          </form>
        </>
      )}
    </>
  );
}
