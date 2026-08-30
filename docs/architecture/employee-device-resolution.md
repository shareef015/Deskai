# Employee and Device Resolution

Device resolution uses the authenticated tenant and employee scope plus authoritative, active asset relationships. Only registered Windows 10 and Windows 11 devices are eligible. Cross-tenant records fail closed; inactive, unregistered, unsupported, or unrelated devices are discarded.

An explicitly reported eligible device receives the strongest match. Otherwise primary, assigned, shared, and recent-status signals produce deterministic scores. A device is proposed automatically only when both confidence and margin thresholds pass. Ambiguous results disclose at most three safe labels and operating-system families—never serial numbers or sensitive inventory.

The employee must confirm a scope-bound selection token before the device identifier enters graph state and before diagnostic consent can be requested. Device confirmation is not diagnostic consent and not remediation approval. Decline, ambiguity, invalid tokens, missing relationships, and cross-scope data cannot initiate endpoint access.
