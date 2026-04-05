import Image from "next/image";
import type { ReactNode } from "react";

const checks = [
  "Multi-agent architecture planning",
  "Live validation and audit scoring",
  "Export a governed PDF report",
];

export function AuthShell({
  children,
  subtitle,
  title,
}: {
  children: ReactNode;
  subtitle: string;
  title: string;
}) {
  return (
    <div className="min-h-[100dvh] bg-black text-white">
      <div className="grid min-h-[100dvh] md:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)]">
      <aside className="relative hidden flex-col overflow-hidden border-b border-white/[0.06] bg-[#050505] px-20 py-12 md:flex md:border-b-0 md:border-r">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.12]"
          style={{
            backgroundImage: `radial-gradient(circle at 1px 1px, rgba(255,255,255,0.14) 1px, transparent 0)`,
            backgroundSize: "28px 28px",
          }}
          aria-hidden
        />

        <div className="relative z-[1] flex flex-1 flex-col justify-center pb-16">
          <div className="flex items-center gap-3">
            <div className="relative h-10 w-10 overflow-hidden rounded-xl border border-white/[0.1] bg-white/[0.04]">
              <Image
                src="/Arkonlogo.png"
                alt=""
                fill
                className="object-cover"
                sizes="40px"
                priority
              />
            </div>
            <span className="text-[18px] font-semibold tracking-tight">
              Arkon
            </span>
          </div>
          <h1 className="mt-14 max-w-sm text-[28px] font-semibold leading-tight tracking-tight text-white md:text-[32px]">
            Architecture intelligence,
            <span className="text-white/50"> governed.</span>
          </h1>
          <ul className="mt-10 space-y-4">
            {checks.map((line) => (
              <li key={line} className="flex items-start gap-3 text-[14px] text-[#b0b0b0]">
                <span
                  className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-white/15 bg-white/[0.04] text-[11px] text-white/70"
                  aria-hidden
                >
                  ✓
                </span>
                {line}
              </li>
            ))}
          </ul>
        </div>

        <p className="relative z-[1] mt-auto text-[11px] font-medium uppercase tracking-wider text-[#505050]">
          Requirements → planning → validated blueprint
        </p>
      </aside>

        <div className="flex flex-col justify-center px-5 py-12 sm:px-10 md:px-14 lg:px-20">
          <div className="mx-auto w-full max-w-[400px]">
            <div className="mb-8 flex justify-center md:hidden">
              <div className="flex items-center gap-2.5">
                <div className="relative h-9 w-9 overflow-hidden rounded-lg border border-white/[0.1] bg-white/[0.04]">
                  <Image
                    src="/Arkonlogo.png"
                    alt=""
                    fill
                    className="object-cover"
                    sizes="36px"
                  />
                </div>
                <span className="text-[17px] font-semibold">Arkon</span>
              </div>
            </div>
            <p className="text-center text-[11px] font-semibold uppercase tracking-[0.2em] text-[#606060] md:text-left">
              {subtitle}
            </p>
            <h2 className="mt-2 text-center text-[26px] font-semibold tracking-tight md:text-left">
              {title}
            </h2>
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
