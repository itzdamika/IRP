"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/** Chromium / Safari Web Speech API (not in default TS DOM typings). */
type SpeechRecognitionAlternative = { readonly transcript: string };
type SpeechRecognitionResult = {
  readonly isFinal: boolean;
  readonly length: number;
  readonly [index: number]: SpeechRecognitionAlternative;
};
type SpeechRecognitionResultList = {
  readonly length: number;
  readonly [index: number]: SpeechRecognitionResult;
};
type WebSpeechRecognitionEvent = Event & {
  readonly resultIndex: number;
  readonly results: SpeechRecognitionResultList;
};
type WebSpeechRecognition = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((ev: WebSpeechRecognitionEvent) => void) | null;
  onerror: ((ev: Event) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};
type WebSpeechRecognitionCtor = new () => WebSpeechRecognition;

type Props = {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  placeholder?: string;
  variant?: "landing" | "dock";
  className?: string;
};

export function ChatPillInput({
  value,
  onChange,
  onSubmit,
  disabled,
  placeholder = "Ask anything",
  variant = "dock",
  className = "",
}: Props) {
  const ta = useRef<HTMLTextAreaElement>(null);
  const recRef = useRef<WebSpeechRecognition | null>(null);
  const speechPrefixRef = useRef("");
  const speechFinalRef = useRef("");
  const [listening, setListening] = useState(false);

  const stopRecognition = useCallback(() => {
    const r = recRef.current;
    recRef.current = null;
    if (!r) return;
    try {
      r.onresult = null;
      r.onerror = null;
      r.onend = null;
      r.stop();
    } catch {
      try {
        r.abort();
      } catch {
        /* ignore */
      }
    }
    setListening(false);
  }, []);

  useEffect(() => () => stopRecognition(), [stopRecognition]);

  const toggleMic = useCallback(() => {
    if (disabled) return;
    const w = typeof window !== "undefined" ? window : null;
    const Ctor = w
      ? ((w as Window & { SpeechRecognition?: WebSpeechRecognitionCtor })
          .SpeechRecognition ||
        (w as Window & { webkitSpeechRecognition?: WebSpeechRecognitionCtor })
          .webkitSpeechRecognition)
      : null;
    if (!Ctor) return;
    if (listening) {
      stopRecognition();
      return;
    }
    speechPrefixRef.current =
      value.replace(/\s+$/, "") + (value.trim() ? " " : "");
    speechFinalRef.current = "";
    const r = new Ctor();
    recRef.current = r;
    r.continuous = true;
    r.interimResults = true;
    r.lang = navigator.language || "en-US";
    r.onresult = (event: WebSpeechRecognitionEvent) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const row = event.results[i];
        const piece = row[0]?.transcript ?? "";
        if (row.isFinal) speechFinalRef.current += piece;
        else interim += piece;
      }
      onChange(
        speechPrefixRef.current + speechFinalRef.current + interim
      );
    };
    r.onerror = () => stopRecognition();
    r.onend = () => {
      if (recRef.current === r) stopRecognition();
    };
    try {
      r.start();
      setListening(true);
    } catch {
      stopRecognition();
    }
  }, [disabled, listening, onChange, stopRecognition, value]);

  const padY = variant === "landing" ? "py-2.5" : "py-2";

  return (
    <div
      className={`flex w-full items-center rounded-full border border-white/[0.12] bg-[#1a1a1a] shadow-[0_0_0_1px_rgba(255,255,255,0.03)] transition-colors duration-200 focus-within:border-white/[0.18] ${padY} pl-3 pr-2 ${className}`}
    >
      <button
        type="button"
        aria-label="Attach"
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-[#b0b0b0] transition-colors duration-200 hover:bg-white/[0.06] hover:text-white disabled:opacity-30"
        disabled={true}
      >
        <PaperclipIcon />
      </button>
      <textarea
        ref={ta}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            onSubmit();
          }
        }}
        rows={1}
        placeholder={placeholder}
        style={{ height: "auto", minHeight: "22px", maxHeight: "8rem" }}
        onInput={(e) => {
          const el = e.currentTarget;
          el.style.height = "auto";
          el.style.height = `${Math.min(el.scrollHeight, 128)}px`;
        }}
        className="mx-1.5 min-h-[22px] min-w-0 flex-1 resize-none bg-transparent py-0.5 text-[15px] leading-[1.35] text-white placeholder:text-[#707070] focus:outline-none disabled:opacity-50"
      />
      <div className="flex shrink-0 items-center gap-0.5 pr-0.5">

        <button
          type="button"
          aria-label={listening ? "Stop dictation" : "Dictate"}
          aria-pressed={listening}
          disabled={disabled}
          onClick={toggleMic}
          className={`flex h-8 w-8 items-center justify-center rounded-full transition-colors duration-200 hover:bg-white/[0.06] disabled:opacity-30 ${
            listening
              ? "bg-red-500/20 text-red-300"
              : "text-[#b0b0b0] hover:text-white"
          }`}
        >
          <MicIcon active={listening} />
        </button>
        <button
          type="button"
          aria-label="Send"
          disabled={disabled || !value.trim()}
          onClick={onSubmit}
          className="ml-0.5 flex h-9 w-9 items-center justify-center rounded-full bg-[#ffffff] text-black shadow-md transition-all duration-200 hover:bg-[#6e6e6e] disabled:cursor-not-allowed disabled:opacity-35 disabled:hover:bg-[#525252]"
        >
          <ArrowUpIcon />
        </button>
      </div>
    </div>
  );
}

function PaperclipIcon() {
  return (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
    >
      <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
    </svg>
  );
}

function MicIcon({ active }: { active?: boolean }) {
  return (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      className={active ? "animate-pulse" : undefined}
    >
      <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" />
      <path d="M19 10v2a7 7 0 01-14 0v-2M12 19v4M8 23h8" />
    </svg>
  );
}

function ChevronIcon() {
  return (
    <svg
      width="11"
      height="11"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M6 9l6 6 6-6" />
    </svg>
  );
}

function ArrowUpIcon() {
  return (
    <svg
      width="17"
      height="17"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.2"
      strokeLinecap="round"
      className="text-black"
    >
      <path d="M12 19V5M5 12l7-7 7 7" />
    </svg>
  );
}
