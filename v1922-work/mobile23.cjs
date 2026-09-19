/**
 * V19.2.3 focused mobile trial probe.
 *
 * Viewports: 390x844 and 430x932 only.
 * Flows: ARRIVAL boundary, DEPARTURE boundary, mid-trip HARD recovery,
 * governed acknowledgement, feasible replacement resolves recovery,
 * no-alternative state, stale candidate warning, GPS allowed/denied.
 */

const { createRequire } = require("node:module");
const req = createRequire(
  "D:/moodle/_v1922_work/redteam/CityNexus-V19.2-RealPhone-Trial-Gate-20260915/snapshot_d/frontend/package.json",
);
const { chromium } = req("@playwright/test");
const fs = require("fs");

const BASE = process.env.WEB_BASE || "http://127.0.0.1:4214";
const API = process.env.API_BASE || "http://127.0.0.1:8000";
const OUT = process.env.OUT_PATH || "evidence/mobile_v1923_d.json";
const JID = "22222222-2222-4222-8222-222222222222";
const DAY = "2026-10-10";
const TZ = "+08:00";

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

function c4Reservation(role, ref, arrival, departure, node) {
  const reservation = {
    reservation_type: "RAIL",
    confirmation_ref: ref,
    origin: { name: "Shanghai Hongqiao", code: "SHH" },
    destination: { name: "Nexus City", code: "CNX" },
    scheduled_departure_at: departure,
    scheduled_arrival_at: arrival,
    anchor_role: role,
    provider_key: "mock-rail",
    price_amount_minor: 128000,
    currency: "CNY",
  };
  if (node) reservation.semantic_node_key = node;
  return reservation;
}

async function addAnchor(role, ref, arrival, departure, node) {
  const imported = await api(`/journeys/${JID}/inbox/import`, {
    method: "POST",
    body: JSON.stringify({
      artifact_type: "STRUCTURED_JSON",
      payload: { reservation: c4Reservation(role, ref, arrival, departure, node) },
    }),
  });
  const draftId = imported.body && imported.body.id;
  return draftId
    ? api(`/journeys/${JID}/inbox/${draftId}/confirm`, { method: "POST" })
    : { status: imported.status };
}

async function selectFirst() {
  const plans = await api(`/journeys/${JID}/plans`);
  const list = Array.isArray(plans.body) ? plans.body : [];
  if (!list.length) return { list, select: { status: null }, start: { status: null } };
  const select = await api(`/journeys/${JID}/plans/${list[0].id}/select`, { method: "POST" });
  const start = await api(`/journeys/${JID}/start`, { method: "POST" });
  return { list, select, start };
}

async function openRoute(page, path) {
  await page.addInitScript(() => {
    window.localStorage.setItem(
      "citynexus.v8.journey_id",
      "22222222-2222-4222-8222-222222222222",
    );
  });
  await page.goto(BASE + path, { waitUntil: "networkidle", timeout: 45000 });
  await page.waitForTimeout(1600);
}
