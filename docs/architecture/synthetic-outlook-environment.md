# Synthetic Microsoft 365 and Outlook environment

The laboratory defines a fictional Microsoft 365 tenant, ten reserved-domain mailboxes and one Outlook client state per endpoint. Classic Outlook and new Outlook retain separate process, profile, cache, search and add-in models. Authentication, connectivity, sync and service health are independent evidence surfaces.

Fixtures contain mailbox metadata only—never messages, credentials, access tokens or MFA secrets. Eight bounded failure modes target declared fields and include exact rollback values. Reset restores healthy tenant and client baselines and clears all injected faults.
