const STORE_KEY = "gbus_holdings_v1";
const NOTIFY_KEY = "gbus_notified_alerts_v1";

let dashboardData = null;
let holdings = loadHoldings();
let selectedChartSymbol = "SPY";

const $ = (selector) => document.querySelector(selector);

document.addEventListener("DOMContentLoaded", () => {
  bindEvents();
  loadData();
  setInterval(() => loadData(true), 5 * 60 * 1000);
});

function bindEvents() {
  $("#holding-form").addEventListener("submit", saveHoldingFromForm);
  $("#reset-form").addEventListener("click", resetForm);
  $("#refresh-data").addEventListener("click", () => loadData());
  $("#enable-notify").addEventListener("click", requestNotifications);
  $("#chart-symbol").addEventListener("change", (event) => {
    selectedChartSymbol = event.target.value;
    drawChart(selectedChartSymbol);
  });
  window.addEventListener("resize", () => drawChart(selectedChartSymbol));

  document.body.addEventListener("click", (event) => {
    const button = event.target.closest("[data-action]");
    if (!button) return;
    const action = button.dataset.action;
    const symbol = button.dataset.symbol;
    const id = button.dataset.id;
    if (action === "chart" && symbol) {
      selectChart(symbol);
    }
    if (action === "fill" && symbol) {
      fillFormFromRecommendation(symbol);
    }
    if (action === "edit" && id) {
      editHolding(id);
    }
    if (action === "delete" && id) {
      deleteHolding(id);
    }
  });
}

