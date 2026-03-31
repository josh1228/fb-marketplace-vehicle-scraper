/**
 * Popup Script – FB Marketplace Car Deal Finder
 *
 * Handles all UI interactions in popup.html:
 *  - Tab switching
 *  - Listing + sorting/filtering deals
 *  - Scan buttons
 *  - Filter/preferences form
 *  - All tool panels (price analyser, score calculator, CSV export,
 *    open marketplace, compare deals, price-drop tracker, notifications)
 */

"use strict";

// ─── Helpers ──────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const fmt = n => n != null ? `$${Number(n).toLocaleString()}` : "N/A";

function sendMsg(type, payload = {}) {
  return new Promise((res, rej) => {
    chrome.runtime.sendMessage({ type, ...payload }, response => {
      if (chrome.runtime.lastError) rej(chrome.runtime.lastError);
      else res(response);
    });
  });
}

function scoreBadgeClass(score) {
  if (score >= 80) return "badge-green";
  if (score >= 60) return "badge-blue";
  if (score >= 40) return "badge-amber";
  return "badge-red";
}

// ─── State ───────────────────────────────────────────────────────────────────
// computeDealScore is provided by scoring.js, loaded before this script.
let allDeals = [];
let currentPrefs = {};

// ─── Tab switching ────────────────────────────────────────────────────────────
document.querySelectorAll(".tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach(c => c.classList.add("hidden"));
    tab.classList.add("active");
    $(`tab-${tab.dataset.tab}`).classList.remove("hidden");
    if (tab.dataset.tab === "tools") refreshStats();
  });
});

// ─── Render deals ─────────────────────────────────────────────────────────────
function renderDeals() {
  const list     = $("deals-list");
  const sortBy   = $("sort-select").value;
  const minScore = parseInt($("min-score-input").value || "0", 10);

  let deals = allDeals.filter(d => (d.score ?? 0) >= minScore);

  switch (sortBy) {
    case "score":       deals.sort((a, b) => (b.score ?? 0) - (a.score ?? 0)); break;
    case "price-asc":   deals.sort((a, b) => (a.priceNum ?? 1e9) - (b.priceNum ?? 1e9)); break;
    case "price-desc":  deals.sort((a, b) => (b.priceNum ?? 0) - (a.priceNum ?? 0)); break;
    case "year-desc":   deals.sort((a, b) => (b.yearNum ?? 0) - (a.yearNum ?? 0)); break;
    case "mileage-asc": deals.sort((a, b) => (a.mileageNum ?? 1e9) - (b.mileageNum ?? 1e9)); break;
    case "recent":      deals.sort((a, b) => (b.foundAt ?? 0) - (a.foundAt ?? 0)); break;
  }

  if (!deals.length) {
    list.innerHTML = `<p class="empty-msg">No deals match your filters.<br>Click <strong>⟳ Scan</strong> or visit Facebook Marketplace.</p>`;
    return;
  }

  list.innerHTML = deals.map(d => {
    const isHot = (d.score ?? 0) >= (currentPrefs.dealScoreThreshold ?? 60);
    const thumb = d.image_url
      ? `<img class="deal-thumb" src="${escHtml(d.image_url)}" alt="" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'" /><div class="deal-thumb-placeholder" style="display:none">🚗</div>`
      : `<div class="deal-thumb-placeholder">🚗</div>`;

    return `
      <div class="deal-card${isHot ? " hot" : ""}">
        ${thumb}
        <div class="deal-info">
          <div class="deal-title" title="${escHtml(d.title || "")}">${escHtml(d.title || "No title")}</div>
          <div class="deal-meta">
            ${d.year ? `<strong>${escHtml(d.year)}</strong> · ` : ""}
            ${d.mileage ? `${escHtml(d.mileage)} · ` : ""}
            ${d.location ? escHtml(d.location) : ""}
          </div>
          <div class="deal-price">${escHtml(d.price || "Price N/A")}</div>
          <div class="deal-actions">
            <span class="deal-score-pill ${scoreBadgeClass(d.score ?? 0)}" style="font-size:10px">
              ${isHot ? "🔥" : "📊"} Score: ${d.score ?? "?"}/100
            </span>
            ${d.listing_url
              ? `<a href="${escHtml(d.listing_url)}" target="_blank" class="btn btn-sm btn-primary" style="font-size:10px;padding:2px 7px">View</a>`
              : ""}
          </div>
        </div>
      </div>`;
  }).join("");
}

function escHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// ─── Refresh stats (Tools tab) ────────────────────────────────────────────────
function refreshStats() {
  const priced   = allDeals.filter(d => d.priceNum != null && d.priceNum > 0);
  const hotCount = allDeals.filter(d => (d.score ?? 0) >= (currentPrefs.dealScoreThreshold ?? 60)).length;
  const avgPrice = priced.length ? Math.round(priced.reduce((s, d) => s + d.priceNum, 0) / priced.length) : null;
  const minPrice = priced.length ? Math.min(...priced.map(d => d.priceNum)) : null;
  const maxPrice = priced.length ? Math.max(...priced.map(d => d.priceNum)) : null;
  const avgScore = allDeals.length ? Math.round(allDeals.reduce((s, d) => s + (d.score ?? 0), 0) / allDeals.length) : null;

  $("stat-count").textContent     = allDeals.length;
  $("stat-avg").textContent       = avgPrice != null ? fmt(avgPrice) : "–";
  $("stat-min").textContent       = minPrice != null ? fmt(minPrice) : "–";
  $("stat-max").textContent       = maxPrice != null ? fmt(maxPrice) : "–";
  $("stat-avg-score").textContent = avgScore != null ? `${avgScore}/100` : "–";
  $("stat-hot").textContent       = hotCount;

  // Price drop tracker
  refreshPriceDrops();
}

function refreshPriceDrops() {
  // TODO: Implement full historical price tracking by persisting a priceHistory
  // map (listingId → [{price, timestamp}]) in chrome.storage.  For now, use a
  // heuristic: flag listings whose title text mentions a price reduction.
  const drops = allDeals.filter(d =>
    /reduced|price drop|lower|was \$/i.test(d.title || "")
  );
  const container = $("price-drops-list");
  if (!drops.length) {
    container.innerHTML = `<p class="empty-msg">No price drops detected yet.</p>`;
    return;
  }
  container.innerHTML = drops.map(d =>
    `<div style="font-size:11px;padding:3px 0;border-bottom:1px solid #f3f4f6">
       <strong>${escHtml(d.title)}</strong> — ${escHtml(d.price || "N/A")}
     </div>`
  ).join("");
}

// ─── Load prefs → populate filters ───────────────────────────────────────────
function populateFilters(prefs) {
  if (prefs.maxPrice   != null) $("f-max-price").value        = prefs.maxPrice;
  if (prefs.minYear    != null) $("f-min-year").value         = prefs.minYear;
  if (prefs.maxMileage != null) $("f-max-mileage").value      = prefs.maxMileage;
  $("f-keyword").value         = prefs.searchKeyword   || "";
  $("f-score-threshold").value = prefs.dealScoreThreshold ?? 60;
  $("f-scan-interval").value   = prefs.scanInterval    ?? 5;
  $("notif-toggle").checked    = prefs.notificationsEnabled !== false;
}

// ─── Status bar helpers ───────────────────────────────────────────────────────
function setStatus(msg) { $("status-text").textContent = msg; }
function updateAutoScanUI(enabled) {
  const btn  = $("btn-auto");
  const badge = $("scan-badge");
  if (enabled) {
    btn.textContent = "Stop Auto";
    btn.classList.add("btn-active");
    badge.classList.remove("hidden");
  } else {
    btn.textContent = "Auto";
    btn.classList.remove("btn-active");
    badge.classList.add("hidden");
  }
}

