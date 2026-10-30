import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import {
  WarningCircle,
  CircleNotch,
  Tray,
  ArrowUpRight,
  ArrowLeft,
  ArrowRight,
} from "@phosphor-icons/react";
import { date, labels } from "./api";
import type { Case, Page } from "./api";

export function ErrorBox({ message }: { message: string }) {
  return message ? (
    <div className="error" role="alert">
      <WarningCircle size={20} />
      {message}
    </div>
  ) : null;
}

export function Loading() {
  return (
    <div className="empty" role="status">
      <CircleNotch className="spin" size={26} /> Loading workspace…
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return (
    <div className="empty">
      <Tray size={34} />
      <p>{children}</p>
    </div>
  );
}

export function Badge({ status }: { status: string }) {
  return (
    <span className={`badge ${status}`}>
      {typeof status === "string"
        ? labels[status] || status.replaceAll("_", " ")
        : "Unknown status"}
    </span>
  );
}

export function Heading({
  eyebrow,
  title,
  subtitle,
  children,
}: {
  eyebrow: string;
  title: ReactNode;
  subtitle: string;
  children?: ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      <div className="heading-actions">{children}</div>
    </div>
  );
}

export function CaseTable({ rows }: { rows: Case[] }) {
  return (
    <div
      className="table-scroll"
      role="region"
      aria-label="Complaint list"
      tabIndex={0}
    >
      <table>
        <thead>
          <tr>
            <th>CASE / INSTITUTION</th>
            <th>CATEGORY</th>
            <th>BUREAU</th>
            <th>STATUS</th>
            <th>DUE DATE</th>
            <th>
              <span className="sr-only">Open</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.id}>
              <td>
                <Link className="case-ref" to={`/cases/${c.id}`}>
                  {c.reference}
                </Link>
                <Link
                  className="table-sub institution-link"
                  to={`/institutions/${c.institution.id}`}
                >
                  {c.institution.name}
                </Link>
              </td>
              <td className="capitalize">{c.category}</td>
              <td>
                <span className="bureau-tag">{c.bureau}</span>
              </td>
              <td>
                <Badge status={c.status} />
              </td>
              <td className={c.overdue ? "overdue-text" : ""}>
                {date(c.due_at)}
                {c.overdue && <span className="table-sub">Overdue</span>}
              </td>
              <td>
                <Link
                  className="icon-link"
                  aria-label={`Open ${c.reference}`}
                  to={`/cases/${c.id}`}
                >
                  <ArrowUpRight size={19} />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!rows.length && <Empty>No cases match these filters.</Empty>}
    </div>
  );
}

export function Pagination({
  data,
  params,
  setParams,
}: {
  data: Page<unknown>;
  params: URLSearchParams;
  setParams: (p: URLSearchParams) => void;
}) {
  const current = Number(params.get("page") || 1);
  return (
    <div className="pagination">
      <span>
        {data.count} records · Page {current} of{" "}
        {Math.max(1, Math.ceil(data.count / 20))}
      </span>
      <div>
        <button
          className="button secondary small"
          disabled={!data.previous}
          onClick={() => {
            const p = new URLSearchParams(params);
            p.set("page", String(current - 1));
            setParams(p);
          }}
        >
          <ArrowLeft size={15} />
          Previous
        </button>
        <button
          className="button secondary small"
          disabled={!data.next}
          onClick={() => {
            const p = new URLSearchParams(params);
            p.set("page", String(current + 1));
            setParams(p);
          }}
        >
          Next
          <ArrowRight size={15} />
        </button>
      </div>
    </div>
  );
}
