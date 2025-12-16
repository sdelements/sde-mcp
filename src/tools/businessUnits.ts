/**
 * Business unit-related tools
 * Translated from: https://github.com/sdelements/sde-mcp/blob/master/src/sde_mcp_server/tools/business_units.py
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { SDElementsClient } from "../utils/apiClient.js";
import { buildParams, jsonToolResult } from "./_shared.js";

/**
 * Register all business unit-related tools
 */
export function registerBusinessUnitTools(
  server: McpServer,
  client: SDElementsClient
): void {
  // List business units
  server.registerTool(
    "list_business_units",
    {
      title: "List Business Units",
      description: "List all business units",
      inputSchema: z.object({
        page_size: z.number().optional().describe("Number of results per page"),
        include: z.string().optional().describe("Related resources to include"),
        expand: z.string().optional().describe("Fields to expand"),
      }),
    },
    async ({ page_size, include, expand }) => {
      const params = buildParams({ page_size, include, expand });
      const result = await client.listBusinessUnits(params);

      return jsonToolResult(result);
    }
  );

  // Get business unit
  server.registerTool(
    "get_business_unit",
    {
      title: "Get Business Unit",
      description: "Get details of a specific business unit",
      inputSchema: z.object({
        business_unit_id: z.number().describe("ID of the business unit"),
      }),
    },
    async ({ business_unit_id }) => {
      const result = await client.getBusinessUnit(business_unit_id);

      return jsonToolResult(result);
    }
  );
}