// ─── Init ─────────────────────────────────────────────────────────────────────
async function init() {
  try {
    const [dealResp, prefResp] = await Promise.all([
      sendMsg("GET_DEALS"),
      sendMsg("GET_PREFS"),
    ]);

    allDeals     = dealResp.deals   || [];
    currentPrefs = prefResp.prefs   || {};

    populateFilters(currentPrefs);
    updateAutoScanUI(currentPrefs.autoScanEnabled);
    renderDeals();

    setStatus(`${allDeals.length} deal(s) stored · ${new Date().toLocaleTimeString()}`);
  } catch (err) {
    setStatus("Error loading data.");
    console.error("[FB Deal Finder popup]", err);
  }
}

init();

// ─── Event Listeners ──────────────────────────────────────────────────────────

// Scan now
$("btn-scan").addEventListener("click", async () => {
  $("btn-scan").textContent = "…";
  $("btn-scan").disabled = true;
  try {
    await sendMsg("TRIGGER_SCAN");
    setStatus("Scan triggered — check Marketplace tab.");
    // Wait ~3 s for the content script to parse the page and send LISTINGS_FOUND
    // to the background, which then stores deals — then refresh the popup list.
    setTimeout(async () => {
      const resp = await sendMsg("GET_DEALS");
      allDeals = resp.deals || [];
      renderDeals();
      setStatus(`${allDeals.length} deal(s) stored · ${new Date().toLocaleTimeString()}`);
    }, 3000);
  } finally {
    $("btn-scan").textContent = "⟳ Scan";
    $("btn-scan").disabled = false;
  }
});

// Toggle auto-scan
$("btn-auto").addEventListener("click", async () => {
  const resp = await sendMsg("TOGGLE_AUTO_SCAN");
  currentPrefs.autoScanEnabled = resp.autoScanEnabled;
  updateAutoScanUI(resp.autoScanEnabled);
  setStatus(resp.autoScanEnabled ? "Auto-scan enabled." : "Auto-scan stopped.");
});

// Sort / min score
$("sort-select").addEventListener("change",    renderDeals);
$("min-score-input").addEventListener("input", renderDeals);

// Clear deals
$("btn-clear-deals").addEventListener("click", async () => {
  if (!confirm("Clear all stored deals?")) return;
  await sendMsg("CLEAR_DEALS");
  allDeals = [];
  renderDeals();
  setStatus("Deals cleared.");
});

// Save filters
$("btn-save-filters").addEventListener("click", async () => {
  const prefs = {
    maxPrice:            parseInt($("f-max-price").value) || null,
    minYear:             parseInt($("f-min-year").value)  || null,
    maxMileage:          parseInt($("f-max-mileage").value) || null,
    searchKeyword:       $("f-keyword").value.trim(),
    dealScoreThreshold:  parseInt($("f-score-threshold").value) || 60,
    scanInterval:        parseInt($("f-scan-interval").value) || 5,
    notificationsEnabled: $("notif-toggle").checked,
  };
  await sendMsg("SAVE_PREFS", { prefs });
  currentPrefs = { ...currentPrefs, ...prefs };
  $("filter-saved-msg").classList.remove("hidden");
  setTimeout(() => $("filter-saved-msg").classList.add("hidden"), 2000);
});

// Reset filters
$("btn-reset-filters").addEventListener("click", () => {
  $("f-max-price").value        = "";
  $("f-min-year").value         = "";
  $("f-max-mileage").value      = "";
  $("f-keyword").value          = "";
  $("f-score-threshold").value  = "60";
  $("f-scan-interval").value    = "5";
});

// ── Notifications toggle ──────────────────────────────────────────────────────
$("notif-toggle").addEventListener("change", async () => {
  await sendMsg("SAVE_PREFS", { prefs: { notificationsEnabled: $("notif-toggle").checked } });
});

