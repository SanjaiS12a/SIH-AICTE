import { mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
const root = resolve(process.env.AUDIT_ARTIFACT_DIR || `../tests/results/runs/local-${new Date().toISOString().replace(/[:.]/g, '-')}-${process.pid}`);
process.env.AUDIT_ARTIFACT_DIR = root;

export function artifact(name: string) {
  const path = resolve(
    root,
    name,
  );
  mkdirSync(dirname(path), { recursive: true });
  return path;
}
