"use client";

import ReactMarkdown from "react-markdown";
import type { JobRecord } from "@/lib/api";

const SOCIAL_LABELS: Record<string, string> = {
  twitter_thread: "Twitter thread",
  linkedin_post: "LinkedIn post",
  instagram_caption: "Instagram caption",
};

export default function ContentPreview({ job }: { job: JobRecord }) {
  const result = job.result;
  if (!result) return null;

  return (
    <div className="space-y-5">
      <div className="bg-surface rounded-2xl border border-edge p-6 md:p-8">
        <div className="prose-content">
          <ReactMarkdown>{result.body_markdown}</ReactMarkdown>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-5">
        <div className="bg-surface rounded-2xl border border-edge p-5">
          <p className="text-sm font-medium text-agent-seo mb-2">SEO</p>
          <p className="text-2xl font-display font-semibold text-ink">
            {result.seo_score ?? "—"}<span className="text-muted text-base font-body">/100</span>
          </p>
          <p className="text-sm text-muted mt-2 leading-relaxed">{result.meta_description}</p>
          <div className="flex flex-wrap gap-1.5 mt-3">
            {result.seo_keywords.map((k) => (
              <span key={k} className="text-xs bg-agent-seo/10 text-agent-seo px-2 py-0.5 rounded-full">{k}</span>
            ))}
          </div>
        </div>

        <div className="bg-surface rounded-2xl border border-edge p-5">
          <p className="text-sm font-medium text-agent-image mb-2">Hero image</p>
          {result.image_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={result.image_url}
              alt={result.alt_text ?? result.image_prompt ?? "Generated hero image"}
              className="rounded-xl w-full object-cover mb-2 border border-edge"
            />
          ) : (
            <p className="text-sm text-muted mb-2">Not generated for this run.</p>
          )}
          <p className="text-xs text-muted leading-relaxed">{result.image_prompt}</p>
        </div>
      </div>

      {Object.keys(result.social_variants).length > 0 && (
        <div className="bg-surface rounded-2xl border border-edge p-5">
          <p className="text-sm font-medium text-agent-social mb-4">Social variants</p>
          <div className="space-y-4">
            {Object.entries(result.social_variants).map(([platform, text]) => (
              <div key={platform}>
                <p className="text-xs text-muted mb-1">{SOCIAL_LABELS[platform] ?? platform}</p>
                <p className="text-sm text-ink/90 whitespace-pre-wrap leading-relaxed">{text}</p>
              </div>
            ))}
          </div>
          {result.hashtags.length > 0 && (
            <p className="text-xs text-agent-social mt-4">{result.hashtags.join(" ")}</p>
          )}
        </div>
      )}

      {result.sources.length > 0 && (
        <div className="bg-surface rounded-2xl border border-edge p-5">
          <p className="text-sm font-medium text-agent-research mb-2">Sources</p>
          <ul className="text-sm text-muted list-disc pl-5 space-y-1">
            {result.sources.map((s) => (
              <li key={s}>
                <a href={s} target="_blank" rel="noreferrer" className="hover:text-ink transition-colors">
                  {s}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
