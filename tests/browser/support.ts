import { mkdirSync } from "node:fs";
import { resolve, dirname } from "node:path";

export function artifact(name: string) {
  const path = resolve(
    process.env.AUDIT_ARTIFACT_DIR || "../tests/results/runs/local",
    name,
  );
  mkdirSync(dirname(path), { recursive: true });
  return path;
}
