import { describe, expect, it, vi, afterEach } from "vitest";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { SDElementsClient } from "../../src/utils/apiClient.js";

import { registerApplicationTools } from "../../src/tools/applications.js";
import { registerBusinessUnitTools } from "../../src/tools/businessUnits.js";
import { registerCountermeasureTools } from "../../src/tools/countermeasures.js";
import { registerDiagramTools } from "../../src/tools/diagrams.js";
import { registerGenericTools } from "../../src/tools/generic.js";
import { registerProjectTools } from "../../src/tools/project.js";
import { registerReportTools } from "../../src/tools/reports.js";
import { registerScanTools } from "../../src/tools/scans.js";
import { registerSurveyTools } from "../../src/tools/surveys.js";
import { registerUserTools } from "../../src/tools/users.js";

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

function resolved<T>(value: T) {
  return vi.fn().mockResolvedValue(value);
}

function returned<T>(value: T) {
  return vi.fn().mockReturnValue(value);
}

/**
 * This list is intentionally explicit.
 *
 * If you add/remove tools, update this list so we detect accidental drift.
 */
const EXPECTED_TOOL_NAMES = [
  // applications
  "create_application",
  "get_application",
  "list_applications",
  "update_application",

  // business units
  "get_business_unit",
  "list_business_units",

  // countermeasures
  "add_countermeasure_note",
  "get_countermeasure",
  "get_task_status_choices",
  "list_countermeasures",
  "update_countermeasure",

  // diagrams
  "create_diagram",
  "delete_diagram",
  "get_diagram",
  "list_project_diagrams",
  "update_diagram",

  // generic
  "api_request",
  "test_connection",

  // projects
  "create_project",
  "create_project_from_code",
  "delete_project",
  "get_project",
  "get_risk_policy",
  "list_profiles",
  "list_projects",
  "list_risk_policies",
  "update_project",

  // reports
  "create_advanced_report",
  "execute_cube_query",
  "get_advanced_report",
  "list_advanced_reports",
  "run_advanced_report",
  "update_advanced_report",

  // scans
  "get_scan_status",
  "list_scan_connections",
  "list_scans",
  "scan_repository",

  // surveys
  "add_survey_answers_by_text",
  "add_survey_question_comment",
  "commit_survey_draft",
  "find_survey_answers",
  "get_project_survey",
  "get_survey_answers_for_project",
  "remove_survey_answers_by_text",
  "set_project_survey_by_text",
  "update_project_survey",

  // users
  "get_current_user",
  "get_user",
  "list_users",
].sort();

function registerAllTools(server: TestMcpServer, client: SDElementsClient) {
  registerApplicationTools(server as unknown as McpServer, client);
  registerBusinessUnitTools(server as unknown as McpServer, client);
  registerCountermeasureTools(server as unknown as McpServer, client);
  registerDiagramTools(server as unknown as McpServer, client);
  registerGenericTools(server as unknown as McpServer, client);
  registerProjectTools(server as unknown as McpServer, client);
  registerReportTools(server as unknown as McpServer, client);
  registerScanTools(server as unknown as McpServer, client);
  registerSurveyTools(server as unknown as McpServer, client);
  registerUserTools(server as unknown as McpServer, client);
}

function makeStubClient(): SDElementsClient {
  /**
   * Proxy-based stub: any missing method becomes an async vi.fn() that resolves {}.
   * Only the methods that need specific shapes are overridden here.
   */
  const defaultAsyncFnCache = new Map<string, ReturnType<typeof vi.fn>>();

  const overrides: Record<string, unknown> = {
    // generic
    apiRequest: resolved({ ok: true }),
    testConnection: resolved(true),
    getHost: returned("https://example.test"),

    // projects (create_project auto-selects default profile if not provided)
    listProfiles: resolved({
      results: [{ id: "P", name: "Default", default: true }],
    }),

    // surveys
    getProjectSurvey: resolved({ answers: [], sections: [] }),
    updateProjectSurvey: resolved({ success: true }),
    findAnswersByText: vi.fn().mockImplementation(async (texts: string[]) => {
      const out: Record<string, unknown> = {};
      for (const t of texts) out[t] = { id: "A1", text: t };
      return out;
    }),
    loadLibraryAnswers: resolved(undefined),
    addAnswerToSurveyDraft: resolved({ success: true }),
    commitSurveyDraft: resolved({ ok: true }),
    addSurveyQuestionComment: resolved({ success: true }),
    getLibraryAnswersCache: returned([]),

    // task status resolution
    listTaskStatuses: resolved({
      results: [{ id: "TS1", name: "Complete", slug: "DONE" }],
    }),

    // cube + reports
    executeCubeQuery: resolved({ data: [] }),
    runAdvancedReport: resolved({ query: { id: 1 }, data: [] }),

    // scanning
    listTeamOnboardingConnections: resolved({ results: [] }),
    createTeamOnboardingScan: resolved({ id: 1 }),
    getTeamOnboardingScan: resolved({ id: 1 }),
    listTeamOnboardingScans: resolved({ results: [] }),
  };

  return new Proxy(overrides as Record<string, unknown>, {
    get(target, prop) {
      if (typeof prop !== "string") return undefined;
      if (prop in target) return target[prop];

      if (!defaultAsyncFnCache.has(prop)) {
        defaultAsyncFnCache.set(prop, resolved({}));
      }
      return defaultAsyncFnCache.get(prop);
    },
  }) as unknown as SDElementsClient;
}

