# Synthetic print and scan environment

The lab models six printers, three scanners and two print servers across the three fictional sites. It preserves queue and job metadata, signed driver versions, TCP/IP ports, print-server reachability, explicit permissions, endpoint mappings, separate MFP print/scan functions, and distinct WIA and TWAIN state.

Ten bounded failure modes carry exact rollback values. Test printing requires employee confirmation of physical output. Test scanning uses only the approved synthetic sheet, never inspects content, and retains its artifact temporarily. Reset restores ready devices, clears queues and locks, and affects only the synthetic tenant.
