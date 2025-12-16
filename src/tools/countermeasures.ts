/**
 * Countermeasure-related tools
 * Translated from: https://github.com/sdelements/sde-mcp/blob/master/src/sde_mcp_server/tools/countermeasures.py
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import {
  SDElementsClient,
  type SDElementsQueryParams,
  type SDElementsTaskStatus,
} from "../utils/apiClient.js";
import { jsonToolResult } from "./_shared.js";

/**
 * Normalize countermeasure ID to full format (project_id-task_id).
 *
 * Accepts:
 * - Integer: 21 -> "T21" -> "{project_id}-T21"
 * - String starting with "T": "T21" -> "{project_id}-T21"
 * - String in full format: "31244-T21" -> "31244-T21" (as-is)
 */
function normalizeCountermeasureId(
  projectId: number,
  countermeasureId: number | string
): string {
  let taskId: string;

  // If integer, convert to "T{number}" format
  if (typeof countermeasureId === "number") {
    taskId = `T${countermeasureId}`;
  } else {
    // Already a string
    taskId = countermeasureId;
  }

  // If already in full format (contains project_id), return as-is
  if (taskId.startsWith(`${projectId}-`)) {
    return taskId;
  }

  // Otherwise, construct full format
  return `${projectId}-${taskId}`;
}

type TaskStatusChoice = SDElementsTaskStatus & { meaning?: string };

/**
 * Resolve a status name or slug to its ID.
 *
 * The API requires status IDs (e.g., "TS1", "TS2") not names (e.g., "Complete").
 * This function looks up the status ID from the task-statuses endpoint.
 */
async function resolveStatusToId(
  status: string,
  client: SDElementsClient
): Promise<string> {
  if (!status || !status.trim()) {
    return status;
  }

  try {
    // Get all available statuses
    const statusesResponse = await client.listTaskStatuses();
    const statusChoices = (statusesResponse.results ||
      []) as TaskStatusChoice[];

    if (statusChoices.length === 0) {
      // If we can't get statuses, return original (might already be an ID)
      return status;
    }

    // Normalize input for comparison
    const statusNormalized = status.trim();
    const statusLower = statusNormalized.toLowerCase();

    // Check if it's already an ID (starts with "TS")
    if (statusNormalized.toUpperCase().startsWith("TS")) {
      // Verify it's a valid ID
      for (const s of statusChoices) {
        if (s.id.toUpperCase() === statusNormalized.toUpperCase()) {
          return s.id;
        }
      }
      return statusNormalized; // Return as-is if not found
    }

    // Try to match by exact name, slug, or meaning first (most reliable)
    for (const statusObj of statusChoices) {
      const name = statusObj.name || "";
      const slug = statusObj.slug || "";
      const meaning = statusObj.meaning || "";
      const statusId = statusObj.id || "";

      // Exact matches (case-insensitive)
      if (
        statusLower === name.toLowerCase() ||
        statusLower === slug.toLowerCase() ||
        statusLower === meaning.toLowerCase()
      ) {
        return statusId;
      }
    }

    // Try partial/fuzzy matching as fallback
    for (const statusObj of statusChoices) {
      const name = statusObj.name?.toLowerCase() || "";
      const slug = statusObj.slug?.toLowerCase() || "";
      const meaning = statusObj.meaning?.toLowerCase() || "";
      const statusId = statusObj.id || "";

      // Check if normalized input matches the start of name/slug/meaning
      if (
        name.startsWith(statusLower) ||
        slug.startsWith(statusLower) ||
        meaning.startsWith(statusLower) ||
        // Handle common variations
        (["completed", "done", "finished"].includes(statusLower) &&
          name.includes("complete")) ||
        (["completed", "done", "finished"].includes(statusLower) &&
          slug.includes("done"))
      ) {
        return statusId;
      }
    }

    // If no match found, return original
    return statusNormalized;
  } catch {
    // If lookup fails, return original value
    return status.trim();
  }
}

/**
 * Register all countermeasure-related tools
 */
