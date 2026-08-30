# Synthetic device inventory

Each laboratory endpoint has a deterministic inventory of installed applications, Windows services, signed drivers, printers, scanners and dependency relationships. Application and driver versions are explicit. Services preserve startup mode plus separate expected and observed state, allowing later scenarios to inject failures without mutating the baseline definition.

The inventory is synthetic, tenant-scoped and read-only. It contains no license keys, secrets, real serial numbers or collected customer telemetry. Reset reconstructs the exact healthy baseline before a scenario applies its bounded state changes.
