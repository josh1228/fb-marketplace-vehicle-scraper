/**
 * Options Page Script – FB Marketplace Car Deal Finder
 */

"use strict";

const STORAGE_PREFS_KEY = "fb_prefs";
const STORAGE_DEALS_KEY = "fb_deals";
const STORAGE_SEEN_KEY  = "fb_seen_ids";

const DEFAULT_PREFS = {
  scanInterval:        5,
  autoScanEnabled:     false,
  dealScoreThreshold:  60,
  maxStoredDeals:      200,
  notificationsEnabled: true,
  maxPrice:            null,
  minYear:             null,
  maxMileage:          null,
  searchKeyword:       "",
};

const $ = id => document.getElementById(id);

async function loadPrefs() {
  const { fb_prefs = {} } = await chrome.storage.local.get(STORAGE_PREFS_KEY);
  return { ...DEFAULT_PREFS, ...fb_prefs };
}

async function savePrefs(prefs) {
  await chrome.storage.local.set({ [STORAGE_PREFS_KEY]: prefs });
  // Update alarm state via background
  chrome.runtime.sendMessage({ type: "SAVE_PREFS", prefs });
}

function populateForm(prefs) {
  $("auto-scan-enabled").checked      = prefs.autoScanEnabled;
  $("scan-interval").value            = prefs.scanInterval ?? 5;
  $("score-threshold").value          = prefs.dealScoreThreshold ?? 60;
  $("max-stored-deals").value         = prefs.maxStoredDeals ?? 200;
  $("notifications-enabled").checked  = prefs.notificationsEnabled !== false;
  $("max-price").value                = prefs.maxPrice    ?? "";
  $("min-year").value                 = prefs.minYear     ?? "";
  $("max-mileage").value              = prefs.maxMileage  ?? "";
  $("search-keyword").value           = prefs.searchKeyword ?? "";
}

function readForm() {
  return {
    autoScanEnabled:     $("auto-scan-enabled").checked,
    scanInterval:        parseInt($("scan-interval").value, 10)     || 5,
    dealScoreThreshold:  parseInt($("score-threshold").value, 10)   || 60,
    maxStoredDeals:      parseInt($("max-stored-deals").value, 10)  || 200,
    notificationsEnabled: $("notifications-enabled").checked,
    maxPrice:            parseInt($("max-price").value, 10)    || null,
    minYear:             parseInt($("min-year").value, 10)     || null,
    maxMileage:          parseInt($("max-mileage").value, 10)  || null,
    searchKeyword:       $("search-keyword").value.trim(),
  };
}

// Init
(async () => {
  const prefs = await loadPrefs();
  populateForm(prefs);
})();

// Save
$("btn-save").addEventListener("click", async () => {
  const prefs = readForm();
  await savePrefs(prefs);
  $("save-msg").classList.remove("hidden");
  setTimeout(() => $("save-msg").classList.add("hidden"), 2500);
});

// Reset
$("btn-reset").addEventListener("click", async () => {
  if (!confirm("Reset all settings to defaults?")) return;
  await savePrefs(DEFAULT_PREFS);
  populateForm(DEFAULT_PREFS);
});

// Clear deals
$("btn-clear").addEventListener("click", async () => {
  if (!confirm("Delete all stored deals and seen-IDs? This cannot be undone.")) return;
  await chrome.storage.local.remove([STORAGE_DEALS_KEY, STORAGE_SEEN_KEY]);
  alert("All stored deals cleared.");
});
