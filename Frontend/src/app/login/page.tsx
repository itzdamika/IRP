"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { AuthShell } from "@/components/auth/AuthShell";
import { api, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    setLoading(true);
    try {
      const data = await api<{ access_token: string }>("/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(data.access_token);
      router.push("/chat");
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell subtitle="Account" title="Welcome back">
      <form onSubmit={onSubmit} className="mt-8 space-y-5">
        <div>
          <label className="text-[11px] font-semibold uppercase tracking-wider text-[#606060]">
            Email
          </label>
          <input
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            className="mt-2 w-full rounded-2xl border border-white/[0.1] bg-[#0c0c0c] px-4 py-3 text-[15px] text-white outline-none transition placeholder:text-[#404040] focus:border-white/[0.22] focus:ring-1 focus:ring-white/10"
          />
        </div>
        <div>
          <div className="flex items-baseline justify-between gap-2">
            <label className="text-[11px] font-semibold uppercase tracking-wider text-[#606060]">
              Password
            </label>
          </div>
          <input
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-2 w-full rounded-2xl border border-white/[0.1] bg-[#0c0c0c] px-4 py-3 text-[15px] text-white outline-none transition focus:border-white/[0.22] focus:ring-1 focus:ring-white/10"
          />
        </div>
        {err && (
          <p className="rounded-xl border border-red-500/20 bg-red-500/10 px-3 py-2 text-[13px] text-red-300/95">
            {err.slice(0, 200)}
          </p>
        )}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-full bg-white py-3.5 text-[14px] font-semibold text-black transition hover:bg-[#e8e8e8] disabled:opacity-45"
        >
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <p className="mt-8 text-center text-[13px] text-[#707070] md:text-left">
        No account?{" "}
        <Link
          href="/signup"
          className="font-medium text-white underline decoration-white/25 underline-offset-4 transition hover:decoration-white/60"
        >
          Create account
        </Link>
      </p>
    </AuthShell>
  );
}
