/**
 * Application-related tools
 * Translated from: https://github.com/sdelements/sde-mcp/blob/master/src/sde_mcp_server/tools/applications.py
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { SDElementsClient } from "../utils/apiClient.js";
import { buildParams, jsonToolResult } from "./_shared.js";

/**
 * Register all application-related tools
 */
export function registerApplicationTools(
  server: McpServer,
  client: SDElementsClient
): void {
  // List applications
  server.registerTool(
    "list_applications",
    {
      title: "List Applications",
      description: "List all applications",
      inputSchema: z.object({
        page_size: z.number().optional().describe("Number of results per page"),
        include: z.string().optional().describe("Related resources to include"),
        expand: z.string().optional().describe("Fields to expand"),
      }),
    },
    async ({ page_size, include, expand }) => {
      const params = buildParams({ page_size, include, expand });
      const result = await client.listApplications(params);

      return jsonToolResult(result);
    }
  );

  // Get application
  server.registerTool(
    "get_application",
    {
      title: "Get Application",
      description: "Get details of a specific application",
      inputSchema: z.object({
        application_id: z.number().describe("ID of the application"),
        page_size: z.number().optional().describe("Number of results per page"),
        include: z.string().optional().describe("Related resources to include"),
        expand: z.string().optional().describe("Fields to expand"),
      }),
    },
    async ({ application_id, page_size, include, expand }) => {
      const params = buildParams({ page_size, include, expand });
      const result = await client.getApplication(application_id, params);

      return jsonToolResult(result);
    }
  );

  // Create application
  server.registerTool(
    "create_application",
    {
      title: "Create Application",
      description: "Create a new application",
      inputSchema: z.object({
        name: z.string().describe("Name of the application"),
        business_unit_id: z.number().describe("ID of the business unit"),
        description: z
          .string()
          .optional()
          .describe("Description of the application"),
      }),
    },
    async ({ name, business_unit_id, description }) => {
      const data: Record<string, unknown> = {
        name,
        business_unit: business_unit_id,
      };

      if (description) {
        data.description = description;
      }

      const result = await client.createApplication(data);

      return jsonToolResult(result);
    }
  );

  // Update application
  server.registerTool(
    "update_application",
    {
      title: "Update Application",
      description: "Update an existing application",
      inputSchema: z.object({
        application_id: z.number().describe("ID of the application to update"),
        name: z.string().optional().describe("New name for the application"),
        description: z.string().optional().describe("New description"),
      }),
    },
    async ({ application_id, name, description }) => {
      const data: Record<string, unknown> = {};

      if (name) {
        data.name = name;
      }
      if (description) {
        data.description = description;
      }

      const result = await client.updateApplication(application_id, data);

      return jsonToolResult(result);
    }
  );
}
