import { AiExecutionSnapshotSchema } from "../../src/contracts/ai-execution.contract";

describe("AI execution contract", () => {
  it("rejects cross-tenant citations and event context", () => {
    const result = AiExecutionSnapshotSchema.safeParse({
      runId: "run-1",
      tenantId: "tenant-a",
      incidentId: "incident-1",
      state: "closed",
      citations: [{ documentId: "d", chunkId: "c", tenantId: "tenant-b", contentHash: "a".repeat(64) }],
      events: [{ sequence: 1, state: "closed", eventType: "incident_closed", tenantId: "tenant-b", runId: "run-1", details: {} }]
    });
    expect(result.success).toBe(false);
  });

  it("accepts an ordered tenant-bound snapshot", () => {
    expect(AiExecutionSnapshotSchema.safeParse({
      runId: "run-1",
      tenantId: "tenant-a",
      incidentId: "incident-1",
      state: "closed",
      citations: [{ documentId: "d", chunkId: "c", tenantId: "tenant-a", contentHash: "a".repeat(64) }],
      events: [
        { sequence: 1, state: "intake", eventType: "incident_accepted", tenantId: "tenant-a", runId: "run-1", details: {} },
        { sequence: 2, state: "closed", eventType: "incident_closed", tenantId: "tenant-a", runId: "run-1", details: {} }
      ]
    }).success).toBe(true);
  });
});
