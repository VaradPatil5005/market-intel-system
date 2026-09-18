const API = "/api";

async function getJSON(path) {
  const res = await fetch(API + path);
  if (!res.ok) throw new Error(path + " -> " + res.status);
  return res.json();
}

function fmtPct(x) {
  if (x === null || x === undefined) return "—";
  return Math.round(x * 100) + "%";
}

async function loadConfig() {
  try {
    const cfg = await getJSON("/config");
    const el = document.getElementById("watchlist-ticker");
    el.innerHTML = cfg.watchlist.map(w => `<span class="tag">${w}</span>`).join("");
  } catch (e) { /* non-fatal */ }
}

async function loadDashboard() {
  const d = await getJSON("/dashboard");
  document.getElementById("stat-runs").textContent = d.runs_completed;
  document.getElementById("stat-confidence").textContent = fmtPct(d.avg_confidence);
  document.getElementById("stat-entities").textContent = d.entities_tracked;
  document.getElementById("stat-trends").textContent = d.trend_signals;
  document.getElementById("stat-insights").textContent = d.insights_total;

  renderReport(d.latest_report);
  renderEntities(d.top_entities);
}

function renderReport(report) {
  const card = document.getElementById("report-card");
  if (!report) {
    card.innerHTML = `<p class="empty-state">No report yet — run the pipeline to generate one. In mock mode this uses seeded sample data, so it's safe to run immediately.</p>`;
    return;
  }
  let payload = {};
  try { payload = JSON.parse(report.full_report_json || "{}"); } catch (e) { payload = {}; }

  const section = (title, items) => {
    if (!items || !items.length) return "";
    const lis = items.map(i => {
      const conf = i.confidence !== undefined
        ? `<span class="confidence-pill ${i.confidence < 0.6 ? "low" : ""}">${fmtPct(i.confidence)}</span>`
        : "";
      return `<li>${i.text || i}${conf}</li>`;
    }).join("");
    return `<div class="report-block"><h4>${title}</h4><ul>${lis}</ul></div>`;
  };

  card.innerHTML = `
    <h3>${payload.title || report.report_title || "Market Intelligence Report"}</h3>
    <div class="timestamp">${payload.generated_at || report.created_at || ""}</div>
    <p class="summary">${payload.executive_summary || "No executive summary available."}</p>
    ${section("Key trends", payload.key_trends)}
    ${section("Competitor movements", payload.competitor_movements)}
    ${section("Sentiment shifts", payload.sentiment_shifts)}
    ${section("Risk signals", payload.risk_signals)}
  `;
}

function renderEntities(entities) {
  const tbody = document.querySelector("#entity-table tbody");
  if (!entities || !entities.length) {
    tbody.innerHTML = `<tr><td class="empty-state" colspan="3">No entities tracked yet.</td></tr>`;
    return;
  }
  tbody.innerHTML = entities.map(e =>
    `<tr><td>${e.name}</td><td>${e.type}</td><td class="num">${e.mentions}</td></tr>`
  ).join("");
}

async function loadTrends() {
  const tbody = document.querySelector("#trend-table tbody");
  try {
    const rows = await getJSON("/trends?limit=6");
    if (!rows.length) { tbody.innerHTML = `<tr><td class="empty-state" colspan="2">No trend signals yet.</td></tr>`; return; }
    tbody.innerHTML = rows.map(r =>
      `<tr><td>${r.topic || "signal"} <span class="empty-state">(${r.trend_label || ""})</span></td><td class="num">${r.z_score !== null && r.z_score !== undefined ? Number(r.z_score).toFixed(2) : ""}</td></tr>`
    ).join("");
  } catch (e) { tbody.innerHTML = `<tr><td class="empty-state" colspan="2">Unavailable.</td></tr>`; }
}

async function loadSentiment() {
  const tbody = document.querySelector("#sentiment-table tbody");
  try {
    const rows = await getJSON("/sentiment?limit=6");
    if (!rows.length) { tbody.innerHTML = `<tr><td class="empty-state" colspan="2">No sentiment data yet.</td></tr>`; return; }
    tbody.innerHTML = rows.map(r =>
      `<tr><td>${r.subject || r.source_id || "source"}</td><td class="num">${r.polarity_score !== null && r.polarity_score !== undefined ? Number(r.polarity_score).toFixed(2) : ""}</td></tr>`
    ).join("");
  } catch (e) { tbody.innerHTML = `<tr><td class="empty-state" colspan="2">Unavailable.</td></tr>`; }
}

function markPipeline(doneNodes, activeNode) {
  document.querySelectorAll("#pipeline-list li").forEach(li => {
    li.classList.remove("done", "active");
    const node = li.dataset.node;
    if (doneNodes.includes(node)) li.classList.add("done");
    if (node === activeNode) li.classList.add("active");
  });
}

async function pollRun(runKey) {
  const statusEl = document.getElementById("run-status");
  const btn = document.getElementById("run-btn");
  const poll = async () => {
    const r = await getJSON(`/run/${runKey}`);
    const checkpoints = (r.checkpoints || []).map(c => c.node);
    markPipeline(checkpoints, r.status === "running" ? "generate_report" : null);
    if (r.status === "queued" || r.status === "running") {
      statusEl.textContent = `running… (${checkpoints.length}/9 steps)`;
      setTimeout(poll, 1500);
    } else if (r.status === "complete") {
      statusEl.textContent = "run complete";
      btn.disabled = false;
      markPipeline(checkpoints, null);
      loadDashboard(); loadTrends(); loadSentiment();
    } else {
      statusEl.textContent = "error: " + (r.error || "unknown");
      btn.disabled = false;
    }
  };
  poll();
}

document.getElementById("run-btn").addEventListener("click", async () => {
  const btn = document.getElementById("run-btn");
  btn.disabled = true;
  document.getElementById("run-status").textContent = "queued…";
  try {
    const res = await fetch(API + "/run", { method: "POST" });
    const { run_key } = await res.json();
    pollRun(run_key);
  } catch (e) {
    document.getElementById("run-status").textContent = "failed to start run";
    btn.disabled = false;
  }
});

loadConfig();
loadDashboard();
loadTrends();
loadSentiment();
