const { createRequire } = require("node:module");
const req = createRequire("D:/moodle/CityNexus/frontend/package.json");
const { chromium } = req("@playwright/test");
const fs = require("fs");
const BASE = "http://127.0.0.1:5173";
const API = "http://127.0.0.1:8000/api/v1";
const JID = "22222222-2222-4222-8222-222222222222";
const SHOTS = "D:/moodle/_v1922_work/rescue_evidence/shots";
const R = [];
const rec = (id, ok, note) => R.push({ id, ok, note: String(note).slice(0, 120) });
const errors = [];

async function newPage(browser, opts = {}) {
  const ctx = await browser.newContext({
    viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, ...opts,
  });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errors.push(String(e).slice(0, 150)));
  page.on("console", (m) => { if (m.type() === "error") errors.push("C:" + m.text().slice(0, 150)); });
  return { ctx, page };
}
const bind = (page) => page.addInitScript(() =>
  localStorage.setItem("citynexus.v8.journey_id", "22222222-2222-4222-8222-222222222222"));
