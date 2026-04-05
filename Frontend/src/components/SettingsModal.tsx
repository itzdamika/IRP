"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";

type Settings = {
  pass_threshold: number;
  max_planning_rounds: number;
  max_requirement_hops: number;
  report_depth: string;
  thinking_enabled: boolean;
  show_internal_panels: boolean;
  theme: string;
};

type Props = {
  open: boolean;
  onClose: () => void;
};

export function SettingsModal({ open, onClose }: Props) {
  const [s, setS] = useState<Settings | null>(null);
  const [saved, setSaved] = useState(false);
  const [err, setErr] = useState("");

  const load = useCallback(() => {
    api<Settings>("/v1/settings")
      .then(setS)
      .catch(() => setS(null));
  }, []);

  useEffect(() => {
    if (open) {
      setErr("");
      load();
    }
  }, [open, load]);

  async function save() {
    if (!s) return;
    setErr("");
    try {
      await api("/v1/settings", { method: "PUT", body: JSON.stringify(s) });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Save failed");
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <motion.button
            type="button"
            aria-label="Close"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/75"
            onClick={onClose}
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            initial={{ opacity: 0, scale: 0.97, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: 8 }}
            className="relative z-10 max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-3xl border border-white/[0.1] bg-[#0a0a0a] p-6 shadow-2xl"
          >
            <div className="mb-4 flex items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-white">Settings</h2>
                <p className="mt-1 text-[13px] text-[#707070]">
                  Governance thresholds and display options
                </p>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="rounded-full px-3 py-1 text-[13px] text-[#909090] hover:bg-white/[0.06] hover:text-white"
              >
                Close
              </button>
            </div>

            {!s ? (
              <div className="flex justify-center py-12">
                <div className="h-8 w-48 rounded-full skeleton" />
              </div>
            ) : (
              <>
                <div className="space-y-4 text-sm">
                  <label className="block">
                    <span className="text-[#707070]">Pass threshold (7–10)</span>
                    <input
                      type="number"
                      step={0.1}
                      min={7}
                      max={10}
                      value={s.pass_threshold}
                      onChange={(e) =>
                        setS({
                          ...s,
                          pass_threshold: parseFloat(e.target.value),
                        })
                      }
                      className="mt-1 w-full rounded-2xl border border-white/[0.08] bg-black px-3 py-2 text-white"
                    />
                  </label>
                  <label className="block">
                    <span className="text-[#707070]">Max planning rounds</span>
                    <input
                      type="number"
                      min={1}
                      max={50}
                      value={s.max_planning_rounds}
                      onChange={(e) =>
                        setS({
                          ...s,
                          max_planning_rounds: parseInt(e.target.value, 10),
                        })
                      }
                      className="mt-1 w-full rounded-2xl border border-white/[0.08] bg-black px-3 py-2 text-white"
                    />
                  </label>
                  <label className="block">
                    <span className="text-[#707070]">Report depth</span>
                    <select
                      value={s.report_depth}
                      onChange={(e) =>
                        setS({ ...s, report_depth: e.target.value })
                      }
                      className="mt-1 w-full rounded-2xl border border-white/[0.08] bg-black px-3 py-2 text-white"
                    >
                      <option value="medium">medium</option>
                      <option value="long">long</option>
                      <option value="extreme">extreme</option>
                    </select>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={s.thinking_enabled}
                      onChange={(e) =>
                        setS({ ...s, thinking_enabled: e.target.checked })
                      }
                    />
                    <span>Thinking / debug traces</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={s.show_internal_panels}
                      onChange={(e) =>
                        setS({ ...s, show_internal_panels: e.target.checked })
                      }
                    />
                    <span>Show internal thinking panels</span>
                  </label>
                </div>
                {err && (
                  <p className="mt-3 text-xs text-red-400">{err.slice(0, 200)}</p>
                )}
                <button
                  type="button"
                  onClick={save}
                  className="mt-6 w-full rounded-full bg-white py-3 text-sm font-semibold text-black hover:bg-[#e8e8e8]"
                >
                  Save
                </button>
                {saved && (
                  <p className="mt-2 text-center text-xs text-emerald-500">
                    Saved.
                  </p>
                )}
              </>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
