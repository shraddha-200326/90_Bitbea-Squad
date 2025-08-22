from concurrent.futures import ThreadPoolExecutor, as_completed
from .utils import parse_assets, head_size, has_mixed_content, grade
from urllib.parse import urlparse

def analyze_performance(resp, base_url: str, max_checks=40, timeout=10, headers=None):
    score = 100
    findings = []

    # TTFB & compression
    ttfb_ms = resp.elapsed.microseconds // 1000
    if ttfb_ms > 800:
        score -= 10
        findings.append({"type": "warning", "msg": f"High TTFB: ~{ttfb_ms} ms. Consider a CDN or caching."})
    else:
        findings.append({"type": "pass", "msg": f"TTFB looks OK (~{ttfb_ms} ms)."})

    if "content-encoding" not in {k.lower() for k in resp.headers}:
        score -= 8
        findings.append({"type": "warning", "msg": "Response not compressed (gzip/br). Enable compression."})
    else:
        findings.append({"type": "pass", "msg": "Compression detected."})

    # Asset discovery
    html = resp.text or ""
    assets = parse_assets(html, base_url)
    total_assets = len(assets)
    if total_assets == 0:
        findings.append({"type": "info", "msg": "No assets referenced (or could not parse)."})
    else:
        findings.append({"type": "info", "msg": f"Found {total_assets} assets (img/script/css). Checking up to {max_checks}."})

    # Asset sizes (HEAD/GET with content-length)
    checked = assets[:max_checks]
    total_bytes = 0

    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(head_size, u, timeout=timeout, headers=headers): u for u in checked}
        for fut in as_completed(futs):
            total_bytes += fut.result() or 0

    kb = total_bytes // 1024
    if kb > 1500:
        score -= 15
        findings.append({"type": "warning", "msg": f"Large total payload (~{kb} KB for first {len(checked)} assets). Consider minification, code splitting, and image optimization."})
    else:
        findings.append({"type": "pass", "msg": f"Total payload looks reasonable (~{kb} KB for checked assets)."})

    # Mixed content
    if has_mixed_content(base_url, assets):
        score -= 12
        findings.append({"type": "error", "msg": "Mixed content detected (HTTP assets on HTTPS page). Use HTTPS for all resources."})

    # Caching hints
    cache_hdrs = {k.lower(): v for k, v in resp.headers.items()}
    cc = cache_hdrs.get("cache-control", "")
    if "max-age" not in cc.lower():
        score -= 6
        findings.append({"type": "warning", "msg": "No cache-control max-age on base document. Add caching where appropriate."})
    else:
        findings.append({"type": "pass", "msg": "Cache-Control present on base document."})

    score = max(0, min(100, score))
    return {
        "score": score,
        "grade": grade(score),
        "overview": {
            "assets_checked": len(checked),
            "assets_found": total_assets,
            "approx_kb": kb,
            "ttfb_ms": ttfb_ms
        },
        "findings": findings
    }
