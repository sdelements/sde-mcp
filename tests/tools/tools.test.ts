import { describe, expect, it, vi, afterEach } from "vitest";
import { registerGenericTools } from "../../src/tools/generic.js";
import { registerSurveyTools } from "../../src/tools/surveys.js";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { SDElementsClient } from "../../src/utils/apiClient.js";

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

describe("tool handlers (unit)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("generic.api_request uppercases method and passes params/data through", async () => {
    const server = new TestMcpServer();
    const client = {
      apiRequest: vi
        .fn<
          (
            method: string,
            endpoint: string,
            data?: unknown,
            params?: unknown
          ) => Promise<unknown>
        >()
        .mockResolvedValue({ ok: true }),
      testConnection: vi.fn(),
      getHost: vi.fn(),
    };

    registerGenericTools(
      server as unknown as McpServer,
      client as unknown as SDElementsClient
    );

    const tool = server.tools.get("api_request");
    expect(tool).toBeTruthy();

    const res = await tool!.handler({
      method: "get",
      endpoint: "/users/me/",
      params: { page_size: 10 },
      data: { ignored: true },
    });

    expect(client.apiRequest).toHaveBeenCalledWith(
      "GET",
      "/users/me/",
      { ignored: true },
      { page_size: 10 }
    );
    expect(parseToolText(res)).toEqual({ ok: true });
  });

  it("surveys.set_project_survey_by_text returns an error when texts can't be found", async () => {
    const server = new TestMcpServer();
    const client = {
      findAnswersByText: vi.fn().mockResolvedValue({ "Made Up": null }),
    };

    registerSurveyTools(
      server as unknown as McpServer,
      client as unknown as SDElementsClient
    );

    const tool = server.tools.get("set_project_survey_by_text")!;
    const res = await tool.handler({
      project_id: 1,
      answer_texts: ["Made Up"],
      replace_all: true,
      survey_complete: false,
    });

    const body = parseToolText<{ error: string; search_results: unknown }>(res);
    expect(body.error).toMatch(/Could not find answers for: Made Up/);
    expect(body.search_results).toEqual({ "Made Up": null });
  });

  it("surveys.set_project_survey_by_text computes answers_to_deselect when replace_all=true", async () => {
    const server = new TestMcpServer();
    const client = {
      findAnswersByText: vi.fn().mockResolvedValue({
        Keep: {
          id: "A2",
          text: "Keep",
          question: "Q",
          matchType: "exact",
          similarity: 1,
        },
      }),
      getProjectSurvey: vi.fn().mockResolvedValue({ answers: ["A1", "A2"] }),
      updateProjectSurvey: vi.fn().mockResolvedValue({ success: true }),
    };

    registerSurveyTools(
      server as unknown as McpServer,
      client as unknown as SDElementsClient
    );

    const tool = server.tools.get("set_project_survey_by_text")!;
    const res = await tool.handler({
      project_id: 123,
      answer_texts: ["Keep"],
      replace_all: true,
      survey_complete: true,
    });

    expect(client.updateProjectSurvey).toHaveBeenCalledWith(123, {
      answers: ["A2"],
      answers_to_deselect: ["A1"],
      survey_complete: true,
    });

    const body = parseToolText<{
      success: boolean;
      answer_ids_used: string[];
      replace_all: boolean;
    }>(res);
    expect(body.success).toBe(true);
    expect(body.answer_ids_used).toEqual(["A2"]);
    expect(body.replace_all).toBe(true);
  });

  it("surveys.get_survey_answers_for_project returns a message when no answers are assigned", async () => {
    const server = new TestMcpServer();
    const client = {
      getProjectSurvey: vi.fn().mockResolvedValue({ answers: [] }),
    };

    registerSurveyTools(
      server as unknown as McpServer,
      client as unknown as SDElementsClient
    );
    const tool = server.tools.get("get_survey_answers_for_project")!;
    const res = await tool.handler({ project_id: 42, format: "summary" });

    const body = parseToolText<{
      project_id: number;
      answer_count: number;
      message: string;
    }>(res);
    expect(body.project_id).toBe(42);
    expect(body.answer_count).toBe(0);
    expect(body.message).toMatch(/No answers/);
  });
});




