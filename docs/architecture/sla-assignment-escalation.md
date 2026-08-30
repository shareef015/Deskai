# SLA, assignment and escalation

Priority selects a versioned acknowledgement, resolution and unowned-work target.
P1 uses continuous time; lower priorities use each tenant's IANA timezone,
working windows and versioned holiday calendar. Daylight-saving behavior comes
from the platform zone database.

Assignment history preserves queue, engineer, assigning human, reason and time
window. A partial unique index permits one active owner per incident. Queue
selection is deterministic across category, location, skills and support hours;
AI may recommend but cannot assign.

Only the resolution clock can pause, and only for allowlisted reasons with an
authorized human/policy decision and expected resume time. At 80% utilization
the current owner and queue lead receive a warning; 100% records a breach.
Unowned incidents escalate earlier by priority. Escalations are deduplicated,
immutable and never close or remediate an incident.
