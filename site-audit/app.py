from flask import Flask, render_template, request, redirect, url_for, flash, send_file, make_response
import requests, json, os, csv
from bs4 import BeautifulSoup
from datetime import datetime
from io import StringIO
import pdfkit

app = Flask(__name__)
app.secret_key = "your_secret_key"

# 🧠 Modular Audit Logic with Weighted Scoring
def run_audit(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # 🔐 Security Checks
    is_https = url.startswith("https://")
    headers = response.headers
    security_headers = {
        "Content-Security-Policy": headers.get("Content-Security-Policy"),
        "X-Frame-Options": headers.get("X-Frame-Options"),
        "Strict-Transport-Security": headers.get("Strict-Transport-Security"),
    }
    external_scripts = [s.get("src") for s in soup.find_all("script") if s.get("src")]
    insecure_scripts = [s for s in external_scripts if s and s.startswith("http://")]

    # ⚡ Performance Insights
    js_files = [s.get("src") for s in soup.find_all("script") if s.get("src")]
    css_files = [l.get("href") for l in soup.find_all("link", rel="stylesheet") if l.get("href")]
    lazy_images = soup.find_all("img", loading="lazy")
    minified_assets = [f for f in js_files + css_files if ".min." in f]
    page_size = len(response.content)

    # 📈 SEO Analysis
    title = soup.title.string if soup.title else None
    meta_desc = soup.find("meta", attrs={"name": "description"})
    meta_robots = soup.find("meta", attrs={"name": "robots"})
    headings = [tag.name for tag in soup.find_all(["h1", "h2", "h3"])]
    images = soup.find_all("img")
    images_missing_alt = [img for img in images if not img.get("alt")]
    canonical = soup.find("link", rel="canonical")

    # 🧮 Weighted Scoring
    weights = {
        "security": {
            "https": 2,
            "headers": 1
        },
        "performance": {
            "minified_assets": 2
        },
        "seo": {
            "title": 1,
            "meta_description": 1,
            "canonical": 1,
            "alt_tags": 2
        }
    }

    security_score = 0
    if is_https:
        security_score += weights["security"]["https"]
    security_score += sum(weights["security"]["headers"] for h in security_headers.values() if h)

    performance_score = weights["performance"]["minified_assets"] if len(minified_assets) > 0 else 0

    seo_score = 0
    seo_score += weights["seo"]["title"] if title else 0
    seo_score += weights["seo"]["meta_description"] if meta_desc else 0
    seo_score += weights["seo"]["canonical"] if canonical else 0
    seo_score += weights["seo"]["alt_tags"] if len(images_missing_alt) == 0 else 0

    total_score = security_score + performance_score + seo_score
    max_score = (
        weights["security"]["https"] +
        weights["security"]["headers"] * len(security_headers) +
        weights["performance"]["minified_assets"] +
        sum(weights["seo"].values())
    )

    return {
        "security": {
            "is_https": is_https,
            "headers": security_headers,
            "insecure_scripts": insecure_scripts,
            "score": security_score,
            "max": weights["security"]["https"] + weights["security"]["headers"] * len(security_headers)
        },
        "performance": {
            "js_files": js_files,
            "css_files": css_files,
            "lazy_images": len(lazy_images),
            "minified_assets": minified_assets,
            "page_size_bytes": page_size,
            "score": performance_score,
            "max": weights["performance"]["minified_assets"]
        },
        "seo": {
            "title": title,
            "meta_description": meta_desc["content"] if meta_desc else None,
            "meta_robots": meta_robots["content"] if meta_robots else None,
            "headings": headings,
            "images_missing_alt": len(images_missing_alt),
            "canonical": canonical["href"] if canonical else None,
            "score": seo_score,
            "max": sum(weights["seo"].values())
        },
        "score": f"{total_score}/{max_score}",
        "max_score": max_score
    }

# 🧾 Home page
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        url = request.form["url"]
        return redirect(url_for("audit", url=url))
    return render_template("audit.html")

# 🔍 Audit route
@app.route("/audit")
def audit():
    url = request.args.get("url")
    try:
        result = run_audit(url)

        # ✅ Save to history
        history_entry = {
            "url": url,
            "score": result["score"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "title": result["seo"]["title"]
        }

        history_path = "data/history.json"
        os.makedirs("data", exist_ok=True)

        if os.path.exists(history_path):
            with open(history_path, "r") as f:
                history = json.load(f)
        else:
            history = []

        history.insert(0, history_entry)

        with open(history_path, "w") as f:
            json.dump(history, f, indent=2)

        # ✅ Save latest report
        report_path = "data/latest_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"Audit Report for {url}\n\n")
            for section, details in result.items():
                f.write(f"{section.upper()}:\n")
                if isinstance(details, dict):
                    for k, v in details.items():
                        f.write(f"  {k}: {v}\n")
                else:
                    f.write(f"{details}\n")
                f.write("\n")

        return render_template("report.html", url=url, result=result)

    except Exception as e:
        flash(f"Error auditing URL: {e}")
        return redirect(url_for("home"))

# 📂 History route
@app.route("/history")
def history():
    history_path = "data/history.json"
    if os.path.exists(history_path):
        with open(history_path, "r") as f:
            history = json.load(f)
    else:
        history = []

    return render_template("history.html", history=history)

# 📥 TXT Download route
@app.route("/download")
def download_report():
    report_path = "data/latest_report.txt"
    if os.path.exists(report_path):
        return send_file(report_path, as_attachment=True)
    else:
        flash("Report file not found.")
        return redirect(url_for("home"))

# 🧾 PDF Download route
@app.route("/download/pdf")
def download_pdf():
    url = request.args.get("url")
    result = run_audit(url)

    rendered = render_template("report.html", url=url, result=result)

    config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")
    pdf = pdfkit.from_string(rendered, False, configuration=config)

    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return response

@app.route("/download/csv")
def download_csv():
    url = request.args.get("url")
    result = run_audit(url)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Section", "Metric", "Value"])

    # Security
    writer.writerow(["Security", "HTTPS", "Yes" if result["security"]["is_https"] else "No"])
    for header, value in result["security"]["headers"].items():
        writer.writerow(["Security", header, "Present" if value else "Missing"])
    for script in result["security"]["insecure_scripts"]:
        writer.writerow(["Security", "Insecure Script", script])
    writer.writerow(["Security", "Score", result["security"]["score"]])
    writer.writerow(["Security", "Max Score", result["security"]["max"]])

    # Performance
    writer.writerow(["Performance", "JS Files", len(result["performance"]["js_files"])])
    writer.writerow(["Performance", "CSS Files", len(result["performance"]["css_files"])])
    writer.writerow(["Performance", "Lazy-loaded Images", result["performance"]["lazy_images"]])
    writer.writerow(["Performance", "Minified Assets", len(result["performance"]["minified_assets"])])
    writer.writerow(["Performance", "Page Size (bytes)", result["performance"]["page_size_bytes"]])
    writer.writerow(["Performance", "Score", result["performance"]["score"]])
    writer.writerow(["Performance", "Max Score", result["performance"]["max"]])

    # SEO
    writer.writerow(["SEO", "Title", result["seo"]["title"] or ""])
    writer.writerow(["SEO", "Meta Description", result["seo"]["meta_description"] or ""])
    writer.writerow(["SEO", "Meta Robots", result["seo"]["meta_robots"] or ""])
    writer.writerow(["SEO", "Canonical URL", result["seo"]["canonical"] or ""])
    writer.writerow(["SEO", "Images Missing Alt", result["seo"]["images_missing_alt"]])
    writer.writerow(["SEO", "Score", result["seo"]["score"]])
    writer.writerow(["SEO", "Max Score", result["seo"]["max"]])

    # Overall
    writer.writerow(["Overall", "Total Score", result["score"]])
    writer.writerow(["Overall", "Max Score", result["max_score"]])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response.headers["Content-Type"] = "text/csv"
    return response

if __name__ == "__main__":
    app.run(debug=True)
