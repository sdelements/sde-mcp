import { build } from "esbuild";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  ".."
);
const srcDir = path.join(repoRoot, "src");
const distDir = path.join(repoRoot, "dist");

function collectTsFiles(dir) {
  /** @type {string[]} */
  const results = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith(".")) continue;
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...collectTsFiles(fullPath));
      continue;
    }
    if (!entry.isFile()) continue;
    if (entry.name.endsWith(".ts") && !entry.name.endsWith(".test.ts")) {
      results.push(fullPath);
    }
  }
  return results;
}

const entryPoints = collectTsFiles(srcDir);

await build({
  entryPoints,
  outdir: distDir,
  outbase: srcDir,
  bundle: true,
  splitting: true,
  format: "esm",
  platform: "node",
  target: "node20",
  packages: "external",
  sourcemap: false,
  legalComments: "none",
});

// Ensure CLI entry has a proper shebang at the very top (esbuild may drop it when bundling).
const distIndexPath = path.join(distDir, "index.js");
if (fs.existsSync(distIndexPath)) {
  const raw = fs.readFileSync(distIndexPath, "utf8");
  const shebang = "#!/usr/bin/env node\n";
  if (!raw.startsWith("#!")) {
    fs.writeFileSync(distIndexPath, shebang + raw, "utf8");
  } else if (!raw.startsWith(shebang)) {
    // Normalize to our expected shebang.
    const withoutFirstLine = raw.replace(/^#!.*\n/, "");
    fs.writeFileSync(distIndexPath, shebang + withoutFirstLine, "utf8");
  }
}
