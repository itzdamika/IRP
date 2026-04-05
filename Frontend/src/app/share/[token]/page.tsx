"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import {
  normalizeUiEvents,
  PlanningEventsPanel,
} from "@/components/chat/PlanningEventsPanel";
import { MessageMarkdown } from "@/components/chat/MessageMarkdown";
import { API_BASE } from "@/lib/api";
import { CHAT_COLUMN } from "@/lib/chatConstants";

type ShareMsg = {
  id: string;
  role: string;
  content: string;
  agent?: string | null;
  metadata?: Record<string, unknown>;
};

export default function SharedThreadPage() {
  const params = useParams();
  const token = params.token as string;
  const [title, setTitle] = useState("");
  const [phase, setPhase] = useState("");
  const [messages, setMessages] = useState<ShareMsg[]>([]);
  const [branchPlanning, setBranchPlanning] = useState<unknown[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/v1/share/${encodeURIComponent(token)}`);
        if (!res.ok) {
          const t = await res.text();
          throw new Error(t || res.statusText);
        }
        const data = await res.json();
        if (cancelled) return;
        setTitle(data.thread?.title || "Shared chat");
        setPhase(data.thread?.phase || "");
        setMessages(data.messages || []);
        setBranchPlanning(
          Array.isArray(data.planning_transcript) ? data.planning_transcript : []
        );
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Could not load share link");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  if (error) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-black px-4 text-center text-white">
        <p className="text-[15px] text-[#c0c0c0]">{error}</p>
        <Link
          href="/"
          className="mt-6 rounded-full border border-white/[0.15] px-5 py-2 text-sm font-medium hover:bg-white/[0.06]"
        >
          Home
        </Link>
      </div>
    );
  }

  const maxInlinePlanningLen = Math.max(
    0,
    ...messages.map((m) =>
      m.role === "assistant" &&
      Array.isArray(m.metadata?.planning_ui_events)
        ? m.metadata.planning_ui_events.length
        : 0
    )
  );
  const branchNorm = normalizeUiEvents(branchPlanning);
  const showBranchPlanning = branchNorm.length > maxInlinePlanningLen;

  return (
    <div className="min-h-screen bg-black text-white">
      <header className="border-b border-white/[0.06] px-4 py-3">
        <div className={CHAT_COLUMN}>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-[#606060]">
            Read-only share
          </p>
          <h1 className="truncate text-[17px] font-semibold">{title || "…"}</h1>
          {phase && (
            <p className="text-[12px] text-[#707070]">Phase: {phase}</p>
          )}
        </div>
      </header>
      <main className={`${CHAT_COLUMN} py-6`}>
        {messages.map((m, i) => (
          <article key={m.id || i} className="mb-10">
            {m.role === "user" ? (
              <div className="flex justify-end">
                <div className="max-w-[80%] rounded-3xl bg-[#2a2a2a] px-4 py-3 text-left text-[15px] leading-relaxed text-white">
                  <p className="whitespace-pre-wrap">{m.content}</p>
                </div>
              </div>
            ) : (
              <div>
                {m.agent && (
                  <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-[#606060]">
                    {m.agent}
                  </p>
                )}
                <MessageMarkdown content={m.content || ""} />
                {(() => {
                  const pe = m.metadata?.planning_ui_events;
                  if (!Array.isArray(pe) || pe.length === 0) return null;
                  return (
                    <PlanningEventsPanel
                      events={normalizeUiEvents(pe)}
                      compactMaxHeight={false}
                    />
                  );
                })()}
              </div>
            )}
          </article>
        ))}
        {showBranchPlanning && (
          <div className="mb-10">
            <p className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-[#606060]">
              Planning session
            </p>
            <PlanningEventsPanel events={branchNorm} compactMaxHeight={false} />
          </div>
        )}
      </main>
    </div>
  );
}
