import { render } from "@testing-library/react";
import { axe } from "jest-axe";
import { ApprovalCard } from "../../src/components/ui/ApprovalCard";

it("approval card has no obvious accessibility violations", async () => {
  const { container } = render(
    <ApprovalCard
      approval={{
        id: "00000000-0000-4000-8000-000000000001",
        incidentId: "00000000-0000-4000-8000-000000000002",
        action: "Restart Print Spooler",
        target: "DESKTOP-034",
        reason: "Queue is blocked",
        risk: "low",
        rollbackAvailable: true,
        status: "pending",
        expiresAt: "2026-08-27T14:00:00.000Z"
      }}
      onApprove={() => undefined}
      onReject={() => undefined}
      onRequestChanges={() => undefined}
    />
  );
  expect(await axe(container)).toHaveNoViolations();
});
