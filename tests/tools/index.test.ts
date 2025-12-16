import { describe, expect, it, vi, afterEach } from "vitest";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { registerAll } from "../../src/tools/index.js";

class CapturingServer {
  tools = new Set<string>();
  registerTool(name: string) {
    this.tools.add(name);
  }
}

describe("tools/index registerAll", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    delete process.env.SDE_HOST;
    delete process.env.SDE_API_KEY;
  });

  it("throws when required env vars are missing", () => {
    // Ensure env vars are unset for this test
    delete process.env.SDE_HOST;
    delete process.env.SDE_API_KEY;
    
    expect(() => registerAll(new CapturingServer() as unknown as McpServer)).toThrow(
      /Missing required environment variables/
    );
  });

  it("registers tools when env vars are present (and warms library answers best-effort)", () => {
    process.env.SDE_HOST = "https://example.test";
    process.env.SDE_API_KEY = "abc";

    // Warmup will call fetch for library/answers. Stub it to avoid network.
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        return new Response(JSON.stringify({ results: [] }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }) as unknown as typeof fetch
    );

    const server = new CapturingServer() as unknown as McpServer;
    registerAll(server);

    // Spot-check a few tool names from different modules
    const names = Array.from((server as CapturingServer).tools);
    expect(names).toContain("list_projects");
    expect(names).toContain("list_applications");
    expect(names).toContain("list_business_units");
    expect(names).toContain("list_countermeasures");
    expect(names).toContain("get_project_survey");
    expect(names).toContain("list_users");
    expect(names).toContain("list_scans");
    expect(names).toContain("list_project_diagrams");
    expect(names).toContain("list_advanced_reports");
    expect(names).toContain("api_request");
  });
});


