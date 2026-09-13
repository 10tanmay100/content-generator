import { NextRequest, NextResponse } from "next/server";
import { getJob } from "@/lib/api";

export async function GET(_req: NextRequest, { params }: { params: { id: string } }) {
  try {
    const job = await getJob(params.id);
    return NextResponse.json(job);
  } catch (err) {
    console.error("job status route error", err);
    return NextResponse.json({ error: "Failed to fetch job status" }, { status: 502 });
  }
}
