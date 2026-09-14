"use client";

import { useState } from "react";
import ContentForm from "@/components/ContentForm";

/**
 * Gates the full form behind a single "Start" action. If a topic already
 * arrived from the homepage's prompt bar, skip the gate entirely — typing a
 * topic and hitting enter there already IS starting, asking again would be
 * redundant friction.
 */
export default function GenerateFlow({ initialTopic }: { initialTopic?: string }) {
  const [started, setStarted] = useState(Boolean(initialTopic));

  if (!started) {
    return (
      <div className="py-6 text-center">
        <button
          onClick={() => setStarted(true)}
          className="bg-agent-writing hover:brightness-110 text-canvas font-medium px-8 py-3.5 rounded-xl transition"
        >
          Start
        </button>
      </div>
    );
  }

  return (
    <div className="animate-[fadeIn_0.4s_ease-out]">
      <ContentForm initialTopic={initialTopic} />
    </div>
  );
}