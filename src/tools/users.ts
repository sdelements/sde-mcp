/**
 * User-related tools
 * Translated from: https://github.com/sdelements/sde-mcp/blob/master/src/sde_mcp_server/tools/users.py
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import {
  SDElementsClient,
  type SDElementsQueryParams,
} from "../utils/apiClient.js";
import { jsonToolResult } from "./_shared.js";

/**
 * Register all user-related tools
 */
export function registerUserTools(
  server: McpServer,
  client: SDElementsClient
): void {
  // List users
  server.registerTool(
    "list_users",
    {
      title: "List Users",
      description: "List all users",
      inputSchema: z.object({
        page_size: z.number().optional().describe("Number of results per page"),
        active: z.boolean().optional().describe("Filter by active status"),
      }),
    },
    async ({ page_size, active }) => {
      const params: SDElementsQueryParams = {};

      if (page_size !== undefined) {
        params.page_size = page_size;
      }
      if (active !== undefined) {
        params.is_active = active;
      }

      const result = await client.listUsers(params);

      return jsonToolResult(result);
    }
  );

  // Get user
  server.registerTool(
    "get_user",
    {
      title: "Get User",
      description: "Get details of a specific user",
      inputSchema: z.object({
        user_id: z.number().describe("ID of the user"),
      }),
    },
    async ({ user_id }) => {
      const result = await client.getUser(user_id);

      return jsonToolResult(result);
    }
  );

  // Get current user
  server.registerTool(
    "get_current_user",
    {
      title: "Get Current User",
      description: "Get current authenticated user",
      inputSchema: z.object({}),
    },
    async () => {
      const result = await client.getCurrentUser();

      return jsonToolResult(result);
    }
  );
}
