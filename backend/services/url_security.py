"""URL validation and network-boundary controls for untrusted scan targets."""
import asyncio
import ipaddress
import socket
from typing import Iterable
from urllib.parse import urlparse

from ..core.config import settings


class UnsafeScanTarget(ValueError):
    """Raised when a requested scan target is unsafe to access from the server."""


def _is_public_ip(value: str) -> bool:
    ip = ipaddress.ip_address(value)
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


async def _resolve(hostname: str, port: int) -> Iterable[str]:
    def lookup():
        return socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)

    try:
        results = await asyncio.to_thread(lookup)
    except socket.gaierror as exc:
        raise UnsafeScanTarget("Target hostname could not be resolved") from exc
    return {item[4][0] for item in results}


async def validate_scan_url(url: str) -> None:
    """Require an HTTP(S) URL that resolves exclusively to public addresses."""
    parsed = urlparse(str(url))
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeScanTarget("Only http and https scan targets are allowed")
    if not parsed.hostname:
        raise UnsafeScanTarget("Scan target must include a hostname")
    if parsed.username or parsed.password:
        raise UnsafeScanTarget("Credentials in scan target URLs are not allowed")

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if settings.SCAN_ALLOWED_PORTS and port not in settings.SCAN_ALLOWED_PORTS:
        raise UnsafeScanTarget(f"Port {port} is not allowed for scan targets")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".local"):
        raise UnsafeScanTarget("Local network targets are not allowed")

    try:
        literal_ip = ipaddress.ip_address(hostname)
    except ValueError:
        literal_ip = None

    if literal_ip is not None:
        if not _is_public_ip(str(literal_ip)):
            raise UnsafeScanTarget("Private, loopback, link-local, and reserved addresses are not allowed")
        return

    addresses = await _resolve(hostname, port)
    if not addresses or any(not _is_public_ip(address) for address in addresses):
        raise UnsafeScanTarget("Target resolves to a non-public network address")
