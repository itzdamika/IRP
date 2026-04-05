"use client";

import { useEffect, useRef } from "react";

type UiEvent = Record<string, unknown>;

function isRecord(x: unknown): x is Record<string, unknown> {
  return typeof x === "object" && x !== null;
}

export function PlanningEventsPanel({
  events,
  showPlaceholder,
  onExpand,
  compactMaxHeight = true,
}: {
  events: UiEvent[];
  showPlaceholder?: boolean;
  onExpand?: () => void;
  /** When false (e.g. modal), inner list uses a taller max-height. */
  compactMaxHeight?: boolean;
}) {
  const scrollRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [events.length, showPlaceholder]);

  if (!events.length && !showPlaceholder) return null;

  return (
    <div className="mb-6 overflow-hidden rounded-2xl border border-emerald-500/20 bg-[#080808] shadow-[0_12px_40px_-12px_rgba(16,185,129,0.15)]">
      <div className="flex items-center gap-3 border-b border-white/[0.06] px-4 py-3">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-emerald-500/15 text-[13px]">
          ◇
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-[14px] font-semibold tracking-tight text-white">
            Planning activity
          </p>
          <p className="text-[12px] text-[#707070]">
            Agents reasoning, scoring, and revising the architecture
          </p>
        </div>
        {onExpand && (
          <button
            type="button"
            onClick={onExpand}
            className="shrink-0 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-[11px] font-semibold text-emerald-100/95 hover:bg-emerald-500/20"
          >
            Expand
          </button>
        )}
      </div>
      <div className="p-4">
        {showPlaceholder && events.length === 0 && (
          <div className="mb-4 flex items-center gap-3 rounded-xl border border-emerald-500/10 bg-emerald-950/20 px-3 py-3">
            <span className="inline-flex h-2 w-2 shrink-0 animate-pulse rounded-full bg-emerald-400" />
            <p className="text-[13px] text-[#a0a0a0]">
              Connecting live stream…
            </p>
          </div>
        )}
        <div
          ref={scrollRef}
          className={`space-y-3 overflow-y-auto overscroll-contain pr-1 ${
            compactMaxHeight
              ? "max-h-[min(50vh,24rem)]"
              : "max-h-[min(85vh,52rem)]"
          }`}
        >
          {events.map((ev, i) => (
            <EventBlock key={i} ev={ev} />
          ))}
        </div>
      </div>
    </div>
  );
}

function EventBlock({ ev }: { ev: UiEvent }) {
  const t = ev.type;
  if (t === "round_tables") {
    const round = ev.round as number;
    const planRows = (ev.plan_rows as string[][]) || [];
    const auditRows = (ev.audit_rows as string[][]) || [];
    return (
      <div className="overflow-hidden rounded-xl border border-emerald-500/15 bg-[#0c0c0c]">
        <div className="border-b border-white/[0.05] bg-emerald-950/25 px-3 py-2.5">
          <p className="text-[13px] font-semibold text-emerald-100/95">
            Round {round}
          </p>
          <p className="text-[11px] text-emerald-200/50">
            Plan snapshot · audit rubric &amp; score
          </p>
        </div>
        <div className="grid gap-4 p-3 sm:grid-cols-2">
          <MiniTable title="Architect plan" rows={planRows} accent="emerald" />
          <MiniTable title="Auditor review" rows={auditRows} accent="slate" />
        </div>
      </div>
    );
  }
  if (t === "thinking") {
    const agent = String(ev.agent || "Agent");
    return (
      <div className="rounded-xl border border-white/[0.07] bg-[#101010] px-3.5 py-3">
        <div className="mb-2 inline-flex items-center rounded-full border border-emerald-500/25 bg-emerald-500/10 px-2.5 py-0.5">
          <span className="text-[11px] font-semibold uppercase tracking-wide text-emerald-300/95">
            {agent}
          </span>
        </div>
        <p className="whitespace-pre-wrap text-[13px] leading-relaxed text-[#c4c4c4]">
          {String(ev.body || "")}
        </p>
      </div>
    );
  }
  if (t === "panel") {
    const color = String(ev.color || "green");
    const ring =
      color === "cyan"
        ? "border-cyan-500/25"
        : color === "red"
          ? "border-red-500/25"
          : "border-emerald-500/25";
    return (
      <div className={`rounded-xl border ${ring} bg-[#101010] px-3.5 py-3`}>
        <p className="text-[13px] font-semibold text-white">
          {String(ev.title || "Update")}
        </p>
        <p className="mt-1.5 whitespace-pre-wrap text-[13px] leading-relaxed text-[#9a9a9a]">
          {String(ev.body || "")}
        </p>
      </div>
    );
  }
  if (t === "status_table") {
    const rows = (ev.rows as string[][]) || [];
    return (
      <div className="rounded-xl border border-white/[0.06] bg-[#101010] p-3">
        <p className="mb-2 text-[12px] font-semibold text-white">
          {String(ev.title || "Status")}
        </p>
        <ul className="space-y-1.5 text-[12px]">
          {rows.map((r, j) => (
            <li key={j} className="flex gap-2">
              <span className="w-[40%] shrink-0 text-[#606060]">{r[0]}</span>
              <span className="text-[#c8c8c8]">{r[1]}</span>
            </li>
          ))}
        </ul>
      </div>
    );
  }
  if (t === "log") {
    return (
      <div className="flex gap-3 rounded-lg px-1 py-1.5">
        <span
          className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500/80"
          aria-hidden
        />
        <p className="text-[13px] leading-snug text-[#a8a8a8]">
          {String(ev.message || "")}
        </p>
      </div>
    );
  }
  if (t === "rule") {
    return (
      <div className="rounded-lg border-l-2 border-amber-500/50 bg-amber-950/10 py-2 pl-3 pr-2">
        <p className="text-[12px] font-medium text-amber-100/90">
          {String(ev.message || "")}
        </p>
      </div>
    );
  }
  return (
    <pre className="max-h-32 overflow-auto rounded-lg bg-black/40 p-2 text-[11px] text-[#606060]">
      {JSON.stringify(ev, null, 2)}
    </pre>
  );
}

function MiniTable({
  title,
  rows,
  accent,
}: {
  title: string;
  rows: string[][];
  accent: "emerald" | "slate";
}) {
  const head =
    accent === "emerald" ? "text-emerald-400/80" : "text-slate-400/90";
  return (
    <div>
      <p className={`mb-2 text-[11px] font-semibold uppercase tracking-wide ${head}`}>
        {title}
      </p>
      <div className="overflow-x-auto rounded-lg border border-white/[0.06] bg-black/30">
        <table className="w-full text-left text-[11px]">
          <tbody>
            {rows.map((r, i) => {
              const highlight =
                r[0]?.toLowerCase().includes("final score") ||
                r[0]?.toLowerCase().includes("passed");
              return (
                <tr
                  key={i}
                  className="border-b border-white/[0.04] last:border-0"
                >
                  <td className="max-w-[42%] px-2 py-1.5 align-top text-[#808080]">
                    {r[0]}
                  </td>
                  <td
                    className={`px-2 py-1.5 ${highlight ? "font-semibold text-emerald-200/95" : "text-[#d6d6d6]"}`}
                  >
                    {r[1]}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function normalizeUiEvents(raw: unknown): UiEvent[] {
  if (!Array.isArray(raw)) return [];
  return raw.filter(isRecord);
}
