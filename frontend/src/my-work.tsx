import { Link } from "react-router-dom";
import type { User } from "./api";
import { Heading } from "./ui";

export function MyWork({ user }: { user: User }) {
  const management = ["coordinator", "auditor"].includes(user.role);
  const tasks = [
    { to: "/cases?pending=true", title: management ? "Open cases" : "Cases in my Bureau", description: "Inspect open complaints and their responsible Bureau." },
    { to: "/cases?approaching=true", title: "Approaching deadlines", description: "Open cases due in the next seven days, excluding overdue cases." },
    { to: "/cases?overdue=true", title: "Overdue cases", description: "Open cases past their expected disposal date." },
    ...(management ? [
      { to: "/coordination?decision=pending", title: "Coordination queue", description: "Compare suggested relationships. Similarity alone does not confirm a common incident." },
      { to: "/coordination/workspace", title: "Coordination workspace", description: "Inspect agreed responsibilities, acknowledgments and follow-up across Bureaus." },
      { to: "/coordination/workspace?awaiting_ack=true", title: "Awaiting acknowledgment", description: "Inspect open coordination records with outstanding acknowledgments." },
      { to: "/escalations", title: "Escalations", description: "Inspect requests for supervisory attention, separately from deadlines and relationships." },
    ] : user.role === "officer" ? [
      { to: "/coordination/requests", title: "Coordination actions", description: "Read and respond to instructions explicitly addressed to you." },
    ] : []),
  ];
  return <>
    <Heading eyebrow="OFFICIAL WORKSPACE" title="My Work"
      subtitle={user.role === "auditor" ? "Read-only access to authorized cases, reviews and coordination history."
        : management ? "Choose a task, inspect the evidence and record the next official action."
          : "Current-Bureau cases and your authorized coordination instructions. These are not a personal assignment queue."}>
      {user.role !== "auditor" && ["coordinator", "officer"].includes(user.role) && <Link className="button" to="/cases/new">Register case</Link>}
      <Link className="button secondary" to="/cases">Case registry</Link>
    </Heading>
    <div className="work-grid">
      {tasks.map(task => <Link className="panel work-task" key={task.to} to={task.to}>
        <h2>{task.title}</h2><p>{task.description}</p><span>Open task queue →</span>
      </Link>)}
    </div>
    <section className="panel card-body">
      <h2>Start with the institution</h2>
      <p>Open its profile to inspect all authorized cases and the complete history. Profile statistics are all-time and independent of Home date filters.</p>
      <Link className="text-button" to="/institutions">Find an institution →</Link>
      {user.role === "coordinator" && <p><Link className="text-button" to="/relationships/new">Create manual relationship</Link> · Choose an institution and two independent cases.</p>}
      <p className="policy-note">Demo policy: the expected disposal deadline is 30 calendar days. Next actions, escalations and relationship decisions are separate operations.</p>
    </section>
  </>;
}
