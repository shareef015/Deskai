# Synthetic network environment

The laboratory models three private subnets with deterministic DHCP leases, gateways, DNS, a credential-free PAC proxy, a secret-free IKEv2 VPN profile and certificate-authenticated corporate Wi-Fi. Every endpoint has an adapter state and separate link, gateway, DNS, proxy, VPN and target health signals.

Seven bounded fault types can alter one declared state path at a time. Each fault carries a fixed restoration value or restores from the baseline. The fixture contains no Wi-Fi keys, VPN secrets, private certificates, public routable addresses or customer network data. Reset clears injected faults and recreates the exact tenant-local healthy state.
