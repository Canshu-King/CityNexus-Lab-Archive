/**
 * V19.2.2 focused mobile trial probe.
 *
 * Two mandated viewports (390x844, 430x932) and the trial-critical flows:
 *   - C4 anchored journey
 *   - stale evidence warning
 *   - mid-trip HARD recovery panel
 *   - GPS allowed / denied
 *
 * Also asserts no horizontal overflow and no uncaught page errors.
 */

const { chromium } = require("playwright");
const fs = require("fs");

const BASE = process.env.WEB_BASE || "http://127.0.0.1:4214";
const API = process.env.API_BASE || "http://127.0.0.1:8070";
const OUT = process.env.OUT_PATH || "evidence/mobile_probe_d.json";

const VIEWPORTS = [
  { name: "390x844", width: 390, height: 844, mobile: true },
  { name: "430x932", width: 430, height: 932, mobile: true },
];

async function api(path, init) {
  const response = await fetch(API + "/api/v1" + path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  let body = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  return { status: response.status, body };
}

const resetDemo = () => api("/demo/reset", { method: "POST" });
