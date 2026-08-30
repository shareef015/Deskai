# Digital twin and deterministic replay

The digital twin binds organization, workforce, identities, endpoints, inventory, network, Outlook, printing and scanning into one content-addressed baseline. Every component has a SHA-256 digest and must resolve to the same synthetic tenant and endpoint set.

State changes use allowlisted domain paths and optimistic versions. Each action records its previous value and resulting digest, enabling exact rollback. Snapshots are content-addressed, replay is bounded to 100 actions, and the same seed plus action sequence yields the same final hash. Reset clears the journal, advances the generation and restores the exact synthetic baseline; production data cannot be loaded.
