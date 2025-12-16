import { describe, expect, it, vi, afterEach } from "vitest";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { SDElementsClient } from "../../src/utils/apiClient.js";
import { registerProjectTools } from "../../src/tools/project.js";

type ToolResult = {
  content: Array<{ type: string; text: string }>;
};
type ToolHandler = (args: Record<string, unknown>) => Promise<ToolResult>;

class TestMcpServer {
  tools = new Map<string, { meta: unknown; handler: ToolHandler }>();
  registerTool(name: string, meta: unknown, handler: ToolHandler) {
    this.tools.set(name, { meta, handler });
  }
}

function parseToolText<T = unknown>(result: ToolResult): T {
  return JSON.parse(result.content[0].text) as T;
}

describe("project tool handlers (unit)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("create_project returns a clear error when name is missing", async () => {
    const server = new TestMcpServer();
    const client = {} as unknown as SDElementsClient;
    registerProjectTools(server as unknown as McpServer, client);

    const tool = server.tools.get("create_project")!;
    const res = await tool.handler({ application_id: 1 });
    const body = parseToolText<{ error: string }>(res);
    expect(body.error).toMatch(/Project name is required/);
  });

  it("create_project returns available profiles when no default/detection is possible", async () => {
    const server = new TestMcpServer();
    const client = {
      listProfiles: vi.fn().mockResolvedValue({
        results: [
          { id: "A", name: "Alpha", default: false },
          { id: "B", name: "Beta", default: false },
        ],
      }),
    } as unknown as SDElementsClient;

    registerProjectTools(server as unknown as McpServer, client);

    const tool = server.tools.get("create_project")!;
    const res = await tool.handler({
      application_id: 1,
      name: "Some Project",
      description: "no keywords",
    });

    const body = parseToolText<{ error: string; available_profiles: unknown[] }>(
      res
    );
    expect(body.error).toMatch(/Profile is required/);
    expect(body.available_profiles).toEqual([
      { id: "A", name: "Alpha" },
      { id: "B", name: "Beta" },
    ]);
  });

  it("update_project returns an error when risk_policy is a non-numeric string", async () => {
    const server = new TestMcpServer();
    const client = {} as unknown as SDElementsClient;
    registerProjectTools(server as unknown as McpServer, client);

    const tool = server.tools.get("update_project")!;
    const res = await tool.handler({ project_id: 1, risk_policy: "abc" });
    const body = parseToolText<{ error: string; suggestion?: string }>(res);
    expect(body.error).toMatch(/risk_policy must be an integer ID/i);
    expect(body.suggestion).toMatch(/list_risk_policies/i);
  });
});




