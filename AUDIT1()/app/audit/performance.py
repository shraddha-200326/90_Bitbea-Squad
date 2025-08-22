import subprocess
import json
import os

def analyze_performance(url):
    report_path = "./reports/lighthouse_report.json"

    try:
        command = [
            "lighthouse", url,
            "--quiet",
            "--chrome-flags=--headless",
            "--output=json",
            f"--output-path={report_path}"
        ]
        subprocess.run(" ".join(command), shell=True, check=True)

        with open(report_path, "r") as f:
            report = json.load(f)

        return {
            "performance_score": report["categories"]["performance"]["score"] * 100,
            "accessibility_score": report["categories"]["accessibility"]["score"] * 100,
            "best_practices_score": report["categories"]["best-practices"]["score"] * 100,
            "seo_score": report["categories"]["seo"]["score"] * 100
        }

    except Exception as e:
        return {"lighthouse_error": str(e)}
