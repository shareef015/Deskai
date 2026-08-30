# Scanner Support Catalogue

## Engineering sequence

DeskPilot treats printing and scanning functions of a multifunction device as
separate Windows pipelines. A working print queue does not prove that WIA,
TWAIN, the scanning application or the scan destination works.

1. Ask the employee to confirm power, display, feeder, cover and physical state.
2. Identify USB, network, WSD or multifunction topology.
3. Enumerate the Windows scanner and imaging driver.
4. Inspect Windows Image Acquisition (`stisvc`) and its dependencies.
5. Distinguish WIA from vendor-supplied TWAIN and verify application/driver
   architecture compatibility.
6. Test network address and approved scanning protocol where applicable.
7. Compare Windows Scan with the required business application.
8. Validate the selected source, format and approved destination.
9. Use an approved synthetic test sheet to perform a controlled scan.
10. Confirm the artifact exists and ask the employee to confirm its readability.

## Privacy and safety

- Employee documents are never used for diagnostic test scans.
- Routine diagnostics collect device, service, driver and artifact metadata,
  not scanned-document content.
- Test artifacts use an approved temporary location and retention policy.
- Restarting WIA requires a dependency and active-session assessment.
- WIA/TWAIN driver installation is privileged and limited to signed packages.
- DeskPilot does not download an arbitrary vendor driver selected by an LLM.
- Network ACL, destination permission, endpoint-security and firmware changes
  require the responsible administrator.
- Mechanical feeder, lamp and sensor problems are physically escalated.

## Resolution evidence

A detected scanner or running WIA service is insufficient. Resolution requires
a controlled scan from the affected application when possible, creation of the
expected artifact, and employee confirmation that the content is readable,
complete and correctly oriented.
