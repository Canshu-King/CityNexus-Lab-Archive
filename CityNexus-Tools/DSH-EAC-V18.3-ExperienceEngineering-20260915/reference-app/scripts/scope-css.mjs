import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

/**
 * V18.3 design-system isolation:
 * - tokens.css stays global (namespaced --cn-* variables).
 * - global.css keeps only document-level rules.
 * - app.css becomes experience.css wrapped in @scope(.citynexus-experience).
 *
 * Run: node scripts/scope-css.mjs
 */
const root = new URL("../src/styles/", import.meta.url);
const source = await readFile(new URL("app.css", root), "utf8");
const scoped = `/* AUTO-GENERATED from app.css by scripts/scope-css.mjs. Do not edit directly. */\n@scope (.citynexus-experience) {\n${source}\n}\n`;
await writeFile(new URL("experience.css", root), scoped, "utf8");
console.log("wrote experience.css scoped to .citynexus-experience");
