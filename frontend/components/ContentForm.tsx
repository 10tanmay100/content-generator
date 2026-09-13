"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { ContentGenerationRequest } from "@/lib/api";

export default function ContentForm({ initialTopic }: { initialTopic?: string }) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [form, setForm] = useState<ContentGenerationRequest>({
    topic: initialTopic ?? "",
    content_format: "blog",
    tone: "professional",
    target_audience: "general readers",
    target_keywords: [],
    word_count: 900,
    generate_image: true,
    generate_social_variants: true,
  });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrorMsg(null);
    setSubmitting(true);
    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error("Generation request failed");
      const data = await res.json();
      router.push(`/preview/${data.job_id}`);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  const inputClasses =
    "w-full bg-surface2 border border-edge rounded-xl px-3 py-2.5 text-ink placeholder:text-muted text-sm outline-none focus:border-agent-writing/60 transition-colors";
  const labelClasses = "block text-sm text-muted mb-1.5";

  return (
    <form onSubmit={handleSubmit} className="bg-surface rounded-2xl border border-edge p-6 space-y-5">
      <div>
        <label className={labelClasses}>Topic</label>
        <input
          required
          minLength={3}
          value={form.topic}
          onChange={(e) => setForm({ ...form, topic: e.target.value })}
          placeholder="e.g. How AI is transforming customer support"
          className={inputClasses}
        />
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <label className={labelClasses}>Format</label>
          <select
            value={form.content_format}
            onChange={(e) => setForm({ ...form, content_format: e.target.value as ContentGenerationRequest["content_format"] })}
            className={inputClasses}
          >
            <option value="blog">Blog post</option>
            <option value="social">Social post</option>
            <option value="email">Email</option>
            <option value="newsletter">Newsletter</option>
          </select>
        </div>
        <div>
          <label className={labelClasses}>Tone</label>
          <select
            value={form.tone}
            onChange={(e) => setForm({ ...form, tone: e.target.value })}
            className={inputClasses}
          >
            <option value="professional">Professional</option>
            <option value="casual">Casual</option>
            <option value="witty">Witty</option>
            <option value="authoritative">Authoritative</option>
          </select>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <label className={labelClasses}>Target audience</label>
          <input
            value={form.target_audience}
            onChange={(e) => setForm({ ...form, target_audience: e.target.value })}
            className={inputClasses}
          />
        </div>
        <div>
          <label className={labelClasses}>Target word count</label>
          <input
            type="number"
            min={150}
            max={5000}
            value={form.word_count}
            onChange={(e) => setForm({ ...form, word_count: Number(e.target.value) })}
            className={inputClasses}
          />
        </div>
      </div>

      <div>
        <label className={labelClasses}>Target keywords (comma-separated)</label>
        <input
          onChange={(e) =>
            setForm({ ...form, target_keywords: e.target.value.split(",").map((k) => k.trim()).filter(Boolean) })
          }
          placeholder="e.g. renewable energy, solar power"
          className={inputClasses}
        />
      </div>

      <div className="flex gap-6 text-sm text-ink pt-1">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={form.generate_image}
            onChange={(e) => setForm({ ...form, generate_image: e.target.checked })}
            className="accent-agent-image"
          />
          Generate image
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={form.generate_social_variants}
            onChange={(e) => setForm({ ...form, generate_social_variants: e.target.checked })}
            className="accent-agent-social"
          />
          Generate social variants
        </label>
      </div>

      {errorMsg && <p className="text-red-400 text-sm">{errorMsg}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="w-full bg-agent-writing hover:brightness-110 disabled:opacity-50 text-canvas font-medium text-sm px-5 py-3 rounded-xl transition"
      >
        {submitting ? "Starting the crew…" : "Start generation"}
      </button>
    </form>
  );
}
