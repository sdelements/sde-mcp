import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SDElementsClient } from "../utils/apiClient";
import { registerProjectTools } from "./project";
import { registerApplicationTools } from "./applications";
import { registerBusinessUnitTools } from "./businessUnits";
import { registerCountermeasureTools } from "./countermeasures";
import { registerSurveyTools } from "./surveys";
import { registerUserTools } from "./users";
import { registerScanTools } from "./scans";
import { registerGenericTools } from "./generic";
import { registerCompactTools } from "./compact";
import { registerLibraryTools } from "./library";

export type SdeCredentials = {
  host: string;
  apiKey: string;
};

/**
 * Register all tools with the MCP server
 * Includes tools for: projects, applications, business units, countermeasures,
 * surveys, users, scans, and generic API operations
 *
 * Toolsets:
 * - default: compact (few router tools)
 * - SDE_TOOLSET=full: registers the legacy tool set (excluding diagrams + reports)
 */
export function registerAll(server: McpServer, creds?: SdeCredentials): void {
  const host = creds?.host ?? process.env.SDE_HOST ?? "";
  const apiKey = creds?.apiKey ?? process.env.SDE_API_KEY ?? "";

  if (!host || !apiKey) {
    if (creds) {
      const missing = [!host ? "host" : null, !apiKey ? "apiKey" : null]
        .filter(Boolean)
        .join(", ");
      throw new Error(`Missing required credentials: ${missing}`);
    }

    const missing = [!host ? "SDE_HOST" : null, !apiKey ? "SDE_API_KEY" : null]
      .filter(Boolean)
      .join(", ");
    throw new Error(`Missing required environment variables: ${missing}`);
  }

  const client = new SDElementsClient({ host, apiKey });

  // Warm up library answers cache (best effort)
  client.loadLibraryAnswers().catch(() => {
    // Swallow errors; tools will load lazily if needed
  });

  const toolset = (process.env.SDE_TOOLSET || "compact").toLowerCase();

  if (toolset === "full") {
    registerProjectTools(server, client);
    registerApplicationTools(server, client);
    registerBusinessUnitTools(server, client);
    registerCountermeasureTools(server, client);
    registerSurveyTools(server, client);
    registerUserTools(server, client);
    registerScanTools(server, client);
    // Diagrams + reporting intentionally not registered.
    registerGenericTools(server, client);
    registerLibraryTools(server, client);
    return;
  }

  // Default: compact
  registerCompactTools(server, client);
}
