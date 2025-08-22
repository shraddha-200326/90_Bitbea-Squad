import re
import socket
import ssl
import time
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
from typing import List, Optional


def normalize_url(url: str) -> str:
    url = url.strip()
    if not re.match(r"^https?://", url, flags=re.I):
        url = "https://" + url  # prefer https by default
    return url


def fetch(url: str, *, timeout: int = 10, allow_redirects: bool = True, headers: dict = None):
    start = time.perf_counter()
    resp = requests.get(url, timeout=timeout, allow_redirects=allow_redirects, headers=headers)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return resp, elapsed_ms


def head_size(url: str, *, timeout: int = 10, headers: dict = None) -> int:
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True, headers=headers)
        if r.status_code >= 400 or "content-length" not in r.headers:
            r2 = requests.get(url, timeout=timeout, allow_redirects=True, headers=headers)
            return int(r2.headers.get("content-length") or 0)
        return int(r.headers.get("content-length") or 0)
    except Exception:
        return 0


def get_domain(url: str) -> str:
    return urlparse(url).netloc


def get_scheme(url: str) -> str:
    return urlparse(url).scheme


def parse_assets(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    assets = set()

    for tag, attr in [("img", "src"), ("script", "src"), ("link", "href")]:
        for el in soup.find_all(tag):
            href = el.get(attr)
            if href:
                abs_url = urljoin(base_url, href)
                assets.add(abs_url)

    return list(assets)


def has_mixed_content(base_url: str, assets: List[str]) -> bool:
    if get_scheme(base_url) != "https":
        return False
    return any(a.lower().startswith("http://") for a in assets)


def days_until_cert_expiry(hostname: str, port: int = 443) -> Optional[int]:
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=8) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                not_after = cert.get("notAfter")
                if not_after:
                    from datetime import datetime
                    expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                    return (expires - datetime.utcnow()).days
    except Exception:
        return None
    return None


def grade(score: int) -> str:
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 50:
        return "D"
    else:
        return "F"
