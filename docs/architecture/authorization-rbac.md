# Enterprise authorization and RBAC

Authentication proves identity; it does not grant an action. The authorization
engine loads active PostgreSQL role assignments for the authenticated tenant,
matches their resource scope, applies explicit denies before allows and denies
when no allow matches. Roles presented in access tokens are hints only and are
never the authoritative assignment source.

Assignments are tenant-scoped, time-bounded, revocable and protected by forced
RLS. Tenant, department, location, device and incident scopes prevent a broad
role name from silently becoming global authority. Every material decision
records the policy version and exact assignments that matched.

Segregation-of-duties checks run independently of role permissions. A proposer
cannot be the sole approver, an incident requester cannot approve a medium/high
risk change, auditors cannot hold conflicting mutation authority in the same
scope, and AI identities can never receive human approval authority.
