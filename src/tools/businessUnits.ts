/**
 * Business unit-related tools
 * Translated from: https://github.com/sdelements/sde-mcp/blob/master/src/sde_mcp_server/tools/business_units.py
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { SDElementsClient } from "../utils/apiClient";
import { buildParams, jsonToolResult } from "./_shared";

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

  // Create business unit
  server.registerTool(
    "create_business_unit",
    {
      title: "Create Business Unit",
      description:
        "Create a new business unit. Client should ask for confirmation before running.",
      inputSchema: z.object({
        name: z.string().describe("Name of the business unit"),
        users: z
          .array(z.object({ email: z.string() }))
          .optional()
          .describe("Users to include in the business unit: [{email}]"),
        groups: z
          .array(z.object({ id: z.string() }))
          .optional()
          .describe("Groups to include in the business unit: [{id}]"),
        default_users: z
          .array(z.object({ email: z.string(), role: z.string().optional() }))
          .optional()
          .describe("Default user roles: [{email, role}]"),
        default_groups: z
          .array(z.object({ id: z.string(), role: z.string().optional() }))
          .optional()
          .describe("Default group roles: [{id, role}]"),
        all_users: z
          .boolean()
          .optional()
          .describe("Whether the business unit includes all users"),
        persist_phases: z
          .boolean()
          .optional()
          .describe("Persist phases for tasks/weaknesses in this business unit"),
        default_risk_policy: z
          .number()
          .optional()
          .describe("Default risk policy ID for this business unit"),
      }),
    },
    async ({
      name,
      users,
      groups,
      default_users,
      default_groups,
      all_users,
      persist_phases,
      default_risk_policy,
    }) => {
      const data: Record<string, unknown> = { name };
      if (users) data.users = users;
      if (groups) data.groups = groups;
      if (default_users) data.default_users = default_users;
      if (default_groups) data.default_groups = default_groups;
      if (all_users !== undefined) data.all_users = all_users;
      if (persist_phases !== undefined) data.persist_phases = persist_phases;
      if (default_risk_policy !== undefined)
        data.default_risk_policy = default_risk_policy;

      const result = await client.createBusinessUnit(data);
      return jsonToolResult(result);
    }
  );

  // Update business unit
  server.registerTool(
    "update_business_unit",
    {
      title: "Update Business Unit",
      description:
        "Update an existing business unit. Client should ask for confirmation before running.",
      inputSchema: z.object({
        business_unit_id: z.number().describe("ID of the business unit"),
        name: z.string().optional().describe("Business unit name"),
        users: z
          .array(z.object({ email: z.string() }))
          .optional()
          .describe("Users to include in the business unit: [{email}]"),
        groups: z
          .array(z.object({ id: z.string() }))
          .optional()
          .describe("Groups to include in the business unit: [{id}]"),
        default_users: z
          .array(z.object({ email: z.string(), role: z.string().optional() }))
          .optional()
          .describe("Default user roles: [{email, role}]"),
        default_groups: z
          .array(z.object({ id: z.string(), role: z.string().optional() }))
          .optional()
          .describe("Default group roles: [{id, role}]"),
        all_users: z
          .boolean()
          .optional()
          .describe("Whether the business unit includes all users"),
        persist_phases: z
          .boolean()
          .optional()
          .describe("Persist phases for tasks/weaknesses in this business unit"),
        default_risk_policy: z
          .number()
          .optional()
          .describe("Default risk policy ID for this business unit"),
      }),
    },
    async ({
      business_unit_id,
      name,
      users,
      groups,
      default_users,
      default_groups,
      all_users,
      persist_phases,
      default_risk_policy,
    }) => {
      const data: Record<string, unknown> = {};
      if (name !== undefined) data.name = name;
      if (users !== undefined) data.users = users;
      if (groups !== undefined) data.groups = groups;
      if (default_users !== undefined) data.default_users = default_users;
      if (default_groups !== undefined) data.default_groups = default_groups;
      if (all_users !== undefined) data.all_users = all_users;
      if (persist_phases !== undefined) data.persist_phases = persist_phases;
      if (default_risk_policy !== undefined)
        data.default_risk_policy = default_risk_policy;

      if (Object.keys(data).length === 0) {
        return jsonToolResult({
          error:
            "No update data provided. Specify at least one field (name, users, groups, default_users, default_groups, all_users, persist_phases, default_risk_policy).",
        });
      }

      const result = await client.updateBusinessUnit(business_unit_id, data);
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
