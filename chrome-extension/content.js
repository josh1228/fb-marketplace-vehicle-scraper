/**
 * Content Script – FB Marketplace Car Deal Finder
 *
 * Runs on every https://www.facebook.com/marketplace/* page.
 * scoring.js is injected before this file (see manifest.json), making
 * `computeDealScore` available as a global.
 *
 * Responsibilities:
 *  - Parse vehicle listing cards from the DOM
 *  - Send parsed listings to the background service worker
 *  - Inject deal-score badges onto each card
 *  - Highlight "hot deal" cards visually
 *  - Respond to SCAN_NOW messages from the background worker
 *  - Observe DOM mutations so newly loaded cards are also processed
 */

(function () {
  "use strict";

  // ─── Helpers ────────────────────────────────────────────────────────────────
  const BADGE_ATTR = "data-fb-deal-score";

  /** Extract the numeric price from a price string like "$12,500". */
  function parsePrice(str) {
    if (!str) return null;
    const m = str.replace(/,/g, "").match(/\$?([\d]+)/);
    return m ? parseInt(m[1], 10) : null;
  }

  /** Return a colour for the score badge. */
  function scoreColour(score) {
    if (score >= 80) return "#16a34a";  // green
    if (score >= 60) return "#ca8a04";  // amber
    if (score >= 40) return "#ea580c";  // orange
    return "#dc2626";                   // red
  }

  /** Parse a single listing card element into a plain object. */
  function parseCard(card) {
    try {
      // Title
      let title = "";
      const ariaEl = card.querySelector("[aria-label]");
      if (ariaEl) title = ariaEl.getAttribute("aria-label");
      if (!title) {
        const span = card.querySelector("span");
        title = span ? span.textContent.trim() : "Unknown";
      }

      // Price
      let price = null;
      const allText = card.textContent || "";
      const priceMatch = allText.match(/\$[\d,]+/);
      if (priceMatch) price = priceMatch[0];

      // Location – match "City, ST" (US city/state format, ≤50 chars to avoid
      // false positives from longer description strings).
      let location = null;
      const spans = card.querySelectorAll("span");
      for (const s of spans) {
        const t = s.textContent.trim();
        if (/^[A-Za-z ]+,\s*[A-Z]{2}$/.test(t) && t.length < 50) {
          location = t;
          break;
        }
      }

      // Image
      const img = card.querySelector("img");
      const image_url = img ? (img.src || img.getAttribute("data-src") || null) : null;

      // Listing URL & ID
      let listing_url = null;
      let listing_id  = null;
      const link = card.querySelector("a[href*='/marketplace/item/']") ||
                   card.closest("a[href*='/marketplace/item/']");
      if (link) {
        let href = link.getAttribute("href");
        if (href && !href.startsWith("http")) href = `https://www.facebook.com${href}`;
        listing_url = href;
        const m = (href || "").match(/\/item\/(\d+)/);
        if (m) listing_id = m[1];
      }

      // Year
      const yearMatch = (title + " " + allText).match(/\b(19|20)\d{2}\b/);
      const year = yearMatch ? yearMatch[0] : null;

      // Mileage
      const mileMatch = allText.replace(/,/g, "").match(/([\d]+)\s*(?:mi|mile|miles|k mi)/i);
      const mileage = mileMatch ? mileMatch[0] : null;

      const priceNum   = parsePrice(price);
      const yearNum    = year ? parseInt(year, 10) : null;
      const mileNum    = mileage ? parseInt(mileMatch[1], 10) : null;

      // computeDealScore is provided by scoring.js, loaded before this file
      const score = computeDealScore(priceNum, yearNum, mileNum);

      return {
        listing_id,
        title,
        price,
        location,
        year,
        mileage,
        image_url,
        listing_url,
        score,
        foundAt: Date.now(),
      };
    } catch (_) {
      return null;
    }
  }

  /** Inject a deal-score badge into a listing card. */
  function injectBadge(card, listing) {
    if (card.getAttribute(BADGE_ATTR)) return; // already done
    card.setAttribute(BADGE_ATTR, listing.score);

    const badge = document.createElement("div");
    badge.className = "fb-deal-badge";
    badge.style.cssText = `
      position:absolute;top:8px;left:8px;z-index:9999;
      background:${scoreColour(listing.score)};
      color:#fff;font-size:11px;font-weight:700;
      padding:3px 7px;border-radius:12px;
      box-shadow:0 1px 4px rgba(0,0,0,.4);
      pointer-events:none;white-space:nowrap;
    `;
    badge.textContent = `Deal: ${listing.score}/100`;

    // Ensure the card is relatively positioned so the badge stacks correctly
    const pos = getComputedStyle(card).position;
    if (pos === "static") card.style.position = "relative";

    card.appendChild(badge);

    // Add a glowing border for hot deals (score ≥ 70)
    if (listing.score >= 70) {
      card.style.outline = `2px solid ${scoreColour(listing.score)}`;
      card.style.outlineOffset = "2px";
    }
  }

  // ─── Core scan function ─────────────────────────────────────────────────────
  function scan() {
    // Collect all listing card candidates
    let cards = Array.from(
      document.querySelectorAll("[data-testid*='marketplace'], [data-testid*='listing']")
    );
    if (!cards.length) {
      // Fallback: parent divs of marketplace item links
      const links = Array.from(
        document.querySelectorAll("a[href*='/marketplace/item/']")
      );
      const parents = links.map(l => l.closest("div[style]") || l.parentElement).filter(Boolean);
      cards = [...new Set(parents)];
    }
    if (!cards.length) {
      // Second fallback: any direct parent of a marketplace link
      cards = Array.from(
        document.querySelectorAll("a[href*='/marketplace/item/']")
      ).map(a => a.parentElement).filter(Boolean);
      cards = [...new Set(cards)];
    }

    const listings = [];
    for (const card of cards) {
      const listing = parseCard(card);
      if (listing && listing.listing_id) {
        injectBadge(card, listing);
        listings.push(listing);
      }
    }

    if (listings.length > 0) {
      chrome.runtime.sendMessage({ type: "LISTINGS_FOUND", listings });
      console.log(`[FB Deal Finder] Sent ${listings.length} listings to background.`);
    }

    return listings.length;
  }

  // ─── DOM mutation observer ──────────────────────────────────────────────────
  let scanTimeout = null;
  const observer = new MutationObserver(() => {
    // Debounce: wait 800 ms after the last DOM change before scanning.
    // Facebook Marketplace performs many rapid DOM mutations during scroll/load;
    // debouncing avoids triggering hundreds of redundant scans.
    clearTimeout(scanTimeout);
    scanTimeout = setTimeout(scan, 800);
  });

  observer.observe(document.body, { childList: true, subtree: true });

  // Delay the initial scan by 1500 ms to allow Facebook's React app to finish
  // its first render cycle and populate listing cards into the DOM.
  setTimeout(scan, 1500);

  // ─── Message listener (from background.js) ─────────────────────────────────
  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message.type === "SCAN_NOW") {
      const count = scan();
      sendResponse({ ok: true, count });
    }
    return false;
  });

  console.log("[FB Deal Finder] Content script loaded on", window.location.href);
})();

