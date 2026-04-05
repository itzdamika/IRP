"use client";

import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import { SettingsModal } from "@/components/SettingsModal";
import { OPEN_SETTINGS, PLANNING_ACTIVE, THREADS_REFRESH } from "@/lib/appEvents";
import { threadIdsWithStoredPlanningJobs } from "@/lib/planningJobStorage";
import { api, clearToken, getToken } from "@/lib/api";

type ThreadItem = {
  id: string;
  title: string;
  phase: string;
  updated_at: string;
};

function startOfLocalDay(d: Date) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
}

function bucketLabel(iso: string): "Today" | "Yesterday" | "Earlier" {
  const t = new Date(iso).getTime();
  const today = startOfLocalDay(new Date());
  const y = new Date();
  y.setDate(y.getDate() - 1);
  const yesterday = startOfLocalDay(y);
  if (t >= today) return "Today";
  if (t >= yesterday) return "Yesterday";
  return "Earlier";
}

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [threads, setThreads] = useState<ThreadItem[]>([]);
  const [planningThreadIds, setPlanningThreadIds] = useState<Set<string>>(
    () => new Set()
  );

  useEffect(() => {
    setPlanningThreadIds(threadIdsWithStoredPlanningJobs());
  }, []);
  const [ready, setReady] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [collapsed, setCollapsed] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [renameThread, setRenameThread] = useState<ThreadItem | null>(null);
  const [renameTitle, setRenameTitle] = useState("");
  const [deleteThread, setDeleteThread] = useState<ThreadItem | null>(null);

  const loadThreads = useCallback(async () => {
    try {
      const data = await api<{ items: ThreadItem[] }>("/v1/threads?limit=80");
      setThreads(data.items);
    } catch {
      setThreads([]);
    }
  }, []);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setReady(true);
    loadThreads();
  }, [router, loadThreads]);

  useEffect(() => {
    const onRefresh = () => loadThreads();
    window.addEventListener(THREADS_REFRESH, onRefresh);
    return () => window.removeEventListener(THREADS_REFRESH, onRefresh);
  }, [loadThreads]);

  useEffect(() => {
    const onPlanning = (e: Event) => {
      const ce = e as CustomEvent<{ threadId: string; active: boolean }>;
      const { threadId, active } = ce.detail || {};
      if (!threadId) return;
      setPlanningThreadIds((prev) => {
        const next = new Set(prev);
        if (active) next.add(threadId);
        else next.delete(threadId);
        return next;
      });
    };
    window.addEventListener(PLANNING_ACTIVE, onPlanning);
    return () => window.removeEventListener(PLANNING_ACTIVE, onPlanning);
  }, []);

  useEffect(() => {
    if (!threads.length) return;
    const stored = threadIdsWithStoredPlanningJobs();
    const threadIdSet = new Set(threads.map((t) => t.id));
    setPlanningThreadIds((prev) => {
      const next = new Set(prev);
      for (const id of stored) {
        if (threadIdSet.has(id)) next.add(id);
      }
      for (const id of prev) {
        if (!threadIdSet.has(id)) next.delete(id);
      }
      return next;
    });
  }, [threads]);

  useEffect(() => {
    const onOpen = () => setSettingsOpen(true);
    window.addEventListener(OPEN_SETTINGS, onOpen);
    return () => window.removeEventListener(OPEN_SETTINGS, onOpen);
  }, []);

  useEffect(() => {
    setMobileNavOpen(false);
  }, [pathname]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return threads;
    return threads.filter((t) => t.title.toLowerCase().includes(q));
  }, [threads, query]);

  const grouped = useMemo(() => {
    const order: ("Today" | "Yesterday" | "Earlier")[] = [
      "Today",
      "Yesterday",
      "Earlier",
    ];
    const m: Record<string, ThreadItem[]> = {
      Today: [],
      Yesterday: [],
      Earlier: [],
    };
    for (const t of filtered) {
      m[bucketLabel(t.updated_at)].push(t);
    }
    return order.map((k) => ({ key: k, items: m[k] }));
  }, [filtered]);

  const [isMd, setIsMd] = useState<boolean | null>(null);
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 768px)");
    const apply = () => setIsMd(mq.matches);
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, []);

  function newChat() {
    router.push("/chat");
  }

  function logout() {
    clearToken();
    router.replace("/login");
  }

  async function submitRename() {
    if (!renameThread || !renameTitle.trim()) return;
    try {
      await api(`/v1/threads/${renameThread.id}`, {
        method: "PATCH",
        body: JSON.stringify({ title: renameTitle.trim() }),
      });
      setRenameThread(null);
      setRenameTitle("");
      loadThreads();
      window.dispatchEvent(new Event(THREADS_REFRESH));
    } catch (e) {
      console.error(e);
    }
  }

  async function submitDelete() {
    if (!deleteThread) return;
    try {
      await api(`/v1/threads/${deleteThread.id}`, { method: "DELETE" });
      if (pathname === `/chat/${deleteThread.id}`) router.push("/chat");
      setDeleteThread(null);
      loadThreads();
      window.dispatchEvent(new Event(THREADS_REFRESH));
    } catch (e) {
      console.error(e);
    }
  }

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-black">
        <div className="h-8 w-8 rounded-full skeleton" />
      </div>
    );
  }

  const asideX =
    isMd === null
      ? undefined
      : isMd
        ? 0
        : mobileNavOpen
          ? 0
          : "-100%";

  return (
    <div className="flex h-[100dvh] bg-black text-white">
      <AnimatePresence>
        {mobileNavOpen && (
          <motion.button
            key="nav-backdrop"
            type="button"
            aria-label="Close menu"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.22 }}
            className="fixed inset-0 z-40 bg-black/75 md:hidden"
            onClick={() => setMobileNavOpen(false)}
          />
        )}
      </AnimatePresence>

      <motion.aside
        initial={false}
        animate={asideX !== undefined ? { x: asideX } : false}
        transition={{ type: "spring", stiffness: 420, damping: 38, mass: 0.7 }}
        className={`fixed inset-y-0 left-0 z-50 flex shrink-0 flex-col border-r border-white/[0.06] bg-black will-change-transform transition-[width] duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] md:relative md:z-0 ${
          isMd === null ? "-translate-x-full md:translate-x-0" : ""
        } ${
          collapsed
            ? "w-14 md:w-14"
            : "w-[min(280px,88vw)] md:w-[min(280px,82vw)]"
        }`}
      >
        <div
          className={`flex h-full flex-col ${collapsed ? "items-center px-1" : "px-2"} py-2`}
        >
          <div
            className={`mb-3 flex items-center ${collapsed ? "flex-col gap-3" : "justify-between px-1"}`}
          >
            <Link
              href="/chat"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-white transition-colors duration-200 hover:bg-white/[0.06]"
              aria-label="Home"
              onClick={() => setMobileNavOpen(false)}
            >
              <LogoMark />
            </Link>
            {!collapsed && (
              <button
                type="button"
                aria-label="Collapse sidebar"
                onClick={() => setCollapsed(true)}
                className="hidden h-9 w-9 items-center justify-center rounded-full text-[#707070] transition-colors duration-200 hover:bg-white/[0.06] hover:text-white md:flex"
              >
                <ChevronPair />
              </button>
            )}
            {collapsed && (
              <button
                type="button"
                aria-label="Expand sidebar"
                onClick={() => setCollapsed(false)}
                className="hidden h-9 w-9 items-center justify-center rounded-full text-[#707070] transition-colors duration-200 hover:bg-white/[0.06] hover:text-white md:flex"
              >
                <ChevronPairRight />
              </button>
            )}
          </div>

          {!collapsed && (
            <>
              <button
                type="button"
                onClick={() => setSearchOpen((v) => !v)}
                className="mb-1 flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-[15px] font-semibold tracking-tight text-white transition-colors duration-200 hover:bg-white/[0.06]"
              >
                <SearchIcon />
                Search
              </button>
              <button
                type="button"
                onClick={newChat}
                className="mb-4 flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-[15px] font-semibold tracking-tight text-white transition-colors duration-200 hover:bg-white/[0.06]"
              >
                <ChatComposeIcon />
                Chat
              </button>

              {searchOpen && (
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search chats…"
                  className="mb-3 w-full rounded-2xl border border-white/[0.08] bg-[#141414] px-3 py-2 text-[13px] text-white placeholder:text-[#606060] focus:border-white/[0.14] focus:outline-none"
                />
              )}

              
            </>
          )}

          {collapsed && (
            <div className="mt-2 flex flex-col items-center gap-1">
              <button
                type="button"
                onClick={() => {
                  setCollapsed(false);
                  setSearchOpen(true);
                }}
                className="flex h-10 w-10 items-center justify-center rounded-full text-[#a0a0a0] transition-colors hover:bg-white/[0.06] hover:text-white"
                aria-label="Search"
              >
                <SearchIcon />
              </button>
              <button
                type="button"
                onClick={newChat}
                className="flex h-10 w-10 items-center justify-center rounded-full text-[#a0a0a0] transition-colors hover:bg-white/[0.06] hover:text-white"
                aria-label="New chat"
              >
                <ChatComposeIcon />
              </button>
            </div>
          )}

          <nav className="mt-2 min-h-0 flex-1 space-y-4 overflow-y-auto">
            {!collapsed &&
              grouped.map(({ key, items }) =>
                items.length ? (
                  <div key={key}>
                    <div className="relative mb-2 px-2">
                      <div className="absolute inset-x-0 top-1/2 h-px bg-white/[0.06]" />
                      <span className="relative bg-black px-1 text-[11px] font-medium uppercase tracking-wider text-[#505050]">
                        {key}
                      </span>
                    </div>
                    <div className="space-y-0.5">
                      {items.map((th) => (
                        <div
                          key={th.id}
                          className={`group/item flex items-center gap-0.5 rounded-2xl pr-1 transition-colors hover:bg-white/[0.04] ${
                            pathname === `/chat/${th.id}`
                              ? "bg-white/[0.08]"
                              : ""
                          }`}
                        >
                          <Link
                            href={`/chat/${th.id}`}
                            className="flex min-w-0 flex-1 items-center gap-2 px-3 py-2.5 text-[14px] font-semibold leading-snug tracking-tight text-[#ececec]"
                            onClick={() => setMobileNavOpen(false)}
                          >
                            {planningThreadIds.has(th.id) && (
                              <span
                                className="h-2 w-2 shrink-0 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.55)]"
                                title="Planning in progress"
                                aria-hidden
                              />
                            )}
                            <span className="line-clamp-1">{th.title}</span>
                          </Link>
                          <div className="relative shrink-0">
                            <button
                              type="button"
                              aria-label="Thread actions"
                              className="flex h-8 w-8 items-center justify-center rounded-full text-[#707070] opacity-100 transition-opacity hover:bg-white/[0.08] hover:text-white md:opacity-0 md:group-hover/item:opacity-100"
                              onClick={(e) => {
                                e.preventDefault();
                                setRenameThread(th);
                                setRenameTitle(th.title);
                              }}
                            >
                              ⋮
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null
              )}
          </nav>

          {!collapsed && (
            <div className="mt-auto border-t border-white/[0.06] pt-3">
              <div className="flex items-center gap-2 rounded-2xl border border-white/[0.08] bg-white/[0.03] p-1.5">
                <button
                  type="button"
                  onClick={() => setSettingsOpen(true)}
                  title="Settings"
                  aria-label="Settings"
                  className="flex flex-1 items-center justify-center gap-2 rounded-xl py-2.5 text-[12px] font-semibold text-[#c0c0c0] transition-colors hover:bg-white/[0.08] hover:text-white"
                >
                  <span className="text-[15px] leading-none opacity-90" aria-hidden>
                    ⚙
                  </span>
                  <span className="hidden sm:inline">Settings</span>
                </button>
                <span
                  className="h-6 w-px shrink-0 bg-white/[0.1]"
                  aria-hidden
                />
                <button
                  type="button"
                  title="Sign out"
                  aria-label="Sign out"
                  onClick={logout}
                  className="group flex flex-1 items-center justify-center gap-2 rounded-xl py-2.5 text-[12px] font-semibold text-[#a0a0a0] transition-colors hover:bg-red-500/15 hover:text-red-300"
                >
                  <span className="text-[#c0c0c0] group-hover:text-red-300">
                    <SignOutIcon />
                  </span>
                  <span className="hidden sm:inline">Log out</span>
                </button>
              </div>
            </div>
          )}
          {collapsed && (
            <div className="mt-auto flex flex-col items-center justify-center gap-2 pb-2">
              <button
                type="button"
                title="Settings"
                aria-label="Settings"
                onClick={() => setSettingsOpen(true)}
                className="flex h-10 w-10 items-center justify-center rounded-full border border-white/[0.1] bg-white/[0.05] text-[16px] text-[#c0c0c0] transition-colors hover:bg-white/[0.1] hover:text-white"
              >
                ⚙
              </button>
              <button
                type="button"
                aria-label="Sign out"
                title="Sign out"
                onClick={logout}
                className="flex h-10 w-10 items-center justify-center rounded-full border border-white/[0.08] bg-white/[0.04] text-red-400/90 transition-colors hover:border-red-500/30 hover:bg-red-500/15 hover:text-red-300"
              >
                <SignOutIcon />
              </button>
            </div>
          )}
        </div>
      </motion.aside>

      <div className="relative flex min-w-0 flex-1 flex-col">
        <button
          type="button"
          aria-label={mobileNavOpen ? "Close sidebar" : "Open sidebar"}
          onClick={() => setMobileNavOpen((v) => !v)}
          className="fixed left-3 top-3 z-30 flex h-10 w-10 items-center justify-center rounded-full border border-white/[0.1] bg-black/90 text-lg text-white shadow-lg backdrop-blur-sm md:hidden"
        >
          {mobileNavOpen ? "×" : "☰"}
        </button>
        <main className="min-h-0 min-w-0 flex-1 overflow-hidden bg-black">
          {children}
        </main>
      </div>

      <SettingsModal open={settingsOpen} onClose={() => setSettingsOpen(false)} />

      {renameThread && (
        <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/75 p-4">
          <div className="w-full max-w-md rounded-3xl border border-white/[0.1] bg-[#111] p-5">
            <h2 className="text-[15px] font-semibold">Rename chat</h2>
            <input
              value={renameTitle}
              onChange={(e) => setRenameTitle(e.target.value)}
              className="mt-3 w-full rounded-2xl border border-white/[0.1] bg-black px-3 py-2.5 text-[15px] text-white"
            />
            <div className="mt-4 flex flex-wrap justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  setDeleteThread(renameThread);
                  setRenameThread(null);
                }}
                className="mr-auto rounded-full px-4 py-2 text-[13px] text-red-400 hover:bg-red-500/10"
              >
                Delete…
              </button>
              <button
                type="button"
                onClick={() => setRenameThread(null)}
                className="rounded-full px-4 py-2 text-[13px] text-[#909090]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={submitRename}
                className="rounded-full bg-white px-5 py-2 text-[13px] font-semibold text-black"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {deleteThread && (
        <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/75 p-4">
          <div className="w-full max-w-md rounded-3xl border border-white/[0.1] bg-[#111] p-5">
            <h2 className="text-[15px] font-semibold">Delete chat?</h2>
            <p className="mt-2 text-[13px] text-[#909090]">
              {deleteThread.title}
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setDeleteThread(null)}
                className="rounded-full px-4 py-2 text-[13px] text-[#909090]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={submitDelete}
                className="rounded-full bg-red-600 px-5 py-2 text-[13px] font-semibold text-white hover:bg-red-500"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function LogoMark() {
  return (
    <img src="/imageBlack.png" alt="logo" />
  );
}

function ChevronPair() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    >
      <path d="M11 17l-5-5 5-5M18 17l-5-5 5-5" />
    </svg>
  );
}

function ChevronPairRight() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    >
      <path d="M13 7l5 5-5 5M6 7l5 5-5 5" />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
    >
      <circle cx="11" cy="11" r="7" />
      <path d="M20 20l-4-4" strokeLinecap="round" />
    </svg>
  );
}

function ChatComposeIcon() {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    >
      <path d="M12 20h9M16.5 3.5a2.12 2.12 0 013 3L7 19l-4 1 1-4L16.5 3.5z" />
    </svg>
  );
}

function SignOutIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.85"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
    >
      <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9" />
    </svg>
  );
}

export { OPEN_SETTINGS, THREADS_REFRESH } from "@/lib/appEvents";