async function loadData(silent = false) {
  try {
    if (!silent) $("#data-status").textContent = "加载中";
    const response = await fetch(`data/latest.json?ts=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    dashboardData = await response.json();
    renderAll();
  } catch (error) {
    $("#data-status").textContent = `数据加载失败：${error.message}`;
    renderHoldings();
  }
}

function renderAll() {
  renderStatus();
  renderPortfolioControls();
  renderHoldings();
  renderMarket();
  renderModules();
  renderSerenity();
  renderNews();
  renderSources();
  drawChart(selectedChartSymbol);
}

function renderStatus() {
  const data = dashboardData;
  $("#data-status").textContent = statusText(data.status);
  $("#trading-date").textContent = data.tradingDate || "--";
  $("#market-score").textContent = data.market?.marketScore ?? "--";
  $("#market-regime").textContent = data.market?.regime || "--";
  $("#status-band").className = `status-band ${data.market?.tone || ""}`;
}

function statusText(status) {
  if (status === "ok") return "已完成每日更新";
  if (status === "partial") return "已更新，部分数据缺失";
  if (status === "fallback") return "备用数据";
  return status || "未知";
}

function renderPortfolioControls() {
  const select = $("#chart-symbol");
  const symbols = new Set(Object.keys(dashboardData?.charts || {}));
  holdings.forEach((holding) => symbols.add(holding.symbol));
  const sorted = [...symbols].filter(Boolean).sort();
  if (!sorted.includes(selectedChartSymbol)) {
    selectedChartSymbol = sorted[0] || "SPY";
  }
  select.innerHTML = sorted
    .map((symbol) => `<option value="${escapeHtml(symbol)}">${escapeHtml(symbol)}</option>`)
    .join("");
  select.value = selectedChartSymbol;
}

function renderHoldings() {
  const tbody = $("#holdings-table");
  if (!holdings.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="muted">暂无持仓。可从推荐模块填入表单，或手动输入股票代码和买入价。</td></tr>`;
    $("#alerts-panel").innerHTML = `<div class="alert-item neutral"><div><strong>等待持仓输入</strong><span>你输入买入价后，页面会按最新数据判断卖点、止损和短线时间止损。</span></div></div>`;
    return;
  }

  const alerts = holdings.map(evaluateHolding);
  $("#alerts-panel").innerHTML = alerts.map(renderAlert).join("");
  maybeNotify(alerts);

  tbody.innerHTML = holdings
    .map((holding) => {
      const price = latestPrice(holding.symbol);
      const pnl = holding.entryPrice && price ? (price / holding.entryPrice - 1) * 100 : null;
      const alert = evaluateHolding(holding);
      return `
        <tr>
          <td><strong>${escapeHtml(holding.symbol)}</strong><br><span class="muted">${escapeHtml(holding.note || "")}</span></td>
          <td>${bucketLabel(holding.bucket)}</td>
          <td class="number">${formatMoney(holding.entryPrice)}</td>
          <td class="number">${formatMoney(price)}</td>
          <td class="number">${formatPct(pnl)}</td>
          <td>${escapeHtml(alert.title)}<br><span class="muted">${escapeHtml(alert.message)}</span></td>
          <td>
            <button class="small-button" data-action="chart" data-symbol="${escapeHtml(holding.symbol)}" type="button">图表</button>
            <button class="small-button" data-action="edit" data-id="${escapeHtml(holding.id)}" type="button">编辑</button>
            <button class="danger-button small-button" data-action="delete" data-id="${escapeHtml(holding.id)}" type="button">删除</button>
          </td>
        </tr>
      `;
    })
    .join("");
}

function renderAlert(alert) {
  return `
    <div class="alert-item ${alert.tone}">
      <div>
        <strong>${escapeHtml(alert.symbol)}：${escapeHtml(alert.title)}</strong>
        <span>${escapeHtml(alert.message)}</span>
      </div>
      <span class="status-pill ${alert.tone}">${escapeHtml(alert.level)}</span>
    </div>
  `;
}

function renderMarket() {
  const market = dashboardData?.market || {};
  const tiles = [
    ["MarketScore", market.marketScore ?? "--", "市场总风险分数"],
    ["SPY", `${formatMoney(market.spy?.close)} / MA200 ${formatMoney(market.spy?.ma200)}`, market.spy?.aboveMa200 ? "SPY 在 MA200 上方" : "SPY 未站稳 MA200"],
    ["QQQ", `${formatMoney(market.qqq?.close)} / 20D ${formatPct(market.qqq?.ret20d)}`, market.qqq?.aboveMa200 ? "QQQ 在 MA200 上方" : "QQQ 未站稳 MA200"],
    ["VIX", market.vix ?? "--", "低于 22 加分"],
    ["强于 MA50", `${market.percentUniverseAboveMa50 ?? "--"}%`, "配置股票池中的市场广度"],
    ["A 仓", `${percentWeight(market.allocation?.trend)}`, "趋势放大仓"],
    ["B 仓", `${percentWeight(market.allocation?.elastic)}`, "高弹性仓"],
    ["现金", `${percentWeight(market.allocation?.cash)}`, "防守和机会资金"]
  ];
  $("#market-dashboard").innerHTML = tiles
    .map(
      ([label, value, note]) => `
      <div class="metric-tile">
        <span class="label">${escapeHtml(label)}</span>
        <strong>${escapeHtml(String(value))}</strong>
        <span class="muted">${escapeHtml(note)}</span>
      </div>
    `
    )
    .join("");
}

function renderModules() {
  const modules = dashboardData?.modules || {};
  const order = ["trend", "elastic", "shortTerm", "cash"];
  $("#strategy-modules").innerHTML = order
    .map((key) => renderModule(modules[key]))
    .join("");
}

function renderModule(module) {
  if (!module) return "";
  const body = module.key === "cash" ? renderCashModule(module) : renderRecommendationTable(module);
  return `
    <article class="module-block">
      <div class="module-header">
        <div>
          <h3>${escapeHtml(module.title)}</h3>
          <span class="muted">${escapeHtml(module.objective || "")}</span>
        </div>
        <span class="allocation-badge">建议占比 ${module.allocationPct ?? "--"}%</span>
      </div>
      <div class="module-body">${body}</div>
    </article>
  `;
}

function renderCashModule(module) {
  return `
    <div class="text-panel">
      ${(module.rules || []).map((rule) => `<p>${escapeHtml(rule)}</p>`).join("")}
    </div>
  `;
}

function renderRecommendationTable(module) {
  const rows = module.recommendations || [];
  if (!rows.length) {
    return `<div class="empty-state">今日没有满足该模块阈值的推荐。市场或个股条件不够时，模型保持空仓/观察。</div>`;
  }
  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>股票</th>
            <th>动作/分数</th>
            <th>现价</th>
            <th>买点</th>
            <th>卖点与时间</th>
            <th>止损</th>
            <th>依据/风险</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          ${rows.map((rec) => renderRecommendationRow(rec, module.key)).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderRecommendationRow(rec, bucket) {
  return `
    <tr>
      <td>
        <strong>${escapeHtml(rec.symbol)}</strong><br>
        <span class="muted">${escapeHtml(rec.name || "")}</span><br>
        <span class="muted">${escapeHtml(rec.sector || "")}</span>
      </td>
      <td>
        <span class="status-pill ${String(rec.action || "").toLowerCase()}">${escapeHtml(rec.action || "WATCH")}</span><br>
        <strong>${escapeHtml(rec.scoreLabel || "Score")} ${rec.score ?? "--"}</strong>
      </td>
      <td class="number">
        ${formatMoney(rec.currentPrice)}<br>
        <span class="muted">ATR ${formatPct(rec.atrPct)}</span><br>
        <span class="muted">量比 ${rec.volumeRatio20 ?? "--"}</span>
      </td>
      <td class="plan-cell">
        <strong>${formatMoney(rec.entry?.price)}</strong><br>
        <span>${formatMoney(rec.entry?.zoneLow)} - ${formatMoney(rec.entry?.zoneHigh)}</span><br>
        <span>${escapeHtml(rec.entry?.note || "")}</span>
      </td>
      <td class="plan-cell">
        <strong>${formatMoney(rec.sell?.target1)} / ${formatMoney(rec.sell?.target2)}</strong><br>
        <span>${escapeHtml(rec.sell?.timeWindow || "")}</span><br>
        <span>${escapeHtml(rec.sell?.earliestDate || "")} 至 ${escapeHtml(rec.sell?.latestDate || "")}</span>
      </td>
      <td class="plan-cell">
        <strong>${formatMoney(rec.stop?.price)}</strong><br>
        <span>${escapeHtml(rec.stop?.timeWindow || "")}</span><br>
        <span>${escapeHtml(rec.stop?.note || "")}</span>
      </td>
      <td>
        <div class="reason-list">
          ${(rec.reasonCodes || []).map((item) => `<span class="tag">${escapeHtml(item)}</span>`).join("")}
          ${(rec.riskFlags || []).map((item) => `<span class="tag risk">${escapeHtml(item)}</span>`).join("")}
        </div>
        <div class="muted">建议单票 ${rec.positionSizePct ?? "--"}%</div>
      </td>
      <td>
        <button class="small-button" data-action="fill" data-symbol="${escapeHtml(rec.symbol)}" data-bucket="${escapeHtml(bucket)}" type="button">填入表单</button>
        <button class="small-button" data-action="chart" data-symbol="${escapeHtml(rec.symbol)}" type="button">图表</button>
      </td>
    </tr>
  `;
}

function renderSerenity() {
  const serenity = dashboardData?.serenity;
  if (!serenity) {
    $("#serenity-summary").innerHTML = "<p>暂无 Serenity 数据。</p>";
    return;
  }
  const summary = (serenity.summary || []).map((item) => `<p>${escapeHtml(item)}</p>`).join("");
  const posts = (serenity.posts || [])
    .map(
      (post) => `
      <p>
        <a href="${escapeAttr(post.url)}" target="_blank" rel="noreferrer">${escapeHtml(formatDateTime(post.createdAt))}</a>
        <br>${escapeHtml(post.text)}
      </p>
    `
    )
    .join("");
  $("#serenity-summary").innerHTML = `
    <p><span class="status-pill ${serenity.status === "ok" ? "positive" : "neutral"}">${escapeHtml(serenity.status || "unknown")}</span>
    <span class="muted">来源：${escapeHtml(serenity.source || "X")}</span></p>
    ${summary}
    ${posts}
  `;
}

function renderNews() {
  const marketNews = dashboardData?.news?.market || [];
  const bySymbol = dashboardData?.news?.bySymbol || {};
  const cards = [];
  if (marketNews.length) {
    cards.push(newsCard("大盘资讯", marketNews));
  }
  Object.entries(bySymbol)
    .slice(0, 8)
    .forEach(([symbol, items]) => cards.push(newsCard(symbol, items)));
  $("#news-list").innerHTML = cards.length ? cards.join("") : `<div class="text-panel">暂无资讯数据。</div>`;
}

function newsCard(title, items) {
  return `
    <article class="news-card">
      <h3>${escapeHtml(title)}</h3>
      ${(items || [])
        .slice(0, 4)
        .map(
          (item) => `
          <p>
            <a href="${escapeAttr(item.link)}" target="_blank" rel="noreferrer">${escapeHtml(item.title || "Untitled")}</a><br>
            <span class="muted">${escapeHtml(item.publisher || "")} ${escapeHtml(formatDateTime(item.publishedAt))}</span>
          </p>
        `
        )
        .join("")}
    </article>
  `;
}

function renderSources() {
  const sources = dashboardData?.sources || [];
  const errors = dashboardData?.errors || [];
  $("#source-list").innerHTML = `
    ${sources
      .map(
        (source) => `
        <div>
          <strong>${escapeHtml(source.name)}</strong>
          <a class="text-link" href="${escapeAttr(source.url)}" target="_blank" rel="noreferrer">打开来源</a>
          <br><span class="muted">${escapeHtml(source.usage || "")}</span>
        </div>
      `
      )
      .join("")}
    <div>
      <strong>自动更新</strong><br>
      <span class="muted">GitHub Actions 在美股交易日收盘后生成 data/latest.json 并发布 GitHub Pages。</span>
    </div>
    ${
      errors.length
        ? `<div><strong>本次运行警告</strong><ul class="error-list">${errors
            .slice(0, 12)
            .map((error) => `<li>${escapeHtml(error)}</li>`)
            .join("")}</ul></div>`
        : ""
    }
  `;
}

function saveHoldingFromForm(event) {
  event.preventDefault();
  const id = $("#holding-id").value || createId();
  const existing = holdings.find((item) => item.id === id);
  const holding = {
    id,
    symbol: normalizeSymbol($("#holding-symbol").value),
    bucket: $("#holding-bucket").value,
    entryPrice: numberOrNull($("#holding-entry").value),
    shares: numberOrNull($("#holding-shares").value),
    entryDate: $("#holding-date").value || dashboardData?.tradingDate || "",
    note: $("#holding-note").value.trim(),
    createdAt: existing?.createdAt || new Date().toISOString(),
    updatedAt: new Date().toISOString()
  };
  if (!holding.symbol) return;
  holdings = existing
    ? holdings.map((item) => (item.id === id ? holding : item))
    : [...holdings, holding];
  persistHoldings();
  resetForm();
  renderPortfolioControls();
  renderHoldings();
  selectChart(holding.symbol);
}

function fillFormFromRecommendation(symbol) {
  const rec = findRecommendation(symbol);
  $("#holding-id").value = "";
  $("#holding-symbol").value = symbol;
  $("#holding-bucket").value = recommendationBucket(symbol) || "trend";
  $("#holding-entry").value = rec?.entry?.price ?? "";
  $("#holding-shares").value = "";
  $("#holding-date").value = dashboardData?.tradingDate || "";
  $("#holding-note").value = rec ? `${rec.scoreLabel} ${rec.score}; ${rec.action}` : "";
  $("#holding-symbol").focus();
  $("#portfolio-section").scrollIntoView({ behavior: "smooth", block: "start" });
}

function editHolding(id) {
  const holding = holdings.find((item) => item.id === id);
  if (!holding) return;
  $("#holding-id").value = holding.id;
  $("#holding-symbol").value = holding.symbol;
  $("#holding-bucket").value = holding.bucket;
  $("#holding-entry").value = holding.entryPrice ?? "";
  $("#holding-shares").value = holding.shares ?? "";
  $("#holding-date").value = holding.entryDate || "";
  $("#holding-note").value = holding.note || "";
  $("#holding-symbol").focus();
}

function deleteHolding(id) {
  holdings = holdings.filter((item) => item.id !== id);
  persistHoldings();
  renderPortfolioControls();
  renderHoldings();
  drawChart(selectedChartSymbol);
}

function resetForm() {
  $("#holding-form").reset();
  $("#holding-id").value = "";
  $("#holding-date").value = dashboardData?.tradingDate || "";
}

function evaluateHolding(holding) {
  const symbol = holding.symbol;
  const price = latestPrice(symbol);
  const entry = holding.entryPrice;
  if (!entry) {
    return {
      id: holding.id,
      symbol,
      tone: "neutral",
      level: "跳过",
      title: "未输入买入价",
      message: "今日推荐策略不触发卖点或止损提醒。"
    };
  }
  if (!price) {
    return {
      id: holding.id,
      symbol,
      tone: "neutral",
      level: "等待",
      title: "无最新价格",
      message: "该标的未在当前数据集中，等待下一次更新或加入脚本股票池。"
    };
  }
  const rec = findRecommendation(symbol);
  const stop = rec?.stop?.price ?? entry * 0.93;
  const target1 = rec?.sell?.target1 ?? entry * 1.15;
  const target2 = rec?.sell?.target2 ?? entry * 1.25;
  const pnl = (price / entry - 1) * 100;
  const heldDays = businessDaysBetween(holding.entryDate, dashboardData?.tradingDate);

  if (price <= stop) {
    return {
      id: holding.id,
      symbol,
      tone: "negative",
      level: "止损",
      title: "触发止损线",
      message: `现价 ${formatMoney(price)} <= 止损 ${formatMoney(stop)}，优先执行风控。`
    };
  }
  if (price >= target2) {
    return {
      id: holding.id,
      symbol,
      tone: "positive",
      level: "卖点2",
      title: "到达第二目标",
      message: `现价 ${formatMoney(price)}，收益 ${formatPct(pnl)}，考虑再卖出 1/3 或抬高保护线。`
    };
  }
  if (price >= target1) {
    return {
      id: holding.id,
      symbol,
      tone: "positive",
      level: "卖点1",
      title: "到达第一目标",
      message: `现价 ${formatMoney(price)}，收益 ${formatPct(pnl)}，考虑卖出 1/3 或 1/2。`
    };
  }
  if (holding.bucket === "shortTerm" && heldDays !== null && heldDays > 10) {
    return {
      id: holding.id,
      symbol,
      tone: "neutral",
      level: "时间止损",
      title: "短线持有超 10 个交易日",
      message: "除非转入趋势仓，否则短线仓应按计划退出或降仓。"
    };
  }
  return {
    id: holding.id,
    symbol,
    tone: "neutral",
    level: "持有",
    title: "未到卖点或止损",
    message: `现价 ${formatMoney(price)}，收益 ${formatPct(pnl)}。继续按计划监控。`
  };
}

function maybeNotify(alerts) {
  if (!("Notification" in window) || Notification.permission !== "granted") return;
  const stored = new Set(JSON.parse(localStorage.getItem(NOTIFY_KEY) || "[]"));
  const today = dashboardData?.tradingDate || new Date().toISOString().slice(0, 10);
  let changed = false;
  alerts
    .filter((alert) => ["止损", "卖点1", "卖点2", "时间止损"].includes(alert.level))
    .forEach((alert) => {
      const key = `${today}:${alert.id}:${alert.level}`;
      if (stored.has(key)) return;
      new Notification(`${alert.symbol} ${alert.title}`, { body: alert.message });
      stored.add(key);
      changed = true;
    });
  if (changed) {
    localStorage.setItem(NOTIFY_KEY, JSON.stringify([...stored].slice(-100)));
  }
}

async function requestNotifications() {
  if (!("Notification" in window)) {
    $("#enable-notify").textContent = "浏览器不支持提醒";
    return;
  }
  const permission = await Notification.requestPermission();
  $("#enable-notify").textContent = permission === "granted" ? "提醒已开启" : "提醒未开启";
  renderHoldings();
}

function drawChart(symbol) {
  const canvas = $("#price-chart");
  if (!canvas) return;
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(320, Math.floor(rect.width * dpr));
  canvas.height = Math.max(260, Math.floor(rect.height * dpr));
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const width = canvas.width / dpr;
  const height = canvas.height / dpr;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);

  const chart = dashboardData?.charts?.[symbol];
  $("#chart-caption").textContent = chart?.bars?.length
    ? `${symbol} 最近 ${chart.bars.length} 个交易日`
    : `${symbol} 暂无可画数据`;
  if (!chart?.bars?.length) {
    drawEmptyChart(ctx, width, height, "暂无价格数据");
    return;
  }

  const padding = { left: 58, right: 18, top: 18, bottom: 34 };
  const bars = chart.bars;
  const series = bars.map((bar) => bar.close).filter(isFiniteNumber);
  const holding = holdings.find((item) => item.symbol === symbol && item.entryPrice);
  const rec = findRecommendation(symbol);
  const guideValues = [
    holding?.entryPrice,
    rec?.stop?.price,
    rec?.sell?.target1,
    rec?.sell?.target2
  ].filter(isFiniteNumber);
  const min = Math.min(...series, ...guideValues);
  const max = Math.max(...series, ...guideValues);
  const range = max === min ? max * 0.1 || 1 : max - min;
  const yMin = min - range * 0.08;
  const yMax = max + range * 0.08;
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;
  const x = (index) => padding.left + (index / Math.max(1, bars.length - 1)) * innerW;
  const y = (value) => padding.top + (1 - (value - yMin) / (yMax - yMin)) * innerH;

  drawGrid(ctx, width, height, padding, yMin, yMax);
  drawLine(ctx, bars.map((bar) => bar.close), x, y, "#2563eb", 2.4);
  drawLine(ctx, bars.map((bar) => bar.ma20), x, y, "#b7791f", 1.5);
  drawLine(ctx, bars.map((bar) => bar.ma50), x, y, "#0f766e", 1.5);
  drawGuide(ctx, holding?.entryPrice, y, padding, width, "#111827", "买入");
  drawGuide(ctx, rec?.stop?.price, y, padding, width, "#c2410c", "止损");
  drawGuide(ctx, rec?.sell?.target1, y, padding, width, "#15803d", "目标1");
  drawGuide(ctx, rec?.sell?.target2, y, padding, width, "#15803d", "目标2");

  ctx.fillStyle = "#344054";
  ctx.font = "12px Inter, sans-serif";
  ctx.fillText(bars[0].date, padding.left, height - 10);
  ctx.textAlign = "right";
  ctx.fillText(bars.at(-1).date, width - padding.right, height - 10);
  ctx.textAlign = "left";
  ctx.fillStyle = "#2563eb";
  ctx.fillText("收盘价", padding.left, 14);
  ctx.fillStyle = "#b7791f";
  ctx.fillText("MA20", padding.left + 58, 14);
  ctx.fillStyle = "#0f766e";
  ctx.fillText("MA50", padding.left + 106, 14);
}

function drawEmptyChart(ctx, width, height, text) {
  ctx.fillStyle = "#687586";
  ctx.font = "15px Inter, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(text, width / 2, height / 2);
  ctx.textAlign = "left";
}

function drawGrid(ctx, width, height, padding, min, max) {
  ctx.strokeStyle = "#e5eaf0";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#687586";
  ctx.font = "12px Inter, sans-serif";
  ctx.textAlign = "right";
  for (let i = 0; i <= 4; i += 1) {
    const pct = i / 4;
    const y = padding.top + pct * (height - padding.top - padding.bottom);
    const value = max - pct * (max - min);
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(width - padding.right, y);
    ctx.stroke();
    ctx.fillText(formatMoney(value), padding.left - 8, y + 4);
  }
  ctx.textAlign = "left";
}

function drawLine(ctx, list, x, y, color, width) {
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.beginPath();
  let started = false;
  list.forEach((value, index) => {
    if (!isFiniteNumber(value)) return;
    if (!started) {
      ctx.moveTo(x(index), y(value));
      started = true;
    } else {
      ctx.lineTo(x(index), y(value));
    }
  });
  if (started) ctx.stroke();
}

function drawGuide(ctx, value, y, padding, width, color, label) {
  if (!isFiniteNumber(value)) return;
  const yy = y(value);
  ctx.save();
  ctx.strokeStyle = color;
  ctx.setLineDash([5, 5]);
  ctx.beginPath();
  ctx.moveTo(padding.left, yy);
  ctx.lineTo(width - padding.right, yy);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.fillStyle = color;
  ctx.font = "12px Inter, sans-serif";
  ctx.fillText(`${label} ${formatMoney(value)}`, padding.left + 6, yy - 5);
  ctx.restore();
}

function selectChart(symbol) {
  selectedChartSymbol = symbol;
  renderPortfolioControls();
  $("#chart-symbol").value = symbol;
  drawChart(symbol);
}

function latestPrice(symbol) {
  const chart = dashboardData?.charts?.[symbol];
  if (chart?.bars?.length) return chart.bars.at(-1).close;
  const rec = findRecommendation(symbol);
  return rec?.currentPrice ?? null;
}

function findRecommendation(symbol) {
  return allRecommendations().find((rec) => rec.symbol === normalizeSymbol(symbol));
}

function recommendationBucket(symbol) {
  const normalized = normalizeSymbol(symbol);
  const modules = dashboardData?.modules || {};
  for (const [key, module] of Object.entries(modules)) {
    if ((module.recommendations || []).some((rec) => rec.symbol === normalized)) return key;
  }
  return null;
}

function allRecommendations() {
  const modules = dashboardData?.modules || {};
  return Object.values(modules).flatMap((module) => module.recommendations || []);
}

function loadHoldings() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORE_KEY) || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function persistHoldings() {
  localStorage.setItem(STORE_KEY, JSON.stringify(holdings));
}

function normalizeSymbol(value) {
  return String(value || "").trim().toUpperCase();
}

function numberOrNull(value) {
  const numeric = Number(String(value).replace(/,/g, ""));
  return Number.isFinite(numeric) && numeric > 0 ? numeric : null;
}

function createId() {
  if (crypto.randomUUID) return crypto.randomUUID();
  return `h-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function isFiniteNumber(value) {
  return Number.isFinite(Number(value));
}

function formatMoney(value) {
  if (!isFiniteNumber(value)) return "--";
  return `$${Number(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}`;
}

function formatPct(value) {
  if (!isFiniteNumber(value)) return "--";
  return `${Number(value).toFixed(2)}%`;
}

function formatDateTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function percentWeight(value) {
  if (!isFiniteNumber(value)) return "--";
  return `${(Number(value) * 100).toFixed(1)}%`;
}

function bucketLabel(bucket) {
  return {
    trend: "A 趋势放大仓",
    elastic: "B 高弹性仓",
    shortTerm: "C 短线交易仓",
    cash: "D 现金/观察"
  }[bucket] || bucket;
}

function businessDaysBetween(startText, endText) {
  if (!startText || !endText) return null;
  const start = new Date(`${startText}T12:00:00Z`);
  const end = new Date(`${endText}T12:00:00Z`);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return null;
  let days = 0;
  const cursor = new Date(start);
  while (cursor < end) {
    cursor.setUTCDate(cursor.getUTCDate() + 1);
    const day = cursor.getUTCDay();
    if (day !== 0 && day !== 6) days += 1;
  }
  return days;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}
