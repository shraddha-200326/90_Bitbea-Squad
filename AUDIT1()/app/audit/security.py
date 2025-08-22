import requests
import socket
import ssl
from urllib.parse import urlparse

def check_https(url):
    return url.startswith("https://")

def get_security_headers(url):
    try:
        response = requests.get(url, timeout=10)
        headers = response.headers
        required_headers = [
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Referrer-Policy"
        ]
        return {h: headers.get(h, "Missing") for h in required_headers}
    except Exception as e:
        return {"error": str(e)}

def ssl_certificate_check(domain):
    context = ssl.create_default_context()
    try:
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                return {
                    "issuer": dict(x[0] for x in cert['issuer']),
                    "subject": dict(x[0] for x in cert['subject']),
                    "valid_from": cert['notBefore'],
                    "valid_to": cert['notAfter'],
                }
    except Exception as e:
        return {"ssl_error": str(e)}

def port_scan(domain):
    open_ports = []
    for port in [21, 22, 80, 443, 8080, 8443]:
        try:
            with socket.create_connection((domain, port), timeout=2):
                open_ports.append(port)
        except:
            continue
    return open_ports

def analyze_security(url):
    parsed = urlparse(url)
    domain = parsed.hostname
    return {
        "https": check_https(url),
        "security_headers": get_security_headers(url),
        "ssl_certificate": ssl_certificate_check(domain),
        "open_ports": port_scan(domain)
    }
