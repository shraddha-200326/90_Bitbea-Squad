const express = require("express");
const cors = require("cors");
const lighthouse = require("lighthouse");
const chromeLauncher = require("chrome-launcher");
const sslChecker = require("ssl-checker");

const app = express();
app.use(cors());
app.use(express.json());

// Performance + SEO Audit (using Lighthouse)
async function runLighthouse(url) {
    const chrome = await chromeLauncher.launch({ chromeFlags: ["--headless"] });
    const options = { logLevel: "info", output: "json", port: chrome.port };
    const runnerResult = await lighthouse(url, options);
    await chrome.kill();
    return runnerResult.lhr.categories; // Returns performance, SEO, etc.
}

// API endpoint
app.post("/audit", async (req, res) => {
    const { url } = req.body;
    try {
        const auditResults = await runLighthouse(url);
        const sslResults = await sslChecker(url.replace("https://","").replace("http://",""));

        res.json({
            performance: auditResults.performance.score * 100,
            seo: auditResults.seo.score * 100,
            ssl: sslResults,
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.listen(5000, () => console.log("Server running on port 5000"));