"""SSRF protections for user supplied scan targets."""
import asyncio
import ipaddress
from urllib.parse import urlparse

from fastapi import HTTPException

from ..core.config import settings


def _is_forbidden_ip(value: str) -> bool:
    ip = ipaddress.ip_address(value)
    return any((
        ip.is_private,
        ip.is_loopback,
        ip.is_link_local,
        ip.is_multicast,
        ip.is_reserved,
        ip.is_unspecified,
    ))


async def validate_scan_url(url: str) -> str:
    parsed = urlparse(str(url))
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
        raise HTTPException(status_code=400, detail='Only public http/https URLs can be scanned.')
    if parsed.username or parsed.password:
        raise HTTPException(status_code=400, detail='URLs containing credentials are not allowed.')
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    if port not in settings.SCAN_ALLOWED_PORTS:
        raise HTTPException(status_code=400, detail='That destination port is not allowed.')
    hostname = parsed.hostname.rstrip('.').lower()
    if hostname in {'localhost', 'localhost.localdomain'} or hostname.endswith('.local'):
        raise HTTPException(status_code=400, detail='Local/private hosts cannot be scanned.')
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(hostname, port, type=0)
    except OSError as exc:
        raise HTTPException(status_code=400, detail='The scan hostname could not be resolved.') from exc
    addresses = {info[4][0].split('%')[0] for info in infos if info and info[4]}
    if not addresses or any(_is_forbidden_ip(address) for address in addresses):
        raise HTTPException(status_code=400, detail='Local/private network destinations cannot be scanned.')
    return str(url)
