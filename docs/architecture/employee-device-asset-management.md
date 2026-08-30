# Employee, device and asset management

Human identity is anchored to the customer's OIDC subject; endpoint identity is
anchored to signed agent enrollment. Asset records represent Windows endpoints,
printers, scanners and print servers without storing raw hardware serials.
Serial numbers are normalized and retained only as SHA-256 fingerprints.

Assignments are temporal records rather than overwritten owner fields. A device
can have one open primary assignment plus explicit shared or temporary access.
Every relationship stays within one tenant, records the assigning human and is
protected by forced RLS. Employees cannot self-assign equipment.

Endpoint lifecycle transitions are explicit, version-checked and terminal after
retirement. Unsupported Windows builds move to restricted operation;
quarantining or retirement blocks endpoint commands independently of AI output.
Inventory exports and all ownership changes create immutable audit events.
