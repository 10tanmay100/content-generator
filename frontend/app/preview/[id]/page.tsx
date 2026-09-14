"use client";

import { useEffect, useState } from "react";
import CrewLoadingScreen from "@/components/CrewLoadingScreen";
import ContentPreview from "@/components/ContentPreview";
import type { JobRecord } from "@/lib/api";

export default function PreviewPage({ params }: { params: { id: string } }) {
  const [job, setJob] = useState<JobRecord | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let interval: ReturnType<typeof setInterval>;

    async function poll() {
      try {
        const res = await fetch(`/api/jobs/${params.id}`, { cache: "no-store" });
        if (!res.ok) throw new Error("Failed to fetch job");
        const data: JobRecord = await res.json();
        if (cancelled) return;
        setJob(data);
        if (data.status === "completed" || data.status === "failed") {
          clearInterval(interval);
        }
      } catch (err) {
        if (!cancelled) setErrorMsg(err instanceof Error ? err.message : "Error polling job");
      }
    }

    poll();
    interval = setInterval(poll, 4000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [params.id]);

  const isInProgress = !job || (job.status !== "completed" && job.status !== "failed");

  return (
    <div className="max-w-3xl mx-auto px-6 py-16 space-y-6">
      {isInProgress && <CrewLoadingScreen status={job?.status ?? "pending"} />}

      <div>
        <h1 className="font-display text-2xl font-semibold text-ink mb-1">
          {job?.topic ?? "Starting the crew…"}
        </h1>
        <p className="text-muted text-sm mb-5">Job {params.id}</p>
      </div>

      {errorMsg && <p className="text-red-400 text-sm">{errorMsg}</p>}
      {job?.status === "failed" && (
        <p className="text-red-400 text-sm">Generation failed: {job.error}</p>
      )}
      {job?.status === "completed" && <ContentPreview job={job} />}
    </div>
  );
}