export function registerCountermeasureTools(
  server: McpServer,
  client: SDElementsClient
): void {
  // List countermeasures
  server.registerTool(
    "list_countermeasures",
    {
      title: "List Countermeasures",
      description:
        "List all countermeasures for a project. Use this to see countermeasures associated with a project, not get_project which returns project details.",
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project"),
        status: z.string().optional().describe("Filter by status"),
        page_size: z.number().optional().describe("Number of results per page"),
        risk_relevant: z
          .boolean()
          .optional()
          .default(true)
          .describe("Filter by risk relevance"),
      }),
    },
    async ({ project_id, status, page_size, risk_relevant = true }) => {
      const params: SDElementsQueryParams = {
        risk_relevant,
      };

      if (status !== undefined) {
        params.status = status;
      }
      if (page_size !== undefined) {
        params.page_size = page_size;
      }

      const result = await client.listTasks(project_id, params);

      return jsonToolResult(result);
    }
  );

  // Get countermeasure
  server.registerTool(
    "get_countermeasure",
    {
      title: "Get Countermeasure",
      description:
        'Get details of a SPECIFIC countermeasure by its ID. Use this when the user asks about a particular countermeasure (e.g., "countermeasure 123", "T21", "countermeasure 456"). Accepts countermeasure ID as integer (e.g., 21) or string (e.g., "T21" or "31244-T21"). Filter by risk relevance - if true, only return risk-relevant countermeasures. Defaults to true. Do NOT use this tool when the user asks about available status choices or what statuses are valid - use get_task_status_choices instead.',
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project"),
        countermeasure_id: z
          .union([z.number(), z.string()])
          .describe("ID of the countermeasure"),
        risk_relevant: z
          .boolean()
          .optional()
          .default(true)
          .describe("Filter by risk relevance"),
      }),
    },
    async ({ project_id, countermeasure_id, risk_relevant = true }) => {
      const normalizedId = normalizeCountermeasureId(
        project_id,
        countermeasure_id
      );
      const params = { risk_relevant };

      const result = await client.getTask(project_id, normalizedId, params);

      return jsonToolResult(result);
    }
  );

  // Update countermeasure
  server.registerTool(
    "update_countermeasure",
    {
      title: "Update Countermeasure",
      description:
        "Update a countermeasure (status or notes). Use when user says 'update status', 'mark as complete', or 'change status'. Do NOT use for 'add note', 'document', or 'note' - use add_countermeasure_note instead. Accepts countermeasure ID as integer (e.g., 21) or string (e.g., \"T21\" or \"31244-T21\").\n\nStatus can be provided as name (e.g., 'Complete', 'Not Applicable'), slug (e.g., 'DONE', 'NA'), or ID (e.g., 'TS1'). The tool will automatically resolve names/slugs to the correct status ID required by the API.\n\nIMPORTANT: The 'notes' parameter sets a status_note, which is only saved when the status actually changes. If the countermeasure already has the target status, use add_countermeasure_note instead to add a note, or change the status to a different value first, then back to the target status to trigger saving the status_note.",
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project"),
        countermeasure_id: z
          .union([z.number(), z.string()])
          .describe("ID of the countermeasure"),
        status: z
          .string()
          .optional()
          .describe("New status (name, slug, or ID)"),
        notes: z
          .string()
          .optional()
          .describe("Status note (only saved when status changes)"),
      }),
    },
    async ({ project_id, countermeasure_id, status, notes }) => {
      const normalizedId = normalizeCountermeasureId(
        project_id,
        countermeasure_id
      );
      const data: Record<string, unknown> = {};

      if (status !== undefined) {
        // Resolve status name/slug to ID
        const statusId = await resolveStatusToId(status, client);

        // Validate that we got a proper status ID
        if (
          !statusId.toUpperCase().startsWith("TS") &&
          statusId.toLowerCase() === status.trim().toLowerCase()
        ) {
          // The status wasn't converted - couldn't find a match
          try {
            const statusesResponse = await client.listTaskStatuses();
            const statusChoices = statusesResponse.results || [];
            const availableStatuses = statusChoices
              .map((s) => s.name)
              .slice(0, 10);

            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(
                    {
                      error: `Could not resolve status '${status}' to a status ID. The API requires status IDs (e.g., 'TS1', 'TS2'), not names.`,
                      provided_status: status,
                      available_status_names: availableStatuses,
                      suggestion:
                        "Use get_task_status_choices to see all available statuses and their IDs.",
                    },
                    null,
                    2
                  ),
                },
              ],
            };
          } catch {
            return jsonToolResult({
              error: `Could not resolve status '${status}' to a status ID. The API requires status IDs (e.g., 'TS1', 'TS2'), not names like '${status}'.`,
              provided_status: status,
              suggestion:
                "Use get_task_status_choices to see all available statuses and their IDs.",
            });
          }
        }

        data.status = statusId;
      }

      if (notes !== undefined) {
        data.status_note = notes;
      }

      if (Object.keys(data).length === 0) {
        return jsonToolResult({
          error: "No update data provided. Specify either 'status' or 'notes'.",
        });
      }

      const result = await client.updateTask(project_id, normalizedId, data);

      return jsonToolResult(result);
    }
  );

  // Add countermeasure note
  server.registerTool(
    "add_countermeasure_note",
    {
      title: "Add Countermeasure Note",
      description:
        "Add a note to a countermeasure. Use when user says 'add note', 'document', 'note that', 'record that', or wants to add documentation. Use update_countermeasure if user wants to change status. Accepts countermeasure ID as integer (e.g., 21) or string (e.g., \"T21\" or \"31244-T21\").\n\nIMPORTANT: Use this tool when adding notes to countermeasures that already have the target status. The update_countermeasure tool's 'notes' parameter only saves status_note when the status actually changes. For countermeasures that already have the desired status, always use add_countermeasure_note to ensure the note is saved.",
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project"),
        countermeasure_id: z
          .union([z.number(), z.string()])
          .describe("ID of the countermeasure"),
        note: z.string().describe("Note text to add"),
      }),
    },
    async ({ project_id, countermeasure_id, note }) => {
      const normalizedId = normalizeCountermeasureId(
        project_id,
        countermeasure_id
      );
      const result = await client.addTaskNote(project_id, normalizedId, note);

      return jsonToolResult(result);
    }
  );

  // Get task status choices
  server.registerTool(
    "get_task_status_choices",
    {
      title: "Get Task Status Choices",
      description:
        "Get the complete list of ALL available task status choices. Returns all valid status values that can be used when updating countermeasures (e.g., 'Complete', 'Not Applicable', 'In Progress', 'DONE', 'NA'). Use this tool when the user asks: \"What task statuses are available?\", \"What statuses can I use?\", \"Show me valid status values\", \"What status values are valid for countermeasures?\", or any question about available/valid status options. Task statuses are standardized across all projects. This tool returns the list of possible statuses, NOT the status of a specific countermeasure. For a specific countermeasure's status, use get_countermeasure instead.",
      inputSchema: z.object({}),
    },
    async () => {
      const result = await client.listTaskStatuses();

      // Format the response to match Python's get_task_status_choices format
      const formattedResult = {
        status_choices: result.results || [],
        status_names: (result.results || [])
          .map((s) => s.name)
          .filter(Boolean),
        note: "These status choices are standardized across all projects",
      };

      return {
        content: [
          { type: "text", text: JSON.stringify(formattedResult, null, 2) },
        ],
      };
    }
  );
}
