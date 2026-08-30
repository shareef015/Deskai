import type { ApprovalRequest } from "../../schemas";

type Props = {
  approval: ApprovalRequest;
  onApprove: () => void;
  onReject: () => void;
  onRequestChanges: () => void;
};

export function ApprovalCard({ approval, onApprove, onReject, onRequestChanges }: Props) {
  return (
    <section aria-labelledby={`approval-${approval.id}`}>
      <h2 id={`approval-${approval.id}`}>Human approval required</h2>
      <dl>
        <dt>Action requested</dt><dd>{approval.action}</dd>
        <dt>Target machine</dt><dd>{approval.target}</dd>
        <dt>Reason</dt><dd>{approval.reason}</dd>
        <dt>Risk</dt><dd>{approval.risk}</dd>
        <dt>Rollback capability</dt><dd>{approval.rollbackAvailable ? "Available" : "Not available"}</dd>
      </dl>
      <div aria-label="Approval actions">
        <button type="button" onClick={onApprove}>Approve action</button>
        <button type="button" onClick={onReject}>Reject action</button>
        <button type="button" onClick={onRequestChanges}>Request changes</button>
      </div>
    </section>
  );
}
