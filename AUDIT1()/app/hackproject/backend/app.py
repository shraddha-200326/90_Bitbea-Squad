from flask import Flask, request, jsonify
from urllib.parse import urljoin
import requests
import tldextract

from audit.utils import normalize_url
from audit.security import analyze_security
from audit.performance import analyze_performance
from config import REQUEST_TIMEOUT, MAX_ASSET_CHECKS, USER_AGENT

app = Flask(__name__)

@app.route("/api/health", methods=["GET"])
def health():
    return {"ok": True}

@app.route("/api/audit", methods=["POST"])
def audit():
    data = request.get_json(silent=True) or {}
    raw_url = data.get("url", "")
    if not raw_url:
        return jsonify({"error": "url is required"}), 400

    url = normalize_url(raw_url)
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True, headers=headers)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch {url}: {str(e)}"}), 502

    # robots.txt
    robots_url = urljoin(resp.url, "/robots.txt")
    robots_text = None
    try:
        r = requests.get(robots_url, timeout=REQUEST_TIMEOUT, headers=headers)
        if r.status_code == 200 and len(r.text) < 200_000:
            robots_text = r.text
    except Exception:
        pass

    security = analyze_security(resp, resp.url, robots_text)
    performance = analyze_performance(
        resp,
        resp.url,
        max_checks=MAX_ASSET_CHECKS,
        timeout=REQUEST_TIMEOUT,
        headers=headers
    )

    # overall
    overall = int(round((security["score"] * 0.55) + (performance["score"] * 0.45)))
    return jsonify({
        "input_url": raw_url,
        "final_url": resp.url,
        "status_code": resp.status_code,
        "overall": {
            "score": overall,
            "grade": "A+" if overall >= 95 else
                     "A"  if overall >= 85 else
                     "B"  if overall >= 75 else
                     "C"  if overall >= 65 else
                     "D"  if overall >= 55 else "F"
        },
        "security": security,
        "performance": performance
    })

if __name__ == "__main__":
    app.run(debug=True)

