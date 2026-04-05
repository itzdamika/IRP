"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ChatPillInput } from "@/components/chat/ChatPillInput";
import { api, getToken } from "@/lib/api";
import { CHAT_COLUMN } from "@/lib/chatConstants";
import { THREADS_REFRESH } from "@/lib/appEvents";

const STARTERS = [
  "Design a multi-tenant SaaS REST API with RBAC and logging",
  "Build a SE project: an event-driven order pipeline using Kafka, outbox pattern, and CI/CD testing",
  "Do threat modeling and secure SDLC for a fintech app with auth"
];

export default function ChatIndex() {
  const router = useRouter();
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  async function startFromMessage(text: string) {
    const t = text.trim();
    if (!t || busy) return;
    setBusy(true);
    try {
      const th = await api<{ id: string; phase: string }>("/v1/threads", {
        method: "POST",
        body: JSON.stringify({}),
      });
      try {
        sessionStorage.setItem(
          "arkon_pending_message",
          JSON.stringify({ threadId: th.id, content: t }),
        );
      } catch {
        /* private mode / quota */
      }
      window.dispatchEvent(new Event(THREADS_REFRESH));
      router.push(`/chat/${th.id}`);
    } catch (e) {
      console.error(e);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full flex-col bg-black">
      <div
        className={`flex flex-1 flex-col items-center justify-center pb-8 pt-16 md:pt-4 ${CHAT_COLUMN}`}
      >
        <div className="mb-10 flex flex-col items-center">
          <div className="mb-6 flex h-20 w-20 items-center justify-center text-white">
            <img src="/imageBlack.png" alt="logo" />
          </div>
          <h1 className="text-center text-[30px] font-semibold tracking-tight text-white">
            What should we architect?
          </h1>
          <p className="mt-2 max-w-md text-center text-[14px] text-[#707070]">
            Write the prompt describing your system.
          </p>
        </div>

        <div className="w-full">
          <ChatPillInput
            variant="landing"
            value={input}
            onChange={setInput}
            disabled={busy}
            placeholder="Ask anything"
            onSubmit={() => {
              startFromMessage(input);
              setInput("");
            }}
          />
        </div>


        <div className="mt-10 w-full space-y-2">
          {STARTERS.map((s) => (
            <button
              key={s}
              type="button"
              disabled={busy}
              onClick={() => startFromMessage(s)}
              className="flex items-center gap-3 rounded-full border border-transparent px-4 py-3 text-left text-[14px] font-semibold leading-snug text-white transition-colors duration-200 hover:bg-[#1c1c1c] disabled:opacity-40"
            >
              <span className="shrink-0 text-[#707070]" aria-hidden>
                ↳
              </span>
              <span>{s}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
