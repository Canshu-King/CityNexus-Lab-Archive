/**
 * V16 Real-User Lab dev config.
 *
 * The shipped `vite.config.ts` proxies `/api/v1` to `127.0.0.1:8000`, which is
 * the port Codex's own backend occupies. Pointing this workspace there would make
 * every UI simulation drive Codex's server and mutate Codex's database, so the
 * proxy target and dev port are the only two things overridden here. Everything
 * else comes from the shipped config, so the simulations exercise the real
 * product surface.
 *
 * `cacheDir` is moved to `%TEMP%` because Vite's dependency pre-bundler deletes
 * its previous `deps_temp_*` directory on startup. Inside this sandbox a bulk
 * deletion above the per-turn quota raises SystemExit inside Node and kills the
 * dev server outright; `%TEMP%` is the one location the guard exempts.
 */
import { defineConfig, mergeConfig, type UserConfig } from "vite";
import path from "node:path";
import os from "node:os";

import base from "./vite.config";

const override: UserConfig = {
  cacheDir: path.join(os.tmpdir(), "citynexus-v16-vite-cache"),
  server: {
    host: "127.0.0.1",
    port: 4173,
    strictPort: true,
    proxy: {
      "/api/v1": { target: "http://127.0.0.1:8010", changeOrigin: false },
    },
  },
};

export default mergeConfig(base as UserConfig, defineConfig(override));
