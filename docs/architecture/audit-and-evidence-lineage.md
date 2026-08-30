# Immutable audit and evidence lineage

Material security, authorization, consent, diagnostic, remediation and closure
events enter PostgreSQL only through a controlled append function. It allocates
a tenant-local monotonic sequence under an advisory lock and hashes each record
with the previous event hash. The application runtime cannot directly insert,
update or delete audit rows, and database triggers reject mutations.

Evidence records preserve source type/reference, content digest, collector and
tool versions, classification, retention deadline and legal-hold state. Derived
evidence adds immutable parent-to-child transformation edges with composite
tenant foreign keys. Large payloads remain in governed object storage.

Hash chains make tampering detectable; they do not replace signed exports,
backups, access control or an external immutable archive. Retention deletion is
performed only by a governed worker, never when legal hold applies, and the
deletion decision itself is audited before payload removal.
