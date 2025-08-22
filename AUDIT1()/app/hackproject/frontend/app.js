const form = document.getElementById("audit-form");
const urlInput = document.getElementById("url-input");
const btn = document.getElementById("audit-btn");
const loading = document.getElementById("loading");
const errorBox = document.getElementById("error");
const summary = document.getElementById("summary");

const setBadge = (el, grade) => {
  el.textContent = grade;
  el.className = "badge";
};

const li = (f) => {
  const el = document.createElement("li");
  el.className = f.type;
  el.textContent = f.msg;
  return el;
};

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorBox.hidden = true;
  summary.hidden = true;
  loading.hidden = false;
  btn.disabled = true;

  try {
    const res = await fetch("http://127.0.0.1:5000/api/audit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: urlInput.value.trim() }),
    });

    if (!res.ok) {
      const t = await res.json().catch(() => ({}));
      throw new Error(t.error || `Request failed (${res.status})`);
    }

    const data = await res.json();

    // Overall
    document.getElementById("overall-score").textContent = data.overall.score;
    setBadge(document.getElementById("overall-grade"), data.overall.grade);
    document.getElementById("final-url").textContent = data.final_url;
    document.getElementById("status-code").textContent = data.status_code;

    // Security
    document.getElementById("sec-score").textContent = data.security.score;
    setBadge(document.getElementById("sec-grade"), data.security.grade);
    const sf = document.getElementById("sec-findings");
    sf.innerHTML = "";
    data.security.findings.forEach(f => sf.appendChild(li(f)));

    // Performance
    document.getElementById("perf-score").textContent = data.performance.score;
    setBadge(document.getElementById("perf-grade"), data.performance.grade);
    const po = data.performance.overview;
    document.getElementById("perf-overview").textContent =
      `Assets checked: ${po.assets_checked} of ${data.performance.overview.assets_found} • Payload ~${po.approx_kb} KB • TTFB ~${po.ttfb_ms} ms`;
    const pf = document.getElementById("perf-findings");
    pf.innerHTML = "";
    data.performance.findings.forEach(f => pf.appendChild(li(f)));

    summary.hidden = false;
  } catch (err) {
    errorBox.textContent = err.message || String(err);
    errorBox.hidden = false;
  } finally {
    loading.hidden = true;
    btn.disabled = false;
  }
});
