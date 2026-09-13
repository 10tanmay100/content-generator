"use client";

import { AGENT_STAGES } from "@/lib/agents";

const STATUS_ORDER = ["researching", "writing", "editing", "seo_optimizing", "generating_image", "social_adapting"];

export default function AgentProgress({ status }: { status: string }) {
  const currentIndex = STATUS_ORDER.indexOf(status);
  const isCompleted = status === "completed";
  const isFailed = status === "failed";

  return (
    <div className="flex flex-wrap gap-2.5">
      {AGENT_STAGES.map((agent, i) => {
        const isDone = isCompleted || i < currentIndex;
        const isActive = i === currentIndex;
        const color = isDone || isActive ? agent.hex : "#262C4A";
        return (
          <div
            key={agent.key}
            className="flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs transition-colors"
            style={{
              borderColor: color,
              backgroundColor: isActive ? `${agent.hex}1F` : "transparent",
              color: isDone || isActive ? agent.hex : "#9098B8",
            }}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${isActive ? "animate-pulse" : ""}`}
              style={{ backgroundColor: color }}
            />
            {agent.label}
          </div>
        );
      })}
      {isFailed && (
        <div className="flex items-center gap-2 rounded-full border border-red-500 px-3 py-1.5 text-xs text-red-400">
          <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
          Failed
        </div>
      )}
    </div>
  );
}
