# Evaluation, Regression and Release Gates

Offline, online-shadow and synthetic suites are immutable evidence-bound runs identified by dataset and configuration fingerprints. Baselines must share tenant and mode with the candidate.

Grounding, safety, routing and tool-policy metrics are evaluated globally and by domain/scenario slices. Minimum thresholds and regression budgets produce warnings or release blockers according to governed metric criticality.

Blocked releases cannot be approved. A qualified release approver may approve only a review-eligible gate and only against the exact candidate run fingerprint. Recruiter demonstrations use synthetic evaluation records isolated from live evidence.
