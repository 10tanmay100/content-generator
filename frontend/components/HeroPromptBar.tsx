"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function HeroPromptBar() {
  const router = useRouter();
  const [topic, setTopic] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = topic.trim();
    if (trimmed.length < 3) return;
    router.push(`/generate?topic=${encodeURIComponent(trimmed)}`);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-xl mx-auto flex items-center gap-2 rounded-2xl bg-surface border border-edge p-2 pl-5 shadow-[0_0_40px_-12px_rgba(155,135,246,0.35)] focus-within:border-agent-writing/60 transition-colors"
    >
      <input
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        placeholder="How AI is changing customer support"
        className="flex-1 bg-transparent text-ink placeholder:text-muted outline-none text-sm py-2"
      />
      <button
        type="submit"
        className="shrink-0 bg-agent-writing hover:brightness-110 text-canvas font-medium text-sm px-5 py-2.5 rounded-xl transition"
      >
        Generate
      </button>
    </form>
  );
}
