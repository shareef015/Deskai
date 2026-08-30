# Printer Support Catalogue

## Engineering sequence

DeskPilot follows the same progression an experienced Windows service-desk
engineer uses:

1. Ask the employee to confirm power, panel errors, paper, covers and physical
   connections.
2. Identify USB, direct network, IPP/WSD or print-server topology.
3. Inspect the Windows printer, queue and job metadata without reading document
   contents.
4. Inspect Print Spooler and PrintService evidence.
5. Validate the configured port against approved asset data, DNS and network
   reachability.
6. Check print-server and permission state for shared printers.
7. Validate signed driver, device-model and Windows Protected Print Mode
   compatibility.
8. Rank root causes before proposing a change.
9. Obtain action-specific approval, capture pre-state and execute a typed tool.
10. Submit a controlled test page and ask the employee to confirm physical
    output before resolving the incident.

## Safety rules

- Queue enumeration collects job metadata, not document content.
- A user's job is not cancelled without the job owner's or authorized
  engineer's approval.
- Clearing the spool directory can destroy pending work and is never automatic.
- Restarting the spooler requires a queue-impact assessment.
- Drivers must be approved and signed. Driver installation is privileged.
- Security policy is never disabled merely to make an incompatible printer
  work. Windows Protected Print Mode changes require the endpoint-security
  authority.
- Print-server, DNS, firewall, ACL and permission changes are escalated to the
  responsible administrator.
- Mechanical, electrical and consumable failures are physical-service cases.

## Resolution evidence

`Ready` status or an empty queue is not sufficient. A controlled test job must
leave the queue, reach the intended printer and produce physical output that
the employee confirms. Rendering and quality incidents additionally require
the employee to confirm the page is readable and correctly formatted.
