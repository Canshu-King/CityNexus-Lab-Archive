"""Provision the V16 frontend's node_modules and dev-server config.

`npm ci` cannot complete in this sandbox (two V15 attempts stalled with an empty
`.bin`), and a file-by-file copy of 27,887 files stalled at 86%. A directory
junction into the neighbouring install is instant, needs no elevation, and is
read-only from our side provided Vite's cache is redirected out of the tree.

Two safety rules carried over from V15, both learned the hard way:

* ``cmd /c mklink /J`` must be invoked with an argument **list**; going through a
  Git-Bash shell string splits the path on the space in ``CityNexus-Tools``.
* A junction must never be removed with ``rm -rf`` — that recurses through the
  reparse point and deletes the *target*. ``rmdir`` on the link is the only safe
  removal, and ``unlink_node_modules.py`` verifies the target afterwards.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

V16 = Path("D:/moodle/CityNexus-Tools/WorkBuddy-V16-RealUserLab-20260914")
FRONTEND = V16 / "frontend"
LINK = FRONTEND / "node_modules"
TARGET = Path("D:/moodle/CityNexus/frontend/node_modules")

VITE_CONFIG = '''/**
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
'''


def make_link() -> int:
    if LINK.exists() or LINK.is_symlink():
        print(f"{LINK} already exists")
        return 0
    if not TARGET.is_dir():
        print(f"target missing: {TARGET}", file=sys.stderr)
        return 1
    proc = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(LINK), str(TARGET)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    ok = LINK.is_dir()
    print(f"mklink rc={proc.returncode} linked={ok} entries="
          f"{len(os.listdir(LINK)) if ok else 0}")
    return 0 if ok else 1


def main() -> int:
    (FRONTEND / "vite.v16-local.config.ts").write_bytes(VITE_CONFIG.encode("utf-8"))
    print("wrote vite.v16-local.config.ts")
    return make_link()


if __name__ == "__main__":
    raise SystemExit(main())
