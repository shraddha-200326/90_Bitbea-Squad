from urllib.parse import urlparse, urljoin
import requests
from .utils import days_until_cert_expiry, get_domain, get_scheme

SEC_HEADERS = [
    "content-security-policy",
    "strict-transport-security",
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "permissions-policy",
]

def analyze_security(resp, base_url: str, robots_text: str | None):
    headers = {k.lower(): v for k, v in resp.headers.items()}
    findings = []
    score = 100

    # HTTPS + redirect
    scheme = get_scheme(resp.url)
    if scheme != "https":
        score -= 15
        findings.append({"type": "warning", "msg": "Site not served over HTTPS."})

    # TLS expiry days
    days = days_until_cert_expiry(get_domain(base_url))
    if days is None:
        score -= 5
        findings.append({"type": "info", "msg": "Could not determine TLS certificate expiry."})
    else:
        if days < 0:
            score -= 30
            findings.append({"type": "error", "msg": "TLS certificate expired."})
        elif days < 15:
            score -= 15
            findings.append({"type": "warning", "msg": f"TLS certificate expires soon ({days} days)."})
        else:
            findings.append({"type": "pass", "msg": f"TLS certificate valid ({days} days remaining)."})

    # Security headers
    missing = []
    good = []
    for h in SEC_HEADERS:
        if h in headers:
            good.append(h)
        else:
            missing.append(h)

    if missing:
        score -= min(30, 5 * len(missing))
        findings.append({"type": "warning", "msg": f"Missing security headers: {', '.join(missing)}"})
    if good:
        findings.append({"type": "pass", "msg": f"Present security headers: {', '.join(good)}"})

    # Server info leakage
    if "server" in headers:
        findings.append({"type": "info", "msg": f"Server header exposes: {headers['server']}. Consider minimizing version leakage."})

    # X-Powered-By leakage
    if "x-powered-by" in headers:
        score -= 5
        findings.append({"type": "warning", "msg": f"X-Powered-By present: {headers['x-powered-by']}. Remove to reduce fingerprinting."})

    # robots.txt sanity (optional)
    if robots_text is not None:
        if "disallow: /" in robots_text.lower():
            findings.append({"type": "info", "msg": "robots.txt blocks all crawling. Is this intentional?"})

    score = max(0, min(100, score))
    return {
        "score": score,
        "grade": "A+" if score >= 95 else
                 "A" if score >= 85 else
                 "B" if score >= 75 else
                 "C" if score >= 65 else
                 "D" if score >= 55 else "F",
        "findings": findings
    }
