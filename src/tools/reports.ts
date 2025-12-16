/**
 * Advanced report tools
 * Translated from: https://github.com/sdelements/sde-mcp/blob/master/src/sde_mcp_server/tools/reports.py
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import {
  SDElementsClient,
  type CubeQuery,
  type SDElementsQueryParams,
} from "../utils/apiClient.js";
import { jsonToolResult } from "./_shared.js";

/**
 * Parse query parameter from string or object
 */
function parseQueryParam(query: string | Record<string, unknown>): {
  parsed: Record<string, unknown> | null;
  error: string | null;
} {
  // If it's already an object, use it directly
  if (typeof query === "object" && query !== null) {
    return { parsed: query, error: null };
  }

  // Convert to string if it's not already
  const queryStr = String(query);

  // Try to parse as JSON, handling multiple encoding layers
  const maxAttempts = 3;
  let parsed: unknown = queryStr;

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      if (typeof parsed === "string") {
        parsed = JSON.parse(parsed);
      } else {
        break; // Already parsed to a non-string
      }
    } catch (e) {
      if (attempt === maxAttempts - 1) {
        // Final attempt failed
        const errorMsg = e instanceof Error ? e.message : String(e);
        return {
          parsed: null,
          error: JSON.stringify(
            {
              error: "Invalid JSON in query parameter",
              json_error: errorMsg,
              received_type: typeof query,
              received_value_preview: queryStr.substring(0, 500),
              suggestion:
                "Ensure the query is valid JSON. Check for missing quotes, commas, or brackets.",
            },
            null,
            2
          ),
        };
      }
      // Try again with the parsed result (might be double-encoded)
      continue;
    }
  }

  // Validate that we got an object
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    return {
      parsed: null,
      error: JSON.stringify(
        {
          error: "Query parameter must be a JSON object/dictionary",
          received_type: typeof query,
          parsed_type: typeof parsed,
          suggestion:
            "The query must be a JSON object, not an array or primitive value.",
        },
        null,
        2
      ),
    };
  }

  return { parsed: parsed as Record<string, unknown>, error: null };
}

/**
 * Register all advanced report tools
 */
