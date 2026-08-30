# Windows and Network Support Catalogue

## Scope

This catalogue supports Outlook, printer, scanner and endpoint-agent incidents.
It is not a general-purpose network administration agent. DeskPilot diagnoses
the affected Windows endpoint and escalates changes owned by network, identity,
security or endpoint-management administrators.

## Diagnostic sequence

1. Establish the affected application, location, connection type, impact and
   last-known-good time.
2. Confirm the Windows build, lifecycle and recent update state.
3. Inspect adapter, driver, link and device-problem status.
4. Inspect IP, DHCP, gateway and route state.
5. Compare approved hostname resolution with direct target connectivity.
6. Inspect proxy, PAC, VPN and managed-policy provenance.
7. Test only the target host and protocol required by the incident.
8. Correlate bounded Event Log windows and system resource state.
9. Propose the smallest reversible action and request authorization.
10. Verify the original Outlook, printing or scanning business function and ask
    the employee to confirm.

## Safety rules

- No Wi-Fi key, VPN secret or certificate private key is collected.
- The firewall and endpoint security are never disabled for diagnosis.
- Full Windows network reset is not automatic; it can remove/reinstall adapters
  and requires a restart and high-risk approval.
- Persistent route, DNS, proxy, VPN, firewall and enterprise-policy changes are
  administrator-owned.
- Packet capture is exception-only, purpose-limited, approved and redacted.
- Only allowlisted Windows services tied to the active incident may be
  restarted after impact assessment.
- Logs are collected for bounded time windows rather than bulk-exported.

## Verification

Network indicators alone are insufficient. A successful ping, DNS lookup or
open TCP port does not resolve the incident. DeskPilot must recheck the original
business function—Outlook connectivity, printer output, scanner acquisition or
endpoint-agent communication—and obtain employee confirmation.
