# Incident Intake and Structured Extraction

The intake extractor converts an employee description into a strict incident record: a concise summary, observable symptoms, business impact, registered affected device, timeline, scored domain candidates with source spans, explicit uncertainty, clarification needs, and bounded evidence references.

Employee text is data, never executable instruction. Secret-like values are redacted before hashing, and the raw message is not copied into durable structured state. Every domain assertion points to a valid span in the sanitized source. Device identifiers must already belong to the employee or tenant inventory.

The extractor has no tools and cannot diagnose root cause, infer consent, authorize actions, or invent missing values. Unknown impact or device information must be represented explicitly. Complete output advances to classification; uncertainty advances to bounded clarification; schema, scope, span, or digest failures are rejected.
