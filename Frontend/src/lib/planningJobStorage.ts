const PREFIX = "arkon_planning_job_";

export type StoredPlanningJob = {
  jobId: string;
  statusUrl: string;
};

export function planningJobStorageKey(threadId: string): string {
  return `${PREFIX}${threadId}`;
}

export function savePlanningJob(
  threadId: string,
  jobId: string,
  statusUrl: string
): void {
  try {
    if (typeof localStorage === "undefined") return;
    const payload: StoredPlanningJob = { jobId, statusUrl };
    localStorage.setItem(planningJobStorageKey(threadId), JSON.stringify(payload));
  } catch {
    /* quota / private mode */
  }
}

export function readPlanningJob(threadId: string): StoredPlanningJob | null {
  try {
    if (typeof localStorage === "undefined") return null;
    const raw = localStorage.getItem(planningJobStorageKey(threadId));
    if (!raw) return null;
    const o = JSON.parse(raw) as unknown;
    if (
      !o ||
      typeof o !== "object" ||
      typeof (o as StoredPlanningJob).jobId !== "string" ||
      typeof (o as StoredPlanningJob).statusUrl !== "string"
    ) {
      return null;
    }
    return o as StoredPlanningJob;
  } catch {
    return null;
  }
}

export function clearPlanningJob(threadId: string): void {
  try {
    if (typeof localStorage === "undefined") return;
    localStorage.removeItem(planningJobStorageKey(threadId));
  } catch {
    /* */
  }
}

/** Thread IDs that have a persisted in-flight planning job marker (may be stale). */
export function threadIdsWithStoredPlanningJobs(): Set<string> {
  const s = new Set<string>();
  if (typeof localStorage === "undefined") return s;
  for (let i = 0; i < localStorage.length; i++) {
    const k = localStorage.key(i);
    if (!k?.startsWith(PREFIX)) continue;
    s.add(k.slice(PREFIX.length));
  }
  return s;
}
