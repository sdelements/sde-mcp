import { describe, expect, it, vi, afterEach } from "vitest";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { SDElementsClient } from "../../src/utils/apiClient.js";
import { registerCountermeasureTools } from "../../src/tools/countermeasures.js";

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

describe("countermeasure tool handlers (unit)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("get_countermeasure normalizes numeric ID to T{n} and prefixes project_id", async () => {
    const server = new TestMcpServer();
    const client = {
      getTask: vi.fn().mockResolvedValue({ ok: true }),
    } as unknown as SDElementsClient;

    registerCountermeasureTools(server as unknown as McpServer, client);

    const tool = server.tools.get("get_countermeasure")!;
    const res = await tool.handler({
      project_id: 31244,
      countermeasure_id: 21,
      risk_relevant: true,
    });

    expect((client as unknown as { getTask: unknown }).getTask).toHaveBeenCalledWith(
      31244,
      "31244-T21",
      { risk_relevant: true }
    );
    expect(parseToolText(res)).toEqual({ ok: true });
  });

  it("update_countermeasure resolves status name to TS id using task-statuses", async () => {
    const server = new TestMcpServer();
    const client = {
      listTaskStatuses: vi.fn().mockResolvedValue({
        results: [{ id: "TS1", name: "Complete", slug: "DONE" }],
      }),
      updateTask: vi.fn().mockResolvedValue({ id: "1-T1", status: "TS1" }),
    } as unknown as SDElementsClient;

    registerCountermeasureTools(server as unknown as McpServer, client);

    const tool = server.tools.get("update_countermeasure")!;
    const res = await tool.handler({
      project_id: 1,
      countermeasure_id: "T1",
      status: "Complete",
      notes: "done",
    });

    expect(
      (client as unknown as { updateTask: unknown }).updateTask
    ).toHaveBeenCalledWith(1, "1-T1", {
      status: "TS1",
      status_note: "done",
    });
    expect(parseToolText(res)).toEqual({ id: "1-T1", status: "TS1" });
  });
});


