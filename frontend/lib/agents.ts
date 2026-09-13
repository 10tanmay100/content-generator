/**
 * Single source of truth for the six pipeline agents: name, one-line role,
 * and accent color (matching tailwind.config.ts's `agent.*` palette). Used
 * by both the homepage relay diagram and the job progress tracker so the
 * same color always means the same stage.
 */
export interface AgentStage {
  key: "research" | "writing" | "editing" | "seo" | "image" | "social";
  label: string;
  role: string;
  colorVar: string; // Tailwind class fragment, e.g. "agent-research"
  hex: string; // for inline SVG/style use
}

export const AGENT_STAGES: AgentStage[] = [
  { key: "research", label: "Research", role: "Gathers facts and sources", colorVar: "agent-research", hex: "#4FD8E8" },
  { key: "writing", label: "Writing", role: "Drafts the article", colorVar: "agent-writing", hex: "#9B87F6" },
  { key: "editing", label: "Editing", role: "Tightens and fact-checks", colorVar: "agent-editing", hex: "#F6B94D" },
  { key: "seo", label: "SEO", role: "Scores and optimizes", colorVar: "agent-seo", hex: "#46E0A0" },
  { key: "image", label: "Image", role: "Generates the hero image", colorVar: "agent-image", hex: "#F773B8" },
  { key: "social", label: "Social", role: "Repurposes for social", colorVar: "agent-social", hex: "#5B9DF9" },
];