// ── Deal Score Calculator ─────────────────────────────────────────────────────
$("btn-calc-score").addEventListener("click", () => {
  const price   = parseFloat($("calc-price").value)   || null;
  const year    = parseInt($("calc-year").value, 10)   || null;
  const mileage = parseInt($("calc-mileage").value, 10) || null;
  const score   = computeDealScore(price, year, mileage);

  const el = $("calc-result");
  let label, colour;
  if (score >= 80)      { label = "🔥 Hot Deal!";    colour = "#16a34a"; }
  else if (score >= 60) { label = "✅ Good Deal";    colour = "#2563eb"; }
  else if (score >= 40) { label = "⚠ Fair Deal";    colour = "#ca8a04"; }
  else                  { label = "❌ Below Average"; colour = "#dc2626"; }

  el.style.background = colour + "1a";
  el.style.color      = colour;
  el.style.border     = `1px solid ${colour}44`;
  el.textContent      = `${label} — Score: ${score}/100`;
  el.classList.remove("hidden");
});

// ── Export to CSV ─────────────────────────────────────────────────────────────
$("btn-export-csv").addEventListener("click", () => {
  if (!allDeals.length) { alert("No deals to export."); return; }

  const headers = ["listing_id","title","price","priceNum","year","mileage","location","score","listing_url","foundAt"];
  const rows = allDeals.map(d =>
    headers.map(h => {
      const val = d[h] ?? "";
      const str = String(val).replace(/"/g, '""');
      return `"${str}"`;
    }).join(",")
  );
  const csv     = [headers.join(","), ...rows].join("\n");
  const blob    = new Blob([csv], { type: "text/csv" });
  const url     = URL.createObjectURL(blob);
  const a       = document.createElement("a");
  a.href        = url;
  a.download    = `fb-car-deals-${new Date().toISOString().slice(0,10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
});

// ── Open Marketplace ─────────────────────────────────────────────────────────
$("btn-open-marketplace").addEventListener("click", () => {
  const category = $("open-category").value;
  const location = $("open-location").value.trim() || "category";
  const base     = location === "category"
    ? `https://www.facebook.com/marketplace/category/${category}`
    : `https://www.facebook.com/marketplace/${location}/${category}`;

  const params = new URLSearchParams();
  if (currentPrefs.maxPrice)    params.set("maxPrice",   currentPrefs.maxPrice);
  if (currentPrefs.minYear)     params.set("minYear",    currentPrefs.minYear);
  if (currentPrefs.maxMileage)  params.set("maxMileage", currentPrefs.maxMileage);
  if (currentPrefs.searchKeyword) params.set("query",   currentPrefs.searchKeyword);

  const url = params.toString() ? `${base}/?${params}` : base;
  chrome.tabs.create({ url });
});

// ── Compare Deals ─────────────────────────────────────────────────────────────
$("btn-compare").addEventListener("click", () => {
  const ids = Array.from(document.querySelectorAll(".compare-id-input"))
    .map(i => i.value.trim()).filter(Boolean);

  if (!ids.length) { alert("Enter at least one listing ID."); return; }

  const picks = ids.map(id => allDeals.find(d => d.listing_id === id)).filter(Boolean);
  if (!picks.length) { alert("No matching deals found. Make sure the IDs match stored deals."); return; }

  const el = $("compare-result");
  const rows = picks.map(d =>
    `<tr>
       <td>${escHtml(d.title || "–")}</td>
       <td>${escHtml(d.price || "–")}</td>
       <td>${escHtml(d.year || "–")}</td>
       <td>${escHtml(d.mileage || "–")}</td>
       <td><span class="deal-score-pill ${scoreBadgeClass(d.score ?? 0)}">${d.score ?? "?"}/100</span></td>
       <td>${d.listing_url ? `<a href="${escHtml(d.listing_url)}" target="_blank" class="btn btn-xs btn-primary">View</a>` : "–"}</td>
     </tr>`
  ).join("");

  el.innerHTML = `
    <table class="compare-table">
      <thead><tr><th>Title</th><th>Price</th><th>Year</th><th>Mileage</th><th>Score</th><th></th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
  el.classList.remove("hidden");
});
