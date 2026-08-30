# Synthetic Windows endpoints

The demo laboratory contains exactly ten deterministic x64 endpoints: five Windows 10 22H2 profiles and five Windows 11 profiles. Each carries fictional hardware, installed software, security posture, assigned employee, location, baseline health and a primary demonstration scenario.

Windows lifecycle policy is explicit. Windows 10 profiles with verified synthetic ESU remain active; the non-ESU profile is restricted and exposes a migration warning. Serial numbers are never stored—only deterministic SHA-256 fingerprints. Reset reconstructs the exact tenant-local initial state and never incorporates real endpoint telemetry.