export function registerReportTools(
  server: McpServer,
  client: SDElementsClient
): void {
  // List advanced reports
  server.registerTool(
    "list_advanced_reports",
    {
      title: "List Advanced Reports",
      description: "List all advanced reports",
      inputSchema: z.object({}),
    },
    async () => {
      const result = await client.listAdvancedReports();

      return jsonToolResult(result);
    }
  );

  // Get advanced report
  server.registerTool(
    "get_advanced_report",
    {
      title: "Get Advanced Report",
      description: "Get details of a specific advanced report",
      inputSchema: z.object({
        report_id: z.number().describe("ID of the report"),
      }),
    },
    async ({ report_id }) => {
      const result = await client.getAdvancedReport(report_id);

      return jsonToolResult(result);
    }
  );

  // Update advanced report
  server.registerTool(
    "update_advanced_report",
    {
      title: "Update Advanced Report",
      description:
        "Update an existing advanced report. Provide only the fields you want to update. The query and chart_meta parameters can be JSON strings or objects.",
      inputSchema: z.object({
        report_id: z.number().describe("ID of the report to update"),
        title: z.string().optional().describe("New title"),
        chart: z.string().optional().describe("Chart type"),
        query: z
          .union([z.string(), z.record(z.string(), z.unknown())])
          .optional()
          .describe("Cube query (JSON string or object)"),
        description: z.string().optional().describe("New description"),
        chart_meta: z
          .union([z.string(), z.record(z.string(), z.unknown())])
          .optional()
          .describe("Chart metadata (JSON string or object)"),
        type: z.string().optional().describe("Report type"),
      }),
    },
    async ({
      report_id,
      title,
      chart,
      query,
      description,
      chart_meta,
      type,
    }) => {
      const data: Record<string, unknown> = {};

      if (title !== undefined) data.title = title;
      if (chart !== undefined) data.chart = chart;
      if (description !== undefined) data.description = description;
      if (type !== undefined) data.type = type;

      if (query !== undefined) {
        const { parsed: queryDict, error } = parseQueryParam(query);
        if (error) {
          return {
            content: [{ type: "text", text: error }],
          };
        }
        data.query = queryDict;
      }

      if (chart_meta !== undefined) {
        const { parsed: metaDict, error } = parseQueryParam(chart_meta);
        if (error) {
          return {
            content: [{ type: "text", text: error }],
          };
        }
        data.chart_meta = metaDict;
      }

      if (Object.keys(data).length === 0) {
        return jsonToolResult({
          error: "No update data provided. Specify at least one field to update.",
        });
      }

      const result = await client.apiRequest(
        "PATCH",
        `queries/${report_id}/`,
        data
      );

      return jsonToolResult(result);
    }
  );

  // Run advanced report
  server.registerTool(
    "run_advanced_report",
    {
      title: "Run Advanced Report",
      description: "Run an advanced report",
      inputSchema: z.object({
        report_id: z.number().describe("ID of the report to run"),
        format: z.string().optional().describe("Output format"),
      }),
    },
    async ({ report_id, format }) => {
      const params: SDElementsQueryParams = {};

      if (format !== undefined) {
        params.format = format;
      }

      const result = await client.runAdvancedReport(report_id, params);

      return jsonToolResult(result);
    }
  );

  // Create advanced report
  server.registerTool(
    "create_advanced_report",
    {
      title: "Create Advanced Report",
      description:
        'Create a new advanced report. The query parameter can be a JSON string or object with schema, dimensions, measures, filters, order, and limit. The chart_meta parameter can be a JSON string or object if provided.\n\nExample query: {"schema": "application", "dimensions": ["Project.name"], "measures": ["Task.count"]}\nExample chart_meta: {"columnOrder": ["Project.name", "Task.count"]}',
      inputSchema: z.object({
        title: z.string().describe("Title of the report"),
        chart: z.string().describe("Chart type"),
        query: z
          .union([z.string(), z.record(z.string(), z.unknown())])
          .describe("Cube query (JSON string or object)"),
        description: z
          .string()
          .optional()
          .describe("Description of the report"),
        chart_meta: z
          .union([z.string(), z.record(z.string(), z.unknown())])
          .optional()
          .describe("Chart metadata"),
        type: z.string().optional().describe("Report type"),
      }),
    },
    async ({ title, chart, query, description, chart_meta, type }) => {
      // Parse query
      const { parsed: queryDict, error: queryError } = parseQueryParam(query);
      if (queryError) {
        return {
          content: [{ type: "text", text: queryError }],
        };
      }

      const data: Record<string, unknown> = {
        title,
        chart,
        query: queryDict,
      };

      if (description) {
        data.description = description;
      }
      if (type !== undefined) {
        data.type = type;
      }

      if (chart_meta !== undefined) {
        const { parsed: metaDict, error: metaError } =
          parseQueryParam(chart_meta);
        if (metaError) {
          return {
            content: [{ type: "text", text: metaError }],
          };
        }
        data.chart_meta = metaDict;
      }

      const result = await client.createAdvancedReport(data);

      return jsonToolResult(result);
    }
  );

  // Execute cube query
  server.registerTool(
    "execute_cube_query",
    {
      title: "Execute Cube Query",
      description:
        'Execute a Cube API query for advanced analytics. The query parameter can be a JSON string or object.\n\nQuery structure (see https://docs.sdelements.com/master/cubeapi/):\n- schema: Required. One of: activity, application, countermeasure, integration, library, project_survey_answers, training, trend_application, trend_projects, trend_tasks, user\n- dimensions: Required. Array like ["Application.name", "Project.id"]\n- measures: Required. Array like ["Project.count", "Task.completeCount"]\n- filters: Optional. Array of objects with member, operator (equals/contains/gt/etc), values\n- order: Optional. 2D array like [["Application.name", "asc"], ["Project.count", "desc"]]\n- limit: Optional. Number to limit results\n- time_dimensions: Optional. For Trend Reports only (trend_application, trend_projects, trend_tasks)\n\nExample: {"schema": "application", "dimensions": ["Application.name"], "measures": ["Project.count"], "limit": 10}',
      inputSchema: z.object({
        query: z
          .union([z.string(), z.record(z.string(), z.unknown())])
          .describe("Cube query (JSON string or object)"),
      }),
    },
    async ({ query }) => {
      // Parse query
      const { parsed: queryDict, error } = parseQueryParam(query);
      if (error) {
        return {
          content: [{ type: "text", text: error }],
        };
      }

      // Basic validation
      if (!queryDict!.schema) {
        return jsonToolResult({
          error:
            "Query must include 'schema' field (e.g., 'application', 'countermeasure', 'user')",
        });
      }

      if (!queryDict!.dimensions && !queryDict!.measures) {
        return jsonToolResult({
          error: "Query must include at least one of 'dimensions' or 'measures'",
        });
      }

      const result = await client.executeCubeQuery(queryDict as CubeQuery);

      return jsonToolResult(result);
    }
  );
}
