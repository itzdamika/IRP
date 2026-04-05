"use client";

import type { ReactNode } from "react";
import { useCallback, useRef } from "react";
import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";

function PreWithCopy({ children }: { children?: ReactNode }) {
  const preRef = useRef<HTMLPreElement>(null);
  const copy = useCallback(() => {
    const t = preRef.current?.innerText ?? "";
    if (t) void navigator.clipboard.writeText(t);
  }, []);

  return (
    <div className="group relative my-5">
      <button
        type="button"
        onClick={copy}
        className="absolute right-3 top-3 z-10 rounded-full border border-white/[0.08] bg-black/60 px-2.5 py-1 text-[11px] font-medium text-[#a0a0a0] opacity-0 transition-all duration-200 hover:border-white/[0.14] hover:bg-white/[0.06] hover:text-white group-hover:opacity-100"
      >
        Copy
      </button>
      <pre
        ref={preRef}
        className="overflow-x-auto rounded-2xl bg-[#171717] p-4 text-[13px] leading-relaxed text-[#e8e8e8] [&_.hljs]:bg-transparent"
      >
        {children}
      </pre>
    </div>
  );
}

export function MessageMarkdown({ content }: { content: string }) {
  return (
    <div className="arkon-md text-[15px] leading-[1.65] text-white">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          pre({ children }) {
            return <PreWithCopy>{children}</PreWithCopy>;
          },
          code({ className, children, ...props }) {
            const isBlock = /language-/.test(className || "");
            if (isBlock) {
              return (
                <code className={className} {...props}>
                  {children}
                </code>
              );
            }
            return (
              <code
                className="rounded-md bg-[#2a1f18] px-1.5 py-0.5 text-[0.88em] text-[#fdba74]"
                {...props}
              >
                {children}
              </code>
            );
          },
          h1({ children }) {
            return (
              <h1 className="mb-3 mt-6 text-xl font-semibold tracking-tight text-white first:mt-0">
                {children}
              </h1>
            );
          },
          h2({ children }) {
            return (
              <h2 className="mb-2 mt-5 text-lg font-semibold tracking-tight text-white first:mt-0">
                {children}
              </h2>
            );
          },
          h3({ children }) {
            return (
              <h3 className="mb-2 mt-4 text-base font-semibold text-white first:mt-0">
                {children}
              </h3>
            );
          },
          p({ children }) {
            return <p className="mb-3 last:mb-0 text-[#ececec]">{children}</p>;
          },
          ul({ children }) {
            return (
              <ul className="mb-3 list-disc space-y-1.5 pl-5 text-[#ececec]">
                {children}
              </ul>
            );
          },
          ol({ children }) {
            return (
              <ol className="mb-3 list-decimal space-y-1.5 pl-5 text-[#ececec]">
                {children}
              </ol>
            );
          },
          li({ children }) {
            return <li className="marker:text-[#707070]">{children}</li>;
          },
          a({ href, children }) {
            return (
              <a
                href={href}
                className="text-white underline decoration-white/30 underline-offset-2 transition hover:decoration-white/60"
                target="_blank"
                rel="noreferrer"
              >
                {children}
              </a>
            );
          },
          blockquote({ children }) {
            return (
              <blockquote className="my-3 border-l-2 border-white/20 pl-4 text-[#b8b8b8]">
                {children}
              </blockquote>
            );
          },
          hr() {
            return <hr className="my-6 border-0 border-t border-white/[0.08]" />;
          },
          table({ children }) {
            return (
              <div className="my-4 overflow-x-auto rounded-xl border border-white/[0.08]">
                <table className="w-full border-collapse text-sm">{children}</table>
              </div>
            );
          },
          th({ children }) {
            return (
              <th className="border-b border-white/[0.08] bg-white/[0.04] px-3 py-2 text-left font-medium text-white">
                {children}
              </th>
            );
          },
          td({ children }) {
            return (
              <td className="border-b border-white/[0.06] px-3 py-2 text-[#d0d0d0]">
                {children}
              </td>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
