# Synthetic environment control panel

The operator panel is a non-production surface for authenticated tenant administrators. It lists predefined scenarios, displays the current generation, version and state digest, captures a snapshot before activation, and exposes version-checked rollback and reset. Operators cannot submit arbitrary state paths or values.

The server binds every session to the configured synthetic tenant. AI identities cannot operate the panel. Every mutation is journaled, reset requires the exact confirmation phrase, snapshot storage and active faults are bounded, and the interface uses accessible forms rather than browser prompts or alerts.
