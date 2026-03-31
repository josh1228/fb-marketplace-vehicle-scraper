/**
 * Background Service Worker – FB Marketplace Car Deal Finder
 *
 * Responsibilities:
 *  - Manage auto-scan alarms via chrome.alarms
 *  - Aggregate deal listings from content-script messages
 *  - Score each listing and flag "hot deals"
 *  - Fire browser notifications for newly discovered hot deals
 *  - Provide storage helpers used by popup and options pages
 */

// Load shared scoring utility (classic service worker – importScripts is available)
importScripts("scoring.js");

// ─── Constants ────────────────────────────────────────────────────────────────
const ALARM_NAME        = "auto-scan";
const STORAGE_DEALS_KEY = "fb_deals";
const STORAGE_SEEN_KEY  = "fb_seen_ids";
const STORAGE_PREFS_KEY = "fb_prefs";

// Default user preferences
const DEFAULT_PREFS = {
  scanInterval:       5,          // minutes between scans
  autoScanEnabled:    false,
  dealScoreThreshold: 60,         // 0-100; listings above this are "hot"
  maxStoredDeals:     200,
  notificationsEnabled: true,
  maxPrice:           null,
  minYear:            null,
  maxMileage:         null,
  searchKeyword:      "",
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
async function getPrefs() {
  const { fb_prefs = {} } = await chrome.storage.local.get(STORAGE_PREFS_KEY);
  return { ...DEFAULT_PREFS, ...fb_prefs };
}

async function getStoredDeals() {
  const { fb_deals = [] } = await chrome.storage.local.get(STORAGE_DEALS_KEY);
  return fb_deals;
}

async function getSeenIds() {
  const { fb_seen_ids = [] } = await chrome.storage.local.get(STORAGE_SEEN_KEY);
  return new Set(fb_seen_ids);
}

/**
 * Score a listing on a 0-100 scale using the shared computeDealScore utility.
 * Higher score = better deal.
 */
function scoreListing(listing) {
  return computeDealScore(listing.priceNum, listing.yearNum, listing.mileageNum);
}

/**
 * Enrich a raw listing (as sent by content.js) with numeric fields and score.
 */
function enrichListing(raw) {
  // Parse price string like "$12,500" → 12500
  const priceMatch = (raw.price || "").replace(/,/g, "").match(/\$?([\d]+)/);
  const priceNum   = priceMatch ? parseInt(priceMatch[1], 10) : null;

  // Parse year
  const yearMatch = (raw.year || raw.title || "").match(/\b(19|20)\d{2}\b/);
  const yearNum   = yearMatch ? parseInt(yearMatch[0], 10) : null;

  // Parse mileage string like "45,000 miles" → 45000
  const mileMatch = (raw.mileage || raw.title || "").replace(/,/g, "").match(/([\d]+)\s*(?:mi|mile)/i);
  const mileageNum = mileMatch ? parseInt(mileMatch[1], 10) : null;

  const enriched = {
    ...raw,
    priceNum,
    yearNum,
    mileageNum,
    foundAt: raw.foundAt || Date.now(),
  };
  enriched.score = scoreListing(enriched);
  return enriched;
}

/**
 * Merge new listings into storage; return count of newly discovered hot deals.
 */
async function mergeListings(newListings) {
  const prefs    = await getPrefs();
  const existing = await getStoredDeals();
  const seenIds  = await getSeenIds();

  const hotNewDeals = [];
  const existingMap = new Map(existing.map(d => [d.listing_id, d]));

  for (const raw of newListings) {
    const listing = enrichListing(raw);
    if (!listing.listing_id) continue;

    const isNew = !seenIds.has(listing.listing_id);
    existingMap.set(listing.listing_id, listing);
    seenIds.add(listing.listing_id);

    if (isNew && listing.score >= prefs.dealScoreThreshold) {
      hotNewDeals.push(listing);
    }
  }

  // Keep most recent deals up to the cap
  const merged = Array.from(existingMap.values())
    .sort((a, b) => b.foundAt - a.foundAt)
    .slice(0, prefs.maxStoredDeals);

  await chrome.storage.local.set({
    [STORAGE_DEALS_KEY]: merged,
    [STORAGE_SEEN_KEY]:  [...seenIds],
  });

  return hotNewDeals;
}

/**
 * Fire a Chrome notification for a hot deal.
 */
function notifyHotDeal(listing) {
  const title = listing.title || "Great Deal Found!";
  const price = listing.price  || "Check it out";
  chrome.notifications.create(`deal-${listing.listing_id}`, {
    type:    "basic",
    iconUrl: "icons/icon48.png",
    title:   `🔥 Hot Deal: ${title}`,
    message: `${price} — Score: ${listing.score}/100\nClick to view on Facebook Marketplace`,
    buttons: [{ title: "View Listing" }],
    priority: 2,
  });
}

/**
 * Trigger a scan by injecting / messaging content script on any open
 * Facebook Marketplace tab.  If no such tab exists, open one.
 */
async function triggerScan() {
  const prefs = await getPrefs();
  const tabs = await chrome.tabs.query({
    url: "https://www.facebook.com/marketplace/*",
  });

  if (tabs.length > 0) {
    // Ask each matching tab to scan
    for (const tab of tabs) {
      chrome.tabs.sendMessage(tab.id, { type: "SCAN_NOW" }).catch(() => {});
    }
  } else {
    // Build the marketplace URL with optional filters
    const params = new URLSearchParams();
    if (prefs.maxPrice)    params.set("maxPrice",    prefs.maxPrice);
    if (prefs.minYear)     params.set("minYear",     prefs.minYear);
    if (prefs.maxMileage)  params.set("maxMileage",  prefs.maxMileage);
    if (prefs.searchKeyword) params.set("query",     prefs.searchKeyword);

    const base = "https://www.facebook.com/marketplace/category/cars-trucks";
    const url  = params.toString() ? `${base}/?${params}` : base;
    chrome.tabs.create({ url, active: false }); // open in background so it doesn't interrupt the user
  }
}

// ─── Alarm Management ─────────────────────────────────────────────────────────
async function startAutoScan() {
  const prefs = await getPrefs();
  await chrome.alarms.clear(ALARM_NAME);
  chrome.alarms.create(ALARM_NAME, {
    delayInMinutes:  prefs.scanInterval,
    periodInMinutes: prefs.scanInterval,
  });
}

async function stopAutoScan() {
  await chrome.alarms.clear(ALARM_NAME);
}

// ─── Event Listeners ──────────────────────────────────────────────────────────
chrome.runtime.onInstalled.addListener(async () => {
  // Ensure prefs are initialised
  const existing = await chrome.storage.local.get(STORAGE_PREFS_KEY);
  if (!existing[STORAGE_PREFS_KEY]) {
    await chrome.storage.local.set({ [STORAGE_PREFS_KEY]: DEFAULT_PREFS });
  }
  console.log("[FB Deal Finder] Extension installed / updated.");
});

chrome.alarms.onAlarm.addListener(async alarm => {
  if (alarm.name === ALARM_NAME) {
    console.log("[FB Deal Finder] Auto-scan alarm fired.");
    await triggerScan();
  }
});

// Notification button click → open listing URL
chrome.notifications.onButtonClicked.addListener((notifId, btnIdx) => {
  if (btnIdx === 0 && notifId.startsWith("deal-")) {
    const listingId = notifId.replace("deal-", "");
    const url = `https://www.facebook.com/marketplace/item/${listingId}`;
    chrome.tabs.create({ url });
  }
  chrome.notifications.clear(notifId);
});

// ─── Message Handler (from content.js and popup.js) ──────────────────────────
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  switch (message.type) {
    // Content script sending scraped listings
    case "LISTINGS_FOUND": {
      (async () => {
        const hotDeals = await mergeListings(message.listings || []);
        const prefs    = await getPrefs();
        if (prefs.notificationsEnabled) {
          // Cap at 3 notifications per scan to avoid overwhelming the user;
          // remaining hot deals are still stored and visible in the popup.
          hotDeals.slice(0, 3).forEach(notifyHotDeal);
        }
        sendResponse({ ok: true, hotCount: hotDeals.length });
      })();
      return true; // async
    }

    // Popup requesting stored deals
    case "GET_DEALS": {
      (async () => {
        const deals = await getStoredDeals();
        sendResponse({ deals });
      })();
      return true;
    }

    // Popup requesting preferences
    case "GET_PREFS": {
      (async () => {
        const prefs = await getPrefs();
        sendResponse({ prefs });
      })();
      return true;
    }

    // Popup / options saving preferences
    case "SAVE_PREFS": {
      (async () => {
        const current = await getPrefs();
        const updated = { ...current, ...message.prefs };
        await chrome.storage.local.set({ [STORAGE_PREFS_KEY]: updated });

        if (updated.autoScanEnabled) {
          await startAutoScan();
        } else {
          await stopAutoScan();
        }
        sendResponse({ ok: true });
      })();
      return true;
    }

    // Popup requesting immediate scan
    case "TRIGGER_SCAN": {
      (async () => {
        await triggerScan();
        sendResponse({ ok: true });
      })();
      return true;
    }

    // Popup clearing all stored deals
    case "CLEAR_DEALS": {
      (async () => {
        await chrome.storage.local.remove([STORAGE_DEALS_KEY, STORAGE_SEEN_KEY]);
        sendResponse({ ok: true });
      })();
      return true;
    }

    // Toggle auto-scan on/off
    case "TOGGLE_AUTO_SCAN": {
      (async () => {
        const prefs = await getPrefs();
        const enabled = !prefs.autoScanEnabled;
        const updated = { ...prefs, autoScanEnabled: enabled };
        await chrome.storage.local.set({ [STORAGE_PREFS_KEY]: updated });
        if (enabled) {
          await startAutoScan();
        } else {
          await stopAutoScan();
        }
        sendResponse({ ok: true, autoScanEnabled: enabled });
      })();
      return true;
    }

    default:
      sendResponse({ error: "Unknown message type" });
  }
});
