import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SDElementsClient } from "../utils/apiClient.js";
import { registerProjectTools } from "./project.js";
import { registerApplicationTools } from "./applications.js";
import { registerBusinessUnitTools } from "./businessUnits.js";
import { registerCountermeasureTools } from "./countermeasures.js";
import { registerSurveyTools } from "./surveys.js";
import { registerUserTools } from "./users.js";
import { registerScanTools } from "./scans.js";
import { registerDiagramTools } from "./diagrams.js";
import { registerReportTools } from "./reports.js";
import { registerGenericTools } from "./generic.js";

/**
 * Register all tools with the MCP server
 * Includes tools for: projects, applications, business units, countermeasures,
 * surveys, users, scans, diagrams, reports, and generic API operations
 */
export function registerAll(server: McpServer): void {
  const host = process.env.SDE_HOST || "";
  const apiKey = process.env.SDE_API_KEY || "";

  if (!host || !apiKey) {
    const missing = [
      !host ? "SDE_HOST" : null,
      !apiKey ? "SDE_API_KEY" : null,
    ]
      .filter(Boolean)
      .join(", ");
    throw new Error(`Missing required environment variables: ${missing}`);
  }

  const client = new SDElementsClient({ host, apiKey });

  // Warm up library answers cache (best effort)
  client.loadLibraryAnswers().catch(() => {
    // Swallow errors; tools will load lazily if needed
  });

  registerProjectTools(server, client);
  registerApplicationTools(server, client);
  registerBusinessUnitTools(server, client);
  registerCountermeasureTools(server, client);
  registerSurveyTools(server, client);
  registerUserTools(server, client);
  registerScanTools(server, client);
  registerDiagramTools(server, client);
  registerReportTools(server, client);
  registerGenericTools(server, client);
}
