/**
 * Client for the FastAPI backend. Server-side calls (route handlers, server
 * components) can use BACKEND_API_TOKEN directly; the browser never sees it.
 */
export interface ContentGenerationRequest {
  topic: string;
  content_format: "blog" | "social" | "email" | "newsletter";
  tone: string;
  target_audience: string;
  target_keywords: string[];
  word_count: number;
  generate_image: boolean;
  generate_social_variants: boolean;
  tenant_id?: string;
}

export interface JobRecord {
  id: string;
  status: string;
  topic: string;
  result?: {
    title: string;
    body_markdown: string;
    meta_description?: string;
    seo_keywords: string[];
    seo_score?: number;
    image_prompt?: string;
    image_url?: string;
    alt_text?: string;
    social_variants: Record<string, string>;
    hashtags: string[];
    sources: string[];
  };
  error?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

function authHeaders(): HeadersInit {
  const token = process.env.BACKEND_API_TOKEN ?? "";
  return { "Content-Type": "application/json", Authorization: `Bearer ${token}` };
}

export async function startGeneration(payload: ContentGenerationRequest): Promise<{ job_id: string }> {
  const res = await fetch(`${API_BASE}/content/generate`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(payload),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to start generation: ${res.status}`);
  return res.json();
}

export async function getJob(jobId: string): Promise<JobRecord> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}`, {
    headers: authHeaders(),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to fetch job: ${res.status}`);
  return res.json();
}