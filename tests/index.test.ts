import { describe, expect, it } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { execSync } from "node:child_process";

describe("src/index", () => {
  it("should be a valid entrypoint file", () => {
    const __filename = fileURLToPath(import.meta.url);
    const __dirname = path.dirname(__filename);
    const indexPath = path.resolve(__dirname, "..", "src", "index.ts");

    const content = readFileSync(indexPath, "utf8");

    // Verify it has the shebang
    expect(content).toContain("#!/usr/bin/env node");

    // Verify it can start either stdio (default) or http via flag
    expect(content).toContain('from "./stdio"');
    expect(content).toContain('from "./http"');
    expect(content).toContain("--http");
    expect(content).toContain("npm_config_http");

    // Verify it exports server functions
    expect(content).toContain("export { createServer, setupSignalHandlers }");
    expect(content).toContain("export { main }");
    expect(content).toContain("export { main as mainHttp }");

    // Verify it calls main
    expect(content).toContain(".catch");
  });

  it("compiled index.js should have shebang", () => {
    const __filename = fileURLToPath(import.meta.url);
    const __dirname = path.dirname(__filename);
    const distIndexPath = path.resolve(__dirname, "..", "dist", "index.js");

    // Ensure dist exists for this assertion (CI/workspaces may not pre-build).
    if (!existsSync(distIndexPath)) {
      execSync("node scripts/build.mjs", {
        cwd: path.resolve(__dirname, ".."),
        stdio: "inherit",
      });
    }
    const content = readFileSync(distIndexPath, "utf8");

    // Verify it has the shebang
    expect(content.startsWith("#!/usr/bin/env node")).toBe(true);
  });
});
