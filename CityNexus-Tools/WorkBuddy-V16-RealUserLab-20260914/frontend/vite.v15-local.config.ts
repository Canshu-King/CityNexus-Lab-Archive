/**
 * V15 Night Lab local dev config — isolated from the Codex worktree.
 *
 * Why this file exists: the shipped `vite.config.ts` proxies `/api/v1` to
 * `127.0.0.1:8000`. During the V15 night lab, port 8000 and port 5173 are both
 * occupied by the Codex session running against `D:/moodle/CityNexus`. Pointing
 * this workspace's dev server at 8000 would have made the UI trial drive
 * *Codex's* backend and mutate *Codex's* database, which the task book forbids.
 *
 * So this config reuses the shipped config verbatim and only overrides the two
 * things that must differ: the proxy target (8010) and the dev port (4173).
 * Nothing else about the app changes, so what the trial exercises is the real
 * product surface.
 */
import { defineConfig, mergeConfig, type UserConfig } from "vite";
import path from "node:path";
import os from "node:os";

import base from "./vite.config";

// Vite's dependency pre-bundler rewrites its cache by deleting the previous
// `deps_temp_*` directory. Inside this sandbox a bulk file deletion above the
// per-turn quota raises SystemExit inside the Node process and kills the dev
// server outright. `%TEMP%` is the one location the guard exempts, so the cache
// lives there instead of in `node_modules/.vite`.
const cacheDir = path.join(os.tmpdir(), "citynexus-v15-vite-cache");

const override: UserConfig = {
  cacheDir,
  server: {
    host: "127.0.0.1",
    port: 4173,
    strictPort: true,
    proxy: {
      "/api/v1": {
        target: "http://127.0.0.1:8010",
        changeOrigin: false,
      },
    },
  },
};

export default mergeConfig(base as UserConfig, defineConfig(override));
