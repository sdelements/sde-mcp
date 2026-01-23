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
        "Search the SD Elements library for countermeasures, threats, components, weaknesses, profiles, or risk policies. Aliases: tasks=countermeasures, problems=weaknesses.",
      inputSchema: z.object({
        query: z.string().min(1).describe("Search query text"),
        types: z
          .array(z.enum(LIBRARY_TYPES))
          .optional()
          .describe(
            "Resource types to search (default: countermeasures, threats, components, weaknesses, profiles, risk_policies; aliases: tasks=countermeasures, problems=weaknesses)"
          ),
        page_size: z.number().optional().describe("Number of results per page"),
        include: z.string().optional().describe("Related resources to include"),
        exclude: z.string().optional().describe("Fields to exclude"),
        expand: z.string().optional().describe("Fields to expand"),
        ordering: z
          .string()
          .optional()
          .describe("Sort field (e.g. name, created; prefix with - for desc)"),
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
