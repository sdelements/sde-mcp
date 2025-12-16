/**
 * Generic API and utility tools
 * Translated from: https://github.com/sdelements/sde-mcp/blob/master/src/sde_mcp_server/tools/generic.py
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { SDElementsClient } from "../utils/apiClient.js";
import { jsonToolResult } from "./_shared.js";

/**
 * Register all generic API tools
 */
export function registerGenericTools(
  server: McpServer,
  client: SDElementsClient
): void {
  // API request
  server.registerTool(
    "api_request",
    {
      title: "API Request",
      description:
        "Make a generic API request to a custom endpoint. Use when user says 'make a GET/POST/PUT/DELETE request', 'call API endpoint', or 'custom API call'. Do NOT use for specific operations - use dedicated tools like get_project instead.",
      inputSchema: z.object({
        method: z
          .string()
          .describe("HTTP method (GET, POST, PUT, PATCH, DELETE)"),
        endpoint: z.string().describe("API endpoint path"),
        params: z
          .record(z.string(), z.unknown())
          .optional()
          .describe("Query parameters"),
        data: z
          .record(z.string(), z.unknown())
          .optional()
          .describe("Request body data"),
      }),
    },
    async ({ method, endpoint, params, data }) => {
      const result = await client.apiRequest(
        method.toUpperCase() as "GET" | "POST" | "PUT" | "PATCH" | "DELETE",
        endpoint,
        data as Record<string, unknown> | undefined,
        params as
          | import("../utils/apiClient.js").SDElementsQueryParams
          | undefined
      );

      return jsonToolResult(result);
    }
  );

  // Test connection
  server.registerTool(
    "test_connection",
    {
      title: "Test Connection",
      description:
        "Test the connection to SD Elements API. Use this to verify API connectivity and credentials, not for making API calls.",
      inputSchema: z.object({}),
    },
    async () => {
      const success = await client.testConnection();

      const result = {
        connection_successful: success,
        host: client.getHost(),
        message: success ? "Connection successful" : "Connection failed",
      };

      return jsonToolResult(result);
    }
  );
}
