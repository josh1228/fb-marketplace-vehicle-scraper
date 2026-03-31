/**
 * scoring.js – Shared deal-scoring logic
 *
 * Loaded as a classic script in three contexts:
 *   1. Background service worker (via importScripts)
 *   2. Content scripts (listed before content.js in manifest)
 *   3. Popup page (via <script src> before popup.js)
 *
 * Assigns computeDealScore to `self` so it is available globally in every
 * context without relying on ES module import/export.
 *
 * Scoring breakdown (0–100 scale, higher = better deal):
 *   - Base score: 50
 *   - Price component:   ±30 pts
 *   - Year  component:   ±15 pts
 *   - Mileage component: ±15 pts
 */

/* global self */
self.computeDealScore = function computeDealScore(priceNum, yearNum, mileageNum) {
  let score = 50; // neutral baseline
  const currentYear = new Date().getFullYear();

  // ── Price component (max ±30 pts) ─────────────────────────────────────────
  if (priceNum != null && priceNum > 0) {
    if      (priceNum < 3000)  score += 30;
    else if (priceNum < 6000)  score += 20;
    else if (priceNum < 10000) score += 10;
    else if (priceNum < 15000) score +=  5;
    else if (priceNum < 25000) score -=  5;
    else if (priceNum < 40000) score -= 15;
    else                       score -= 25;
  }

  // ── Year component (max ±15 pts) ──────────────────────────────────────────
  if (yearNum != null) {
    const age = currentYear - yearNum;
    if      (age <= 2)  score += 15;
    else if (age <= 5)  score += 10;
    else if (age <= 10) score +=  5;
    else if (age <= 15) score -=  5;
    else if (age <= 20) score -= 10;
    else                score -= 15;
  }

  // ── Mileage component (max ±15 pts) ───────────────────────────────────────
  if (mileageNum != null) {
    if      (mileageNum < 20000)  score += 15;
    else if (mileageNum < 50000)  score += 10;
    else if (mileageNum < 80000)  score +=  5;
    else if (mileageNum < 120000) score -=  5;
    else if (mileageNum < 180000) score -= 10;
    else                          score -= 15;
  }

  return Math.max(0, Math.min(100, Math.round(score)));
};
