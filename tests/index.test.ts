import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

describe("src/index", () => {
  it("should be a valid entrypoint file", () => {
    const __filename = fileURLToPath(import.meta.url);
    const __dirname = path.dirname(__filename);
    const indexPath = path.resolve(__dirname, "..", "src", "index.ts");
    
    const content = readFileSync(indexPath, "utf8");
    
    // Verify it has the shebang
    expect(content).toContain("#!/usr/bin/env node");
    
    // Verify it imports main from server
    expect(content).toContain('import { main } from "./server.js"');
    
    // Verify it exports server functions
    expect(content).toContain("export { createServer, setupSignalHandlers, main }");
    
    // Verify it calls main
    expect(content).toContain("main().catch");
  });

  it("compiled index.js should have shebang", () => {
    const __filename = fileURLToPath(import.meta.url);
    const __dirname = path.dirname(__filename);
    const distIndexPath = path.resolve(__dirname, "..", "dist", "index.js");
    
    const content = readFileSync(distIndexPath, "utf8");
    
    // Verify it has the shebang
    expect(content.startsWith("#!/usr/bin/env node")).toBe(true);
  });
});
