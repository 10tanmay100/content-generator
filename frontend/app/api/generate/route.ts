import { NextRequest, NextResponse } from "next/server";
import { startGeneration } from "@/lib/api";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const result = await startGeneration(body);
    return NextResponse.json(result, { status: 202 });
  } catch (err) {
    console.error("generate route error", err);
    return NextResponse.json({ error: "Failed to start content generation" }, { status: 502 });
  }
}
