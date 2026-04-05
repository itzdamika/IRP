export const THREADS_REFRESH = "arkon:threads-refresh";
export const OPEN_SETTINGS = "arkon:open-settings";
export const PLANNING_ACTIVE = "arkon:planning-active";

export function dispatchPlanningActive(threadId: string, active: boolean): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(
    new CustomEvent(PLANNING_ACTIVE, { detail: { threadId, active } })
  );
}