const SMOKE_ARGS_BY_TOOL: Record<string, Record<string, unknown>> = {
  // applications
  list_applications: {},
  get_application: { application_id: 1 },
  create_application: { name: "App", business_unit_id: 1 },
  update_application: { application_id: 1, name: "App2" },

  // business units
  list_business_units: {},
  get_business_unit: { business_unit_id: 1 },

  // countermeasures
  list_countermeasures: { project_id: 1 },
  get_countermeasure: { project_id: 1, countermeasure_id: "T1" },
  update_countermeasure: {
    project_id: 1,
    countermeasure_id: "T1",
    status: "TS1",
  },
  add_countermeasure_note: {
    project_id: 1,
    countermeasure_id: "T1",
    note: "note",
  },
  get_task_status_choices: {},

  // diagrams
  list_project_diagrams: { project_id: 1 },
  get_diagram: { diagram_id: 1 },
  create_diagram: { project_id: 1, name: "Diag" },
  update_diagram: { diagram_id: 1, name: "Diag2" },
  delete_diagram: { diagram_id: 1 },

  // generic
  api_request: { method: "GET", endpoint: "users/me/" },
  test_connection: {},

  // projects
  list_projects: {},
  get_project: { project_id: 1 },
  list_profiles: {},
  list_risk_policies: {},
  get_risk_policy: { risk_policy_id: 1 },
  create_project: { application_id: 1, name: "Proj", description: "d" },
  update_project: { project_id: 1, name: "Proj2" },
  delete_project: { project_id: 1 },
  // This tool is complex; smoke the early-error path (no inputs) to ensure it returns JSON.
  create_project_from_code: {},

  // reports
  list_advanced_reports: {},
  get_advanced_report: { report_id: 1 },
  create_advanced_report: {
    title: "R",
    chart: "table",
    query: {
      schema: "application",
      dimensions: ["Application.name"],
      measures: ["Project.count"],
    },
  },
  update_advanced_report: { report_id: 1, title: "R2" },
  run_advanced_report: { report_id: 1 },
  execute_cube_query: {
    query: {
      schema: "application",
      dimensions: ["Application.name"],
      measures: ["Project.count"],
    },
  },

  // scans
  list_scan_connections: {},
  scan_repository: {
    project_id: 1,
    connection_id: 1,
    repository_url: "https://example.test/repo",
  },
  get_scan_status: { scan_id: 1 },
  list_scans: {},

  // surveys
  get_project_survey: { project_id: 1 },
  update_project_survey: { project_id: 1, answers: ["A1"] },
  find_survey_answers: { project_id: 1, search_texts: ["X"] },
  set_project_survey_by_text: {
    project_id: 1,
    answer_texts: ["X"],
    replace_all: false,
  },
  remove_survey_answers_by_text: {
    project_id: 1,
    answer_texts_to_remove: ["X"],
  },
  add_survey_answers_by_text: { project_id: 1, answer_texts_to_add: ["X"] },
  get_survey_answers_for_project: { project_id: 1, format: "summary" },
  commit_survey_draft: { project_id: 1 },
  add_survey_question_comment: {
    project_id: 1,
    question_id: "Q1",
    comment: "c",
  },

  // users
  list_users: {},
  get_user: { user_id: 1 },
  get_current_user: {},
};

describe("tools (coverage)", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("registers the complete expected tool set (no missing or extra tools)", () => {
    const server = new TestMcpServer();
    const client = makeStubClient();
    registerAllTools(server, client);

    const actual = Array.from(server.tools.keys()).sort();
    expect(actual).toEqual(EXPECTED_TOOL_NAMES);

    // Also ensure we have no duplicates (Map would hide duplicates silently).
    expect(new Set(actual).size).toBe(actual.length);
  });

  it("smoke-runs every tool handler and returns parseable JSON", async () => {
    const server = new TestMcpServer();
    const client = makeStubClient();
    registerAllTools(server, client);

    for (const toolName of EXPECTED_TOOL_NAMES) {
      const tool = server.tools.get(toolName);
      expect(tool, `tool not registered: ${toolName}`).toBeTruthy();

      const args = SMOKE_ARGS_BY_TOOL[toolName];
      expect(args, `missing smoke args for tool: ${toolName}`).toBeTruthy();

      // Ensure every tool can be invoked at least once without throwing,
      // and that its response is JSON.
      const res = await tool!.handler(args);
      expect(
        res.content?.[0]?.text,
        `no response text for tool: ${toolName}`
      ).toBeTruthy();
      expect(
        () => parseToolText(res),
        `response is not JSON for tool: ${toolName}`
      ).not.toThrow();
    }
  });
});




