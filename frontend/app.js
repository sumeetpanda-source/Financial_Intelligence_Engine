const state = {
  summary: null,
  currentTable: "recommendations",
};

const numberFmt = new Intl.NumberFormat("en-US");

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Request failed: ${url}`);
  return response.json();
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `Request failed: ${url}`);
  return data;
}

function text(value) {
  if (value === null || value === undefined || value === "") return "N/A";
  return String(value);
}

function renderMetrics(summary) {
  const metrics = [
    ["Universe", summary.universe_count, "cached companies"],
    ["Features", summary.feature_count, "ML-ready rows"],
    ["Deep Analysis", summary.deep_analysis_count, "scored companies"],
    ["News", summary.news_count, "sentiment articles"],
    ["Technicals", summary.technical_count, "indicator rows"],
  ];

  document.getElementById("metrics").innerHTML = metrics.map(([label, value, caption]) => `
    <article class="metric">
      <span>${label}</span>
      <strong>${numberFmt.format(value || 0)}</strong>
      <span>${caption}</span>
    </article>
  `).join("");

  document.getElementById("runState").innerHTML = `
    <span class="dot"></span>
    ${text(summary.environment)} data | ${text(summary.genai_provider)} GenAI
  `;
}

function renderBars(distribution) {
  const entries = Object.entries(distribution || {});
  const total = entries.reduce((sum, [, count]) => sum + count, 0) || 1;
  document.getElementById("recommendationBars").innerHTML = entries.map(([name, count]) => {
    const pct = Math.round((count / total) * 100);
    return `
      <div class="bar-row">
        <strong>${name}</strong>
        <div class="track"><div class="fill" style="width:${pct}%"></div></div>
        <span>${count}</span>
      </div>
    `;
  }).join("") || "<p>No recommendation data found.</p>";
}

function renderRankList(id, rows, scoreField, captionField) {
  document.getElementById(id).innerHTML = (rows || []).map((row) => `
    <div class="rank-item">
      <strong>${text(row.Ticker || row.ticker)}</strong>
      <div>
        <span>${text(row.Company || row.company_name || row.ticker)}</span>
        <small>${text(row[captionField])}</small>
      </div>
      <span class="badge">${text(row[scoreField])}</span>
    </div>
  `).join("") || "<p>No rows found.</p>";
}

function renderOutputs(files) {
  document.getElementById("outputFiles").innerHTML = (files || []).map((file) => `
    <a class="file-item ${file.exists ? "" : "disabled"}" href="${file.url || "#"}" target="_blank" rel="noreferrer">
      <strong>${file.name}</strong>
      <span>${file.exists ? `${file.size_kb} KB` : "Missing"}</span>
      <span class="badge">${file.exists ? "Open file" : "Missing"}</span>
    </a>
  `).join("");
}

function renderOverview(summary) {
  renderBars(summary.recommendation_distribution);
  renderRankList("topRecommendations", summary.top_recommendations, "Overall Score", "Recommendation");
  renderRankList("sentimentLeaders", summary.sentiment_leaders, "avg_sentiment", "news_count");
  renderOutputs(summary.output_files);
}

async function renderUniverse() {
  const query = encodeURIComponent(document.getElementById("universeSearch").value.trim());
  const payload = await getJson(`/api/universe?limit=1000&q=${query}`);
  document.getElementById("universeRows").innerHTML = payload.rows.map((row) => `
    <tr>
      <td><strong>${text(row.ticker)}</strong></td>
      <td>${text(row.company_name)}</td>
      <td>${text(row.exchange)}</td>
      <td>${text(row.source)}</td>
    </tr>
  `).join("");
}

function tableFromRows(rows, columns) {
  if (!rows || rows.length === 0) return "<tbody><tr><td>No data found.</td></tr></tbody>";
  return `
    <thead><tr>${columns.map((column) => `<th>${column.label}</th>`).join("")}</tr></thead>
    <tbody>
      ${rows.map((row) => `
        <tr>${columns.map((column) => `<td>${text(row[column.key])}</td>`).join("")}</tr>
      `).join("")}
    </tbody>
  `;
}

async function renderAnalysisTable(kind = state.currentTable) {
  state.currentTable = kind;
  document.querySelectorAll(".segment").forEach((button) => {
    button.classList.toggle("active", button.dataset.table === kind);
  });

  const config = {
    recommendations: {
      url: "/api/recommendations",
      columns: [
        { key: "Ticker", label: "Ticker" },
        { key: "Company", label: "Company" },
        { key: "Overall Score", label: "Overall" },
        { key: "Recommendation", label: "Recommendation" },
        { key: "Risk Level", label: "Risk" },
        { key: "Confidence %", label: "Confidence" },
      ],
    },
    sentiment: {
      url: "/api/sentiment",
      columns: [
        { key: "ticker", label: "Ticker" },
        { key: "avg_sentiment", label: "Average" },
        { key: "sentiment_volatility", label: "Volatility" },
        { key: "total_positive_signals", label: "Positive" },
        { key: "total_negative_signals", label: "Negative" },
        { key: "news_count", label: "News" },
      ],
    },
    news: {
      url: "/api/news?limit=80",
      columns: [
        { key: "ticker", label: "Ticker" },
        { key: "date", label: "Date" },
        { key: "headline", label: "Headline" },
        { key: "sentiment_label", label: "Sentiment" },
        { key: "source", label: "Source" },
      ],
    },
  }[kind];

  const payload = await getJson(config.url);
  document.getElementById("analysisTable").innerHTML = tableFromRows(payload.rows, config.columns);
}

function markdownToHtml(markdown) {
  return text(markdown)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/^### (.*)$/gm, "<h4>$1</h4>")
    .replace(/^## (.*)$/gm, "<h3>$1</h3>")
    .replace(/^# (.*)$/gm, "<h3>$1</h3>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n- /g, "\n* ")
    .replace(/\n/g, "<br>");
}

function renderAskAnswer(payload) {
  const suggestions = (payload.suggestions || []).map((item) => `
    <div class="suggestion-card">
      <div>
        <strong>${text(item.ticker)}</strong>
        <span>${text(item.recommendation)}</span>
      </div>
      <div class="score">${text(item.investment_score)}</div>
      <small>
        Sentiment ${text(item.drivers?.sentiment_score)} |
        Risk ${text(item.drivers?.risk_score)} |
        Return ${text(item.drivers?.expected_return_pct)}%
      </small>
    </div>
  `).join("");

  const agents = (payload.agent_summaries || []).map((agent) => `
    <div class="agent-note">
      <strong>${text(agent.agent)}</strong>
      <span>${text(agent.summary)}</span>
      <small>Confidence: ${text(agent.confidence)}</small>
    </div>
  `).join("");

  const evidence = (payload.evidence || []).map((item, index) => `
    <div class="evidence-item">
      <div>
        <strong>[${index + 1}] ${text(item.filename)}</strong>
        <span>${text(item.document_type)}${item.page_number ? ` | page ${item.page_number}` : ""}</span>
      </div>
      <span class="badge">${text(item.score)}</span>
      <p>${text(item.snippet)}</p>
    </div>
  `).join("");

  document.getElementById("answerPanel").innerHTML = `
    <div class="answer-block">
      <span class="badge">${text(payload.tickers?.join(", "))}</span>
      <h3>Suggestion</h3>
      <div class="suggestion-grid">${suggestions}</div>
      <h3>Explanation</h3>
      <div class="answer-text">${markdownToHtml(payload.answer)}</div>
      <h3>Agent Signals</h3>
      <div class="agent-grid">${agents}</div>
      <h3>Retrieved Evidence</h3>
      <div class="evidence-grid">${evidence || "<p>No evidence returned.</p>"}</div>
      <p class="disclaimer">${text(payload.disclaimer)}</p>
    </div>
  `;
}

async function askQuestion(question) {
  const status = document.getElementById("askStatus");
  status.textContent = "Analyzing...";
  document.getElementById("answerPanel").innerHTML = `<div class="empty-answer">Running the multi-agent workflow.</div>`;

  try {
    const payload = await postJson("/api/ask", { question });
    renderAskAnswer(payload);
    status.textContent = "Done";
  } catch (error) {
    document.getElementById("answerPanel").innerHTML = `<div class="empty-answer">${text(error.message)}</div>`;
    status.textContent = "Failed";
  }
}

function bindEvents() {
  document.querySelectorAll(".nav-button").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".nav-button").forEach((item) => item.classList.remove("active"));
      document.querySelectorAll(".view").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      document.getElementById(button.dataset.view).classList.add("active");
    });
  });

  document.querySelectorAll(".segment").forEach((button) => {
    button.addEventListener("click", () => renderAnalysisTable(button.dataset.table));
  });

  document.getElementById("universeSearch").addEventListener("input", () => {
    clearTimeout(window.universeTimer);
    window.universeTimer = setTimeout(renderUniverse, 180);
  });

  document.getElementById("askForm").addEventListener("submit", (event) => {
    event.preventDefault();
    const question = document.getElementById("questionInput").value.trim();
    if (question) askQuestion(question);
  });

  document.querySelectorAll(".prompt-chips button").forEach((button) => {
    button.addEventListener("click", () => {
      document.getElementById("questionInput").value = button.dataset.question;
      askQuestion(button.dataset.question);
    });
  });
}

async function init() {
  bindEvents();
  state.summary = await getJson("/api/summary");
  renderMetrics(state.summary);
  renderOverview(state.summary);
  await renderUniverse();
  await renderAnalysisTable();
}

init().catch((error) => {
  document.body.innerHTML = `<main class="shell"><h1>Dashboard error</h1><p>${error.message}</p></main>`;
});
