"""Fail-closed public URL validation for AURA's read-only live crawl."""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse, urlunparse


def validate_public_url(value: str) -> str:
    """Return a normalized public HTTP(S) URL or raise ValueError.

    DNS is resolved before every request (including redirects); any non-global
    address fails closed so the crawler cannot reach loopback, private, link
    local, or cloud-metadata networks.
    """
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("live targets must be absolute public http(s) URLs")
    if parsed.username or parsed.password:
        raise ValueError("credentials in audit URLs are not allowed")
    host = parsed.hostname.rstrip(".").lower()
    if host == "localhost" or host.endswith(".localhost"):
        raise ValueError("localhost is not a public audit target")
    try:
        addresses = [item[4][0] for item in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)]
    except socket.gaierror as exc:
        raise ValueError(f"could not resolve public hostname: {host}") from exc
    if not addresses:
        raise ValueError("hostname did not resolve to a public address")
    for address in addresses:
        try:
            if not ipaddress.ip_address(address).is_global:
                raise ValueError("audit target resolves to a non-public address")
        except ValueError as exc:
            if str(exc) == "audit target resolves to a non-public address":
                raise
            raise ValueError("hostname returned an invalid IP address") from exc
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path or "/", "", parsed.query, ""))
