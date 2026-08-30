import { NextResponse } from "next/server";

export async function GET(): Promise<NextResponse> {
  const now = new Date().toISOString();
  return NextResponse.json({
    id: "11111111-1111-4111-8111-111111111111",
    tenantId: "22222222-2222-4222-8222-222222222222",
    title: "Synthetic printer queue unavailable",
    description: "Deterministic incident used for frontend failure-recovery verification.",
    status: "diagnosing",
    severity: "medium",
    createdAt: now,
    updatedAt: now,
  }, {
    headers: { "x-request-id": "demo-request-0001" },
  });
}
