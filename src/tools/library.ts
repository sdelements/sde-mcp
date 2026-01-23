import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { SDElementsClient, type SDElementsLibraryType } from "../utils/apiClient";
import { buildParams, jsonToolResult } from "./_shared";

const LIBRARY_TYPES = [
  "countermeasures",
  "threats",
  "components",
  "weaknesses",
  "profiles",
  "risk_policies",
  "answers",
  "task_statuses",
  "implementations",
] as const satisfies readonly SDElementsLibraryType[];

function normalizeLibraryType(type: SDElementsLibraryType): SDElementsLibraryType {
  if (type === "tasks") return "countermeasures";
  if (type === "problems") return "weaknesses";
  return type;
}

export function registerLibraryTools(
  server: McpServer,
  client: SDElementsClient
): void {
  server.registerTool(
    "library_search",
    {
      title: "Library Search",
      description:
        "Search the SD Elements library for countermeasures, threats, components, weaknesses, profiles, risk policies, answers, countermeasure statuses, or countermeasure how-tos (implementations). Aliases: tasks=countermeasures, problems=weaknesses, implementations=how-tos.",
      inputSchema: z.object({
        query: z.string().min(1).describe("Search query text"),
        types: z
          .array(z.enum(LIBRARY_TYPES))
          .optional()
          .describe(
            "Resource types to search (default: countermeasures, threats, components, weaknesses, profiles, risk_policies, answers, task_statuses, implementations; aliases: tasks=countermeasures, problems=weaknesses)"
          ),
        page_size: z.number().optional().describe("Number of results per page"),
        include: z.string().optional().describe("Related resources to include"),
        exclude: z.string().optional().describe("Fields to exclude"),
        expand: z.string().optional().describe("Fields to expand"),
        ordering: z
          .string()
          .optional()
          .describe("Sort field (e.g. name, created; prefix with - for desc)"),
        task_id: z
          .string()
          .optional()
          .describe("Library countermeasure ID (for implementations)"),
        implementation_id: z
          .string()
          .optional()
          .describe("Implementation ID (for a specific how-to)"),
        active: z
          .boolean()
          .optional()
          .describe("Filter by active status (implementations)"),
        show_original: z
          .boolean()
          .optional()
          .describe("Return original content for built-in modified how-tos"),
        filters: z
          .record(z.string(), z.union([z.string(), z.number(), z.boolean()]))
          .optional()
          .describe("Additional filter params (e.g. name__icontains)"),
      }),
    },
    async (args) => {
      const requestedTypes = args.types?.length ? args.types : LIBRARY_TYPES;
      const types = requestedTypes.map(normalizeLibraryType);
      const params = buildParams({
        page_size: args.page_size,
        include: args.include,
        exclude: args.exclude,
        expand: args.expand,
        ordering: args.ordering,
        search: args.query,
        active: args.active,
        show_original: args.show_original,
        ...(args.filters || {}),
      });
      const query = args.query.trim();
      const queryLower = query.toLowerCase();

      const results = await Promise.all(
        types.map(async (type) => {
          try {
            if (type === "risk_policies") {
              if (/^\d+$/.test(query)) {
                const data = await client.getRiskPolicy(Number(query), {
                  page_size: args.page_size,
                });
                return [type, data] as const;
              }
              const riskPolicyParams =
                queryLower === "all" || queryLower === "*"
                  ? buildParams({
                      page_size: args.page_size,
                      include: args.include,
                      exclude: args.exclude,
                      expand: args.expand,
                      ordering: args.ordering,
                      ...(args.filters || {}),
                    })
                  : params;
              const data = await client.listRiskPolicies(riskPolicyParams);
              return [type, data] as const;
            }
            if (type === "task_statuses") {
              const data = await client.listTaskStatuses(params);
              return [type, data] as const;
            }
            if (type === "implementations") {
              if (!args.task_id) {
                return [type, { error: "task_id is required for implementations" }] as const;
              }
              const implParams = buildParams({
                page_size: args.page_size,
                include: args.include,
                ordering: args.ordering,
                active: args.active,
                show_original: args.show_original,
                ...(args.filters || {}),
              });
              if (args.implementation_id) {
                const data = await client.getLibraryTaskImplementation(
                  args.task_id,
                  args.implementation_id,
                  implParams
                );
                return [type, data] as const;
              }
              const data = await client.listLibraryTaskImplementations(
                args.task_id,
                implParams
              );
              return [type, data] as const;
            }
            const data = await client.listLibraryItems(type, params);
            return [type, data] as const;
          } catch (error) {
            const msg = error instanceof Error ? error.message : String(error);
            return [type, { error: msg }] as const;
          }
        })
      );

      return jsonToolResult({
        query: args.query,
        types,
        requested_types: requestedTypes,
        results: Object.fromEntries(results),
        params,
      });
    }
  );
}
