import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SDElementsClient } from "../utils/apiClient";
import { registerProjectTools } from "./project";
import { registerApplicationTools } from "./applications";
import { registerBusinessUnitTools } from "./businessUnits";
import { registerCountermeasureTools } from "./countermeasures";
import { registerSurveyTools } from "./surveys";
import { registerUserTools } from "./users";
import { registerScanTools } from "./scans";
import { registerDiagramTools } from "./diagrams";
import { registerReportTools } from "./reports";
import { registerGenericTools } from "./generic";

export type SdeCredentials = {
  host: string;
  apiKey: string;
};

/**
 * Register all tools with the MCP server
 * Includes tools for: projects, applications, business units, countermeasures,
 * surveys, users, scans, diagrams, reports, and generic API operations
 */
export function registerAll(server: McpServer, creds?: SdeCredentials): void {
  const host = creds?.host ?? process.env.SDE_HOST ?? "";
  const apiKey = creds?.apiKey ?? process.env.SDE_API_KEY ?? "";

  if (!host || !apiKey) {
    if (creds) {
      const missing = [
        !host ? "host" : null,
        !apiKey ? "apiKey" : null,
      ]
        .filter(Boolean)
        .join(", ");
      throw new Error(`Missing required credentials: ${missing}`);
    } else {
      const missing = [
        !host ? "SDE_HOST" : null,
        !apiKey ? "SDE_API_KEY" : null,
      ]
        .filter(Boolean)
        .join(", ");
      throw new Error(`Missing required environment variables: ${missing}`);
    }
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
