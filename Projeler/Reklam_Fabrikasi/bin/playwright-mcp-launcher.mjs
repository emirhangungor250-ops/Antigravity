#!/usr/bin/env node
// Cross-platform launcher for @playwright/mcp.
// Resolves the pinned CLI from this plugin's node_modules and spawns it
// with the same Node binary, so Windows users do not need a global install
// or Bash. Pinned to @playwright/mcp 0.0.41 because newer versions have
// broken Windows behavior at the time of writing.

import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const require = createRequire(import.meta.url);

// @playwright/mcp 0.0.41 does not export "./cli.js" via package.json
// `exports`, but it does ship `cli.js` next to its package.json and
// declares a `bin` entry pointing at it. Resolve via package.json so we
// always pick up whatever the installed version uses, no matter where
// node_modules ends up.
let cliPath;
try {
  const pkgJsonPath = require.resolve("@playwright/mcp/package.json");
  const pkg = require("@playwright/mcp/package.json");
  const binEntry =
    typeof pkg.bin === "string"
      ? pkg.bin
      : pkg.bin && pkg.bin["mcp-server-playwright"]
        ? pkg.bin["mcp-server-playwright"]
        : "cli.js";
  cliPath = resolve(dirname(pkgJsonPath), binEntry);
} catch (err) {
  console.error(
    "[reklam-fabrikasi] Could not resolve @playwright/mcp. " +
      "Run `npm install` inside Reklam Fabrikası plugin folder."
  );
  console.error(err && err.message ? err.message : err);
  process.exit(1);
}

const args = process.argv.slice(2);

const child = spawn(process.execPath, [cliPath, ...args], {
  stdio: "inherit",
  env: process.env,
  cwd: dirname(fileURLToPath(import.meta.url))
});

child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 0);
});

child.on("error", (err) => {
  console.error("[reklam-fabrikasi] Failed to start @playwright/mcp:", err.message);
  process.exit(1);
});
