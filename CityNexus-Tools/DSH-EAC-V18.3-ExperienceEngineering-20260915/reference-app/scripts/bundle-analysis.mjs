import { readFile, readdir, stat, writeFile } from "node:fs/promises";
import { gzipSync } from "node:zlib";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const dist = fileURLToPath(new URL("../dist/", import.meta.url));
const out = fileURLToPath(new URL("../../evidence/bundle_analysis.json", import.meta.url));

const BEFORE = {
  label: "V18.2 reference (single bundle, MapLibre in initial entry)",
  total_js_bytes: 1324790,
  total_js_gzip_bytes: 368690,
  css_bytes: 93350,
  css_gzip_bytes: 14960,
  initial_js_bytes: 1324790,
  initial_js_gzip_bytes: 368690,
  note: "MapLibre + React + app in the entry chunk; >500 kB warning.",
};

async function listFiles(dir) {
  const result = [];
  for (const entry of await readdir(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) result.push(...(await listFiles(full)));
    else result.push(full);
  }
  return result;
}

const files = await listFiles(dist);
const assets = [];
for (const file of files) {
  if (!/\.(js|css|html)$/.test(file)) continue;
  const data = await readFile(file);
  const gzip = gzipSync(data);
  assets.push({
    path: file.slice(dist.length).replaceAll("\\", "/"),
    bytes: data.byteLength,
    gzip_bytes: gzip.byteLength,
  });
}

const indexHtml = await readFile(join(dist, "index.html"), "utf8");
const initialAssets = [...indexHtml.matchAll(/(?:src|href)="\.?\/?([^"]+\.(?:js|css))"/g)].map((match) => match[1]);
const initial = assets.filter((asset) => initialAssets.some((name) => asset.path.endsWith(name)));
const jsAssets = assets.filter((asset) => asset.path.endsWith(".js"));
const cssAssets = assets.filter((asset) => asset.path.endsWith(".css"));
const sum = (items, key) => items.reduce((total, item) => total + item[key], 0);

const report = {
  generated_at: new Date().toISOString(),
  before: BEFORE,
  after: {
    label: "V18.3 lazy routes + dynamic MapLibre",
    total_js_bytes: sum(jsAssets, "bytes"),
    total_js_gzip_bytes: sum(jsAssets, "gzip_bytes"),
    css_bytes: sum(cssAssets, "bytes"),
    css_gzip_bytes: sum(cssAssets, "gzip_bytes"),
    initial_js_bytes: sum(initial.filter((asset) => asset.path.endsWith(".js")), "bytes"),
    initial_js_gzip_bytes: sum(initial.filter((asset) => asset.path.endsWith(".js")), "gzip_bytes"),
    initial_assets: initial.map((asset) => asset.path),
    chunks: assets.sort((a, b) => b.bytes - a.bytes),
  },
  delta: {
    initial_js_bytes_saved: BEFORE.initial_js_bytes - sum(initial.filter((asset) => asset.path.endsWith(".js")), "bytes"),
    initial_js_gzip_bytes_saved: BEFORE.initial_js_gzip_bytes - sum(initial.filter((asset) => asset.path.endsWith(".js")), "gzip_bytes"),
  },
  map_lazy_loaded: assets.some((asset) => asset.path.includes("maplibre")) && !initial.some((asset) => asset.path.includes("maplibre")),
};

await writeFile(out, JSON.stringify(report, null, 2) + "\n", "utf8");
console.log(JSON.stringify({ initial_js: report.after.initial_js_bytes, total_js: report.after.total_js_bytes, map_lazy_loaded: report.map_lazy_loaded }, null, 2));
