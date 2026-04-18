/* PRISM frontend — websocket client, live meters, progress, summary */

const STRATEGY_DESC = {
  "draft-polish":        "OpenClaw drafts → Claude polishes. Balanced savings.",
  "parallel-specialist": "All 3 run in parallel, each on its specialty.",
  "cascade":             "Cheapest tries first; escalates only if unsure.",
  "vote-of-three":       "All 3 answer; PRISM picks consensus. Robust.",
  "context-share":       "One reads, others use the distilled brief. ~70% savings.",
};

const $ = (id) => document.getElementById(id);
let ws, config, selectedStrategy, running = false;
let perAgent = {}; // { claude: {in,out,cost,tps}, ... }
let stepsMeta = [];
let stepsDone = 0;

// ── Boot ────────────────────────────────────────────────────────
(async function init() {
  config = await fetch("/api/config").then(r => r.json());
  selectedStrategy = config.default;
  renderStrategies();
  ["claude","openclaw","mythos"].forEach(a => {
    const m = config.agents[a];
    $(`model-${a}`).textContent = m.model || "—";
    if (!m.configured) $(`chip-${a}`).style.opacity = 0.45;
  });
  connectWS();
  loadHistory();
  bindUI();
})();

function renderStrategies() {
  const g = $("strategy-grid");
  g.innerHTML = "";
  for (const s of config.strategies) {
    const el = document.createElement("div");
    el.className = "strategy" + (s === selectedStrategy ? " selected" : "");
    el.innerHTML = `
      <div class="strategy-name">${s}</div>
      <div class="strategy-desc">${STRATEGY_DESC[s] || ""}</div>`;
    el.onclick = () => {
      selectedStrategy = s;
      [...g.children].forEach(c => c.classList.remove("selected"));
      el.classList.add("selected");
    };
    g.appendChild(el);
  }
}

