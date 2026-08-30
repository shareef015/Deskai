from __future__ import annotations

from dataclasses import dataclass
import ipaddress
from typing import Callable, Iterable
from urllib.parse import urlsplit


class SsrfViolation(ValueError):
    pass


Resolver = Callable[[str], Iterable[str]]


def _public_ip(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    # Reject all non-global destinations: private, loopback, link-local, multicast, reserved, etc.
    return ip.is_global


@dataclass(frozen=True, slots=True)
class ValidatedTarget:
    url: str
    hostname: str
    port: int
    resolved_ips: tuple[str, ...]


class SsrfPolicy:
    """Validate outbound HTTPS targets before connecting and return addresses that adapters must pin."""

    def __init__(
        self,
        *,
        allowed_hosts: frozenset[str] | None = None,
        allowed_ports: frozenset[int] = frozenset({443}),
    ) -> None:
        self.allowed_hosts = allowed_hosts
        self.allowed_ports = allowed_ports

    def validate(self, url: str, resolver: Resolver) -> ValidatedTarget:
        parts = urlsplit(url)
        if parts.scheme.lower() != "https":
            raise SsrfViolation("https_required")
        if parts.username is not None or parts.password is not None:
            raise SsrfViolation("userinfo_forbidden")
        if not parts.hostname:
            raise SsrfViolation("hostname_required")
        hostname = parts.hostname.rstrip(".").lower()
        if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".localhost"):
            raise SsrfViolation("local_hostname_forbidden")
        if self.allowed_hosts is not None and hostname not in self.allowed_hosts:
            raise SsrfViolation("host_not_allowlisted")
        port = parts.port or 443
        if port not in self.allowed_ports:
            raise SsrfViolation("port_not_allowed")
        addresses = tuple(dict.fromkeys(resolver(hostname)))
        if not addresses:
            raise SsrfViolation("dns_no_addresses")
        if any(not _public_ip(address) for address in addresses):
            raise SsrfViolation("non_public_destination")
        return ValidatedTarget(url=url, hostname=hostname, port=port, resolved_ips=addresses)
