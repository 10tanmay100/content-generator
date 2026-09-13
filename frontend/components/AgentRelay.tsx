import { AGENT_STAGES } from "@/lib/agents";

/**
 * Static relay diagram of the six agents, connected by a line with a single
 * traveling glow (see .relay-pulse in globals.css) — the page's one
 * deliberate motion moment, representing work flowing through the pipeline.
 */
export default function AgentRelay() {
  return (
    <div className="w-full overflow-x-auto">
      <div className="relative flex items-start justify-between gap-2 min-w-[640px] max-w-3xl mx-auto px-4">
        {/* Connector line + traveling pulse share one relatively-positioned
            track so the pulse's left:0%->100% always matches the line's
            actual rendered width, at any viewport size. */}
        <div className="absolute top-[14px] left-8 right-8 h-px bg-edge" aria-hidden="true">
          <div className="relative w-full h-full">
            <div
              className="absolute -top-[3.5px] w-2 h-2 rounded-full bg-white shadow-[0_0_12px_4px_rgba(255,255,255,0.6)] relay-pulse"
              aria-hidden="true"
            />
          </div>
        </div>

        {AGENT_STAGES.map((agent) => (
          <div key={agent.key} className="relative z-10 flex flex-col items-center gap-3 w-24">
            <span
              className="w-9 h-9 rounded-full flex items-center justify-center border-2"
              style={{ borderColor: agent.hex, boxShadow: `0 0 16px 0 ${agent.hex}55` }}
            >
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: agent.hex }} />
            </span>
            <div className="text-center">
              <p className="text-sm font-medium text-ink">{agent.label}</p>
              <p className="text-xs text-muted mt-0.5 leading-tight">{agent.role}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