function bindUI() {
  $("run-btn").onclick = run;
  $("task").addEventListener("keydown", (e) => {
    if (e.ctrlKey && e.key === "Enter") run();
  });
  document.querySelectorAll(".tab").forEach(t => {
    t.onclick = () => {
      document.querySelectorAll(".tab").forEach(x => x.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(x => x.classList.remove("active"));
      t.classList.add("active");
      $(`pane-${t.dataset.tab}`).classList.add("active");
      if (t.dataset.tab === "history") loadHistory();
    };
  });
}

// ── Websocket ───────────────────────────────────────────────────
function connectWS() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws`);
  ws.onopen    = () => { $("conn-status").textContent = "● connected"; $("conn-status").className = "ok"; };
  ws.onclose   = () => { $("conn-status").textContent = "● disconnected"; $("conn-status").className = "bad"; setTimeout(connectWS, 2000); };
  ws.onerror   = () => { $("conn-status").textContent = "● error"; $("conn-status").className = "bad"; };
  ws.onmessage = (e) => handle(JSON.parse(e.data));
}

function run() {
  if (running) return;
  const task = $("task").value.trim();
  if (!task) { $("task").focus(); return; }
  resetMeters();
  running = true;
  $("run-btn").disabled = true;
  $("run-btn").querySelector(".run-btn-text").textContent = "RUNNING…";
  switchTab("stream");
  ws.send(JSON.stringify({ type: "run", task, strategy: selectedStrategy }));
}

function switchTab(name) {
  document.querySelectorAll(".tab").forEach(t =>
    t.classList.toggle("active", t.dataset.tab === name));
  document.querySelectorAll(".tab-pane").forEach(p =>
    p.classList.toggle("active", p.id === `pane-${name}`));
}

function resetMeters() {
  perAgent = {};
  stepsDone = 0;
  stepsMeta = [];
  $("progress-fill").style.width = "0%";
  $("progress-pct").textContent = "0%";
  $("savings-value").textContent = "$0.0000";
  $("savings-pct").textContent = "0% cheaper";
  ["claude","openclaw","mythos"].forEach(a => {
    $(`tps-${a}`).textContent = "0 tok/s";
    $(`tok-${a}`).textContent = "0 in · 0 out";
    $(`cost-${a}`).textContent = "$0.0000";
    $(`bar-${a}`).style.width = "0%";
    document.querySelector(`.meter[data-agent="${a}"]`).classList.remove("active");
    $(`chip-${a}`).classList.remove("active");
  });
  $("pane-stream").innerHTML = "";
}

// ── Event handler ────────────────────────────────────────────────
let bubbles = {}; // idx -> {headEl, textEl}

function handle(evt) {
  switch (evt.type) {
    case "plan": {
      stepsMeta = evt.steps;
      bubbles = {};
      const p = $("pane-stream");
      p.innerHTML = `<div class="bubble" style="border-color:#f5c24c">
        <div class="bubble-head"><span class="bubble-agent">PRISM PLAN</span>
        <span>${evt.strategy}</span></div>
        <div class="bubble-text">${evt.steps.length} step(s) — ${
          evt.steps.map(s => `${s.agent}(${s.role})`).join(" · ")
        }</div></div>`;
      break;
    }
    case "step_start": {
      const p = $("pane-stream");
      const div = document.createElement("div");
      div.className = "bubble";
      div.dataset.agent = evt.agent;
      div.innerHTML = `
        <div class="bubble-head">
          <span class="bubble-agent">${evt.agent.toUpperCase()} · ${evt.role}</span>
          <span>${evt.model || ""}</span>
        </div>
        <div class="bubble-text"></div>`;
      p.appendChild(div);
      p.scrollTop = p.scrollHeight;
      bubbles[evt.idx] = { textEl: div.querySelector(".bubble-text") };
      document.querySelector(`.meter[data-agent="${evt.agent}"]`)?.classList.add("active");
      $(`chip-${evt.agent}`)?.classList.add("active");
      break;
    }
    case "delta": {
      const b = bubbles[evt.idx];
      if (b) { b.textEl.textContent += evt.delta; $("pane-stream").scrollTop = $("pane-stream").scrollHeight; }
      // Live meters
      $(`tps-${evt.agent}`).textContent = `${evt.tps} tok/s`;
      $(`tok-${evt.agent}`).textContent = `${evt.tokens_in} in · ${evt.tokens_out} out`;
      const maxTps = 120;
      $(`bar-${evt.agent}`).style.width = Math.min(100, (evt.tps / maxTps) * 100) + "%";
      break;
    }
    case "step_done": {
      stepsDone += 1;
      perAgent[evt.agent] = perAgent[evt.agent] || { tin: 0, tout: 0, cost: 0 };
      perAgent[evt.agent].tin  += evt.tokens_in;
      perAgent[evt.agent].tout += evt.tokens_out;
      perAgent[evt.agent].cost += evt.cost_usd;
      $(`cost-${evt.agent}`).textContent = "$" + perAgent[evt.agent].cost.toFixed(4);
      const pct = Math.min(100, (stepsDone / stepsMeta.length) * 100);
      $("progress-fill").style.width = pct + "%";
      $("progress-pct").textContent = Math.round(pct) + "%";
      document.querySelector(`.meter[data-agent="${evt.agent}"]`)?.classList.remove("active");
      break;
    }
    case "complete": {
      running = false;
      $("run-btn").disabled = false;
      $("run-btn").querySelector(".run-btn-text").textContent = "RUN THE MESH";
      $("progress-fill").style.width = "100%";
      $("progress-pct").textContent = "100%";
      $("savings-value").textContent = "$" + evt.saved_usd.toFixed(4);
      $("savings-pct").textContent = `${evt.saved_pct}% cheaper than pure Claude`;
      ["claude","openclaw","mythos"].forEach(a => $(`chip-${a}`)?.classList.remove("active"));
      renderSummary(evt);
      loadHistory();
      break;
    }
    case "error": {
      running = false;
      $("run-btn").disabled = false;
      $("run-btn").querySelector(".run-btn-text").textContent = "RUN THE MESH";
      const p = $("pane-stream");
      const d = document.createElement("div");
      d.className = "bubble";
      d.style.borderColor = "#ff6b6b";
      d.innerHTML = `<div class="bubble-head"><span class="bubble-agent" style="color:#ff6b6b">ERROR</span></div>
        <div class="bubble-text">${evt.error}</div>`;
      p.appendChild(d);
      break;
    }
  }
}

function renderSummary(evt) {
  const agents = Object.entries(evt.totals)
    .map(([a, v]) => `<li><b style="color:var(--${a})">${a}</b> — ${v.tokens_in} in · ${v.tokens_out} out · $${v.cost_usd.toFixed(4)} · ${v.ms}ms</li>`)
    .join("");
  $("pane-summary").innerHTML = `
    <div class="summary-card">
      <h3>WHAT THE MESH DID</h3>
      <div class="summary-text">${evt.summary}</div>
    </div>
    <div class="summary-card">
      <h3>PER-AGENT USAGE</h3>
      <ul class="summary-text" style="margin:0;padding-left:18px">${agents}</ul>
    </div>
    <div class="summary-card">
      <h3>COST BREAKDOWN</h3>
      <div class="summary-text">
        Spent: <b>$${evt.spent_usd.toFixed(4)}</b><br/>
        Pure-Claude baseline: <b>$${evt.baseline_usd.toFixed(4)}</b><br/>
        <span style="color:var(--gold)">Saved: $${evt.saved_usd.toFixed(4)} (${evt.saved_pct}%)</span>
      </div>
    </div>
    <div class="summary-card">
      <h3>FINAL OUTPUT</h3>
      <pre class="summary-text" style="white-space:pre-wrap">${escapeHtml(evt.final_output || "")}</pre>
    </div>`;
  switchTab("summary");
}

async function loadHistory() {
  try {
    const h = await fetch("/api/history").then(r => r.json());
    const p = $("pane-history");
    if (!h.length) { p.innerHTML = '<div class="summary-empty">No runs yet.</div>'; return; }
    p.innerHTML = h.reverse().map(r => `
      <div class="history-row">
        <div class="history-task">${escapeHtml((r.task || "").slice(0, 120))}</div>
        <div class="history-meta">${r.strategy} · saved $${(r.saved_usd||0).toFixed(4)} (${(r.saved_pct||0)}%) · ${new Date((r.ts||0)*1000).toLocaleTimeString()}</div>
      </div>`).join("");
  } catch {}
}

function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, c =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
