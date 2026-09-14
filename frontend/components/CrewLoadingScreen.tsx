"use client";

import { useEffect, useState } from "react";
import { AGENT_STAGES } from "@/lib/agents";

const STATUS_ORDER = ["researching", "writing", "editing", "seo_optimizing", "generating_image", "social_adapting"];

// Light, generic flavor lines that rotate underneath the stage-specific
// detail — a small bit of personality for what would otherwise be a static
// wait. Kept short and calm; this is routine software status, not a moment
// that needs jokes or high energy.
const FLAVOR_LINES = [
  "Still going",
  "Working through it",
  "On track",
  "Making progress",
];

function useElapsedSeconds() {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const startedAt = Date.now();
    const interval = setInterval(() => setSeconds(Math.floor((Date.now() - startedAt) / 1000)), 1000);
    return () => clearInterval(interval);
  }, []);
  return seconds;
}

function formatElapsed(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return minutes > 0 ? `${minutes}m ${seconds.toString().padStart(2, "0")}s` : `${seconds}s`;
}

/**
 * Full-screen popup shown while the crew is working. Reflects real backend
 * progress (ContentCrew fires a status update as each task actually
 * completes — see app/crew/content_crew.py) rather than guessing from a
 * timer. The elapsed-time counter and rotating flavor line are purely
 * local/cosmetic reassurance that something is still happening.
 */
export default function CrewLoadingScreen({ status }: { status: string }) {
  const elapsed = useElapsedSeconds();
  const rawIndex = STATUS_ORDER.indexOf(status);
  const activeIndex = rawIndex === -1 ? 0 : rawIndex; // "pending" -> about to start research
  const activeAgent = AGENT_STAGES[activeIndex];

  const [flavorIndex, setFlavorIndex] = useState(0);
  useEffect(() => {
    const interval = setInterval(() => {
      setFlavorIndex((i) => (i + 1) % FLAVOR_LINES.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed inset-0 z-50 flex items-center justify-center bg-canvas/92 backdrop-blur-md px-6"
    >
      <div className="flex flex-col items-center text-center max-w-xs">
        <div className="relative w-28 h-28 flex items-center justify-center mb-8">
          <div
            className="loading-glow absolute inset-0 rounded-full"
            style={{ boxShadow: `0 0 60px 10px ${activeAgent.hex}35` }}
          />
          <div
            className="absolute inset-0 rounded-full border-2 border-transparent animate-spin"
            style={{
              borderTopColor: activeAgent.hex,
              borderRightColor: `${activeAgent.hex}40`,
              animationDuration: "1.3s",
            }}
          />
          <div
            className="absolute inset-3 rounded-full"
            style={{ backgroundColor: `${activeAgent.hex}14` }}
          />
          <span className="relative font-display text-2xl font-semibold" style={{ color: activeAgent.hex }}>
            {activeIndex + 1}/6
          </span>
        </div>

        <p className="font-display text-xl font-semibold text-ink">{activeAgent.label}</p>
        <p className="text-muted text-sm mt-1.5">{activeAgent.role}</p>

        <div className="flex items-center gap-2 mt-7">
          {AGENT_STAGES.map((agent, i) => (
            <span
              key={agent.key}
              className="w-1.5 h-1.5 rounded-full transition-colors duration-500"
              style={{ backgroundColor: i <= activeIndex ? agent.hex : "#262C4A" }}
            />
          ))}
        </div>

        <p className="text-xs text-muted mt-6 tabular-nums">
          {formatElapsed(elapsed)} · {FLAVOR_LINES[flavorIndex]}
        </p>
      </div>
    </div>
  );
}