"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { OPEN_SETTINGS } from "@/lib/appEvents";

export default function SettingsPage() {
  const router = useRouter();
  useEffect(() => {
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent(OPEN_SETTINGS));
    }
    router.replace("/chat");
  }, [router]);
  return (
    <div className="flex min-h-screen items-center justify-center bg-black text-[#707070]">
      Opening settings…
    </div>
  );
}
