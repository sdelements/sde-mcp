/**
 * Diagram-related tools
 * Translated from: https://github.com/sdelements/sde-mcp/blob/master/src/sde_mcp_server/tools/diagrams.py
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { SDElementsClient } from "../utils/apiClient.js";
import { jsonToolResult } from "./_shared.js";

/**
 * Register all diagram-related tools
 */
export function registerDiagramTools(
  server: McpServer,
  client: SDElementsClient
): void {
  // List project diagrams
  server.registerTool(
    "list_project_diagrams",
    {
      title: "List Project Diagrams",
      description: "List diagrams for a project",
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project"),
      }),
    },
    async ({ project_id }) => {
      const result = await client.listProjectDiagrams(project_id);

      return jsonToolResult(result);
    }
  );

  // Get diagram
  server.registerTool(
    "get_diagram",
    {
      title: "Get Diagram",
      description: "Get details of a specific diagram",
      inputSchema: z.object({
        diagram_id: z.number().describe("ID of the diagram"),
      }),
    },
    async ({ diagram_id }) => {
      const result = await client.getProjectDiagram(diagram_id);

      return jsonToolResult(result);
    }
  );

  // Create diagram
  server.registerTool(
    "create_diagram",
    {
      title: "Create Diagram",
      description: "Create a new diagram",
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project"),
        name: z.string().describe("Name of the diagram"),
        diagram_data: z
          .record(z.string(), z.unknown())
          .optional()
          .describe("Diagram data"),
      }),
    },
    async ({ project_id, name, diagram_data }) => {
      const data: Record<string, unknown> = {
        project: project_id,
        name,
      };

      if (diagram_data) {
        data.diagram_data = diagram_data;
      }

      const result = await client.createProjectDiagram(data);

      return jsonToolResult(result);
    }
  );

  // Update diagram
  server.registerTool(
    "update_diagram",
    {
      title: "Update Diagram",
      description: "Update a diagram",
      inputSchema: z.object({
        diagram_id: z.number().describe("ID of the diagram to update"),
        name: z.string().optional().describe("New name for the diagram"),
        diagram_data: z
          .record(z.string(), z.unknown())
          .optional()
          .describe("New diagram data"),
      }),
    },
    async ({ diagram_id, name, diagram_data }) => {
      const data: Record<string, unknown> = {};

      if (name) {
        data.name = name;
      }
      if (diagram_data) {
        data.diagram_data = diagram_data;
      }

      const result = await client.updateProjectDiagram(diagram_id, data);

      return jsonToolResult(result);
    }
  );

  // Delete diagram
  server.registerTool(
    "delete_diagram",
    {
      title: "Delete Diagram",
      description: "Delete a diagram",
      inputSchema: z.object({
        diagram_id: z.number().describe("ID of the diagram to delete"),
      }),
    },
    async ({ diagram_id }) => {
      const result = await client.deleteProjectDiagram(diagram_id);

      return jsonToolResult(result);
    }
  );
}
