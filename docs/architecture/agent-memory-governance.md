# Agent Memory Governance and Privacy-Safe Persistence

Working memory is restricted to one active tenant, subject, incident, thread journey, and a one-day maximum TTL. Episodic memory supports explicit support continuity for up to 30 days only with granted consent. Reusable knowledge is de-identified, human-curated content with a maximum one-year TTL; model summaries cannot promote themselves.

Each record stores fingerprints and provenance rather than raw conversation or endpoint content. Purpose, sensitivity, encryption, consent, creation, expiry, and status are explicit. Sensitive records require encryption. Recall independently rechecks tenant, subject, purpose, class, incident where applicable, consent, status, and expiry.

Working memory cannot cross incidents, and no class may cross tenants or subjects. Conflicting durable memories stop for human resolution rather than silent merging. Revocation, expiry, and authorized deletion remove recall eligibility while retaining a non-content tombstone for accountability. Hidden memory and background personalization are prohibited.
