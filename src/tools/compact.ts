/**
 * Compact “router” toolset.
 *
 * Default toolset (unless SDE_TOOLSET=full), designed to minimize tool count by
 * grouping related operations under a small number of domain tools.
 *
 * Diagrams and reporting tools are intentionally omitted.
 */
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import {
  SDElementsClient,
  type SDElementsQueryParams,
  type SDElementsTaskStatus,
} from "../utils/apiClient";
import { buildParams, jsonToolResult } from "./_shared";
import { registerGenericTools } from "./generic";

/**
 * Detect profile from project name/description context.
 * Adapted from `src/tools/project.ts`.
 */
function detectProfileFromContext(
  name: string,
  description: string,
  profiles: Array<{ id: string; name: string; default?: boolean }>
): string | null {
  const context = `${name} ${description}`.toLowerCase();

  const patterns: Record<string, string[]> = {
    mobile: ["mobile", "ios", "android", "app store", "google play"],
    web: ["web", "website", "webapp", "browser"],
    api: ["api", "rest", "graphql", "microservice"],
    cloud: ["cloud", "aws", "azure", "gcp"],
  };

  for (const profile of profiles) {
    const profileName = (profile.name || "").toLowerCase();
    const keywords = patterns[profileName] || [profileName];
    for (const keyword of keywords) {
      if (context.includes(keyword)) return profile.id;
    }
  }

  return null;
}

/**
 * Normalize countermeasure ID to full format (project_id-task_id).
 * Adapted from `src/tools/countermeasures.ts`.
 */
function normalizeCountermeasureId(
  projectId: number,
  countermeasureId: number | string
): string {
  const taskId =
    typeof countermeasureId === "number" ? `T${countermeasureId}` : countermeasureId;
  if (taskId.startsWith(`${projectId}-`)) return taskId;
  return `${projectId}-${taskId}`;
}

type TaskStatusChoice = SDElementsTaskStatus & { meaning?: string };

/**
 * Resolve a status name or slug to its ID.
 * Adapted from `src/tools/countermeasures.ts`.
 */
async function resolveStatusToId(
  status: string,
  client: SDElementsClient
): Promise<string> {
  if (!status || !status.trim()) return status;

  try {
    const statusesResponse = await client.listTaskStatuses();
    const statusChoices = (statusesResponse.results || []) as TaskStatusChoice[];
    if (statusChoices.length === 0) return status;

    const statusNormalized = status.trim();
    const statusLower = statusNormalized.toLowerCase();

    if (statusNormalized.toUpperCase().startsWith("TS")) {
      for (const s of statusChoices) {
        if (s.id.toUpperCase() === statusNormalized.toUpperCase()) return s.id;
      }
      return statusNormalized;
    }

    for (const s of statusChoices) {
      const name = s.name || "";
      const slug = s.slug || "";
      const meaning = (s as TaskStatusChoice).meaning || "";
      if (
        statusLower === name.toLowerCase() ||
        statusLower === slug.toLowerCase() ||
        statusLower === meaning.toLowerCase()
      ) {
        return s.id;
      }
    }

    for (const s of statusChoices) {
      const name = s.name?.toLowerCase() || "";
      const slug = s.slug?.toLowerCase() || "";
      const meaning = (s as TaskStatusChoice).meaning?.toLowerCase() || "";
      if (
        name.startsWith(statusLower) ||
        slug.startsWith(statusLower) ||
        meaning.startsWith(statusLower) ||
        (["completed", "done", "finished"].includes(statusLower) &&
          name.includes("complete")) ||
        (["completed", "done", "finished"].includes(statusLower) && slug.includes("done"))
      ) {
        return s.id;
      }
    }

    return statusNormalized;
  } catch {
    return status.trim();
  }
}

export function registerCompactTools(
  server: McpServer,
  client: SDElementsClient
): void {
  // ---- projects ----
  server.registerTool(
    "project",
    {
      title: "Project",
      description:
        "Project operations (list/get/create/update/delete, profiles, risk policies).",
      // NOTE: We intentionally avoid z.discriminatedUnion() here because some MCP
      // clients (via SDK JSON schema conversion) fail to display any arguments.
      // Use a single object with an op enum + optional fields, and validate per-op
      // at runtime inside the handler.
      inputSchema: z.object({
        op: z
          .enum([
            "list",
            "get",
            "create",
            "update",
            "delete",
            "listProfiles",
            "listRiskPolicies",
            "getRiskPolicy",
          ])
          .describe("Operation to perform"),

        // shared query params
        page_size: z.number().optional().describe("Number of results per page"),
        include: z.string().optional().describe("Related resources to include"),
        exclude: z.string().optional().describe("Fields to exclude"),
        expand: z.string().optional().describe("Fields to expand"),

        // list filters (subset; supports SD Elements lookup patterns via string values)
        application: z.number().optional().describe("Filter by application ID"),
        name__icontains: z
          .string()
          .optional()
          .describe("Case-insensitive name contains filter"),
        slug: z.string().optional().describe("Filter by slug"),
        ordering: z
          .string()
          .optional()
          .describe("Sort field (e.g. name, created, updated; prefix with - for desc)"),
        search: z
          .string()
          .optional()
          .describe("Text search on name and profile name"),
        components: z
          .string()
          .optional()
          .describe("Comma-separated component IDs to filter by"),
        creator: z.number().optional().describe("Filter by creator user ID"),
        created: z
          .string()
          .optional()
          .describe("Created date filter (supports lookups like created__gte via api_request)"),
        updated: z
          .string()
          .optional()
          .describe("Updated date filter (supports lookups like updated__gte via api_request)"),
        active: z
          .union([z.boolean(), z.literal("all")])
          .optional()
          .describe("true/false/all (default active only)"),

        // ids / payload fields (used depending on op)
        project_id: z.number().optional().describe("Project ID"),
        application_id: z.number().optional().describe("Application ID"),
        name: z.string().optional().describe("Project name"),
        description: z.string().optional().describe("Project description"),
        profile_id: z.string().optional().describe("Profile ID"),
        risk_policy: z
          .union([z.number(), z.string()])
          .optional()
          .describe("Risk policy ID (numeric)"),
        risk_policy_id: z.number().optional().describe("Risk policy ID"),

        // create/update fields from SD Elements docs
        locked: z
          .boolean()
          .optional()
          .describe("Lock/unlock project survey (requires permission)"),
        project_locked: z
          .boolean()
          .optional()
          .describe("Lock/unlock project (requires ENABLE_PROJECT_LOCKING)"),
        archived: z.boolean().optional().describe("Archive/unarchive project"),
        tags: z.array(z.string()).optional().describe("Project tags"),
        answers: z
          .array(z.string())
          .optional()
          .describe("Survey answer IDs to apply on create/update"),
        users: z
          .array(
            z.object({
              email: z.string(),
              role: z.union([z.string(), z.null()]).optional(),
            })
          )
          .optional()
          .describe("Project users to assign: [{email, role}]"),
        groups: z
          .array(
            z.object({
              id: z.string(),
              role: z.union([z.string(), z.null()]).optional(),
            })
          )
          .optional()
          .describe("Project groups to assign: [{id, role}]"),
        custom_attributes: z
          .record(z.string(), z.unknown())
          .optional()
          .describe("Custom attributes object (case-sensitive)"),
      }),
    },
    async (args) => {
      switch (args.op) {
        case "list": {
          const params = buildParams({
            page_size: args.page_size,
            include: args.include,
            exclude: args.exclude,
            expand: args.expand,
            application: args.application,
            slug: args.slug,
            ordering: args.ordering,
            search: args.search,
            components: args.components,
            creator: args.creator,
            created: args.created,
            updated: args.updated,
            active: args.active,
            name__icontains: args.name__icontains,
          });
          return jsonToolResult(await client.listProjects(params));
        }
        case "get": {
          if (args.project_id === undefined) {
            return jsonToolResult({
              error: "project_id is required for op=get",
            });
          }
          const params = buildParams({
            page_size: args.page_size,
            include: args.include,
            exclude: args.exclude,
            expand: args.expand,
          });
          return jsonToolResult(await client.getProject(args.project_id, params));
        }
        case "listProfiles": {
          const params = args.page_size ? { page_size: args.page_size } : {};
          return jsonToolResult(await client.listProfiles(params));
        }
        case "listRiskPolicies": {
          const params = args.page_size ? { page_size: args.page_size } : {};
          return jsonToolResult(await client.listRiskPolicies(params));
        }
        case "getRiskPolicy": {
          if (args.risk_policy_id === undefined) {
            return jsonToolResult({
              error: "risk_policy_id is required for op=getRiskPolicy",
            });
          }
          const params = args.page_size ? { page_size: args.page_size } : {};
          return jsonToolResult(await client.getRiskPolicy(args.risk_policy_id, params));
        }
        case "create": {
          if (args.application_id === undefined) {
            return jsonToolResult({
              error: "application_id is required for op=create",
            });
          }
          if (!args.name) {
            return jsonToolResult({
              error: "name is required for op=create",
            });
          }
          let resolvedProfileId = args.profile_id;

          if (!resolvedProfileId) {
            const profilesResponse = await client.listProfiles({ page_size: 1000 });
            const profilesData = profilesResponse as {
              results: Array<{ id: string; name: string; default?: boolean }>;
            };
            const profiles = profilesData.results || [];

            if (profiles.length === 0) {
              return jsonToolResult({
                error: "No profiles available. Cannot create project without a profile.",
              });
            }

            const detectedProfileId = detectProfileFromContext(
              args.name,
              args.description || "",
              profiles
            );
            if (detectedProfileId) {
              resolvedProfileId = detectedProfileId;
            } else {
              const defaultProfile = profiles.find((p) => p.default);
              if (defaultProfile) {
                resolvedProfileId = defaultProfile.id;
              } else {
                return jsonToolResult({
                  error: "Profile is required. Please provide the 'profile_id' parameter.",
                  available_profiles: profiles.map((p) => ({ id: p.id, name: p.name })),
                });
              }
            }
          }

          const data: Record<string, unknown> = {
            name: args.name,
            application: args.application_id,
          };
          if (args.description) data.description = args.description;
          if (resolvedProfileId) data.profile = resolvedProfileId;

          // Docs-supported fields: https://docs.sdelements.com/master/api/docs/projects/#create-a-new-project
          if (args.locked !== undefined) data.locked = args.locked;
          if (args.risk_policy !== undefined && args.risk_policy !== null) {
            data.risk_policy =
              typeof args.risk_policy === "string"
                ? parseInt(args.risk_policy, 10)
                : args.risk_policy;
          }
          if (args.tags) data.tags = args.tags;
          if (args.answers) data.answers = args.answers;
          if (args.users) data.users = args.users;
          if (args.groups) data.groups = args.groups;
          if (args.custom_attributes) data.custom_attributes = args.custom_attributes;

          return jsonToolResult(await client.createProject(data));
        }
        case "update": {
          if (args.project_id === undefined) {
            return jsonToolResult({
              error: "project_id is required for op=update",
            });
          }
          // Validate risk_policy is numeric if provided
          let resolvedRiskPolicy: number | undefined;
          if (args.risk_policy !== undefined && args.risk_policy !== null) {
            if (typeof args.risk_policy === "string") {
              const parsed = parseInt(args.risk_policy, 10);
              if (isNaN(parsed)) {
                return jsonToolResult({
                  error: `risk_policy must be an integer ID, got string that cannot be converted: ${args.risk_policy}`,
                  suggestion: "Use op=listRiskPolicies to find the correct ID.",
                });
              }
              resolvedRiskPolicy = parsed;
            } else {
              resolvedRiskPolicy = args.risk_policy;
            }
          }

          const data: Record<string, unknown> = {};
          if (args.application_id !== undefined) data.application = args.application_id;
          if (args.profile_id !== undefined) data.profile = args.profile_id;
          if (args.name !== undefined) data.name = args.name;
          if (args.description !== undefined) data.description = args.description;
          if (resolvedRiskPolicy !== undefined) data.risk_policy = resolvedRiskPolicy;
          if (args.archived !== undefined) data.archived = args.archived;
          if (args.tags !== undefined) data.tags = args.tags;
          if (args.users !== undefined) data.users = args.users;
          if (args.groups !== undefined) data.groups = args.groups;
          if (args.answers !== undefined) data.answers = args.answers;
          if (args.custom_attributes !== undefined)
            data.custom_attributes = args.custom_attributes;
          if (args.locked !== undefined) data.locked = args.locked;
          if (args.project_locked !== undefined) data.project_locked = args.project_locked;

          if (Object.keys(data).length === 0) {
            return jsonToolResult({
              error:
                "No update data provided. Specify at least one field (application_id, profile_id, name, description, archived, tags, users, groups, risk_policy, answers, custom_attributes, locked, project_locked).",
            });
          }

          return jsonToolResult(await client.updateProject(args.project_id, data));
        }
        case "delete":
          if (args.project_id === undefined) {
            return jsonToolResult({
              error: "project_id is required for op=delete",
            });
          }
          return jsonToolResult(await client.deleteProject(args.project_id));
      }
    }
  );

  // ---- applications ----
  server.registerTool(
    "application",
    {
      title: "Application",
      description: "Application operations (list/get/create/update).",
      inputSchema: z.object({
        op: z.enum(["list", "get", "create", "update"]).describe("Operation to perform"),
        page_size: z.number().optional().describe("Number of results per page"),
        include: z.string().optional().describe("Related resources to include"),
        expand: z.string().optional().describe("Fields to expand"),

        application_id: z.number().optional().describe("Application ID"),
        name: z.string().optional().describe("Application name"),
        business_unit_id: z.number().optional().describe("Business unit ID"),
        description: z.string().optional().describe("Application description"),
      }),
    },
    async (args) => {
      switch (args.op) {
        case "list": {
          const params = buildParams({
            page_size: args.page_size,
            include: args.include,
            expand: args.expand,
          });
          return jsonToolResult(await client.listApplications(params));
        }
        case "get": {
          if (args.application_id === undefined) {
            return jsonToolResult({ error: "application_id is required for op=get" });
          }
          const params = buildParams({
            page_size: args.page_size,
            include: args.include,
            expand: args.expand,
          });
          return jsonToolResult(await client.getApplication(args.application_id, params));
        }
        case "create": {
          if (!args.name) {
            return jsonToolResult({ error: "name is required for op=create" });
          }
          if (args.business_unit_id === undefined) {
            return jsonToolResult({
              error: "business_unit_id is required for op=create",
            });
          }
          const data: Record<string, unknown> = {
            name: args.name,
            business_unit: args.business_unit_id,
          };
          if (args.description) data.description = args.description;
          return jsonToolResult(await client.createApplication(data));
        }
        case "update": {
          if (args.application_id === undefined) {
            return jsonToolResult({
              error: "application_id is required for op=update",
            });
          }
          const data: Record<string, unknown> = {};
          if (args.name !== undefined) data.name = args.name;
          if (args.description !== undefined) data.description = args.description;
          return jsonToolResult(await client.updateApplication(args.application_id, data));
        }
      }
    }
  );

  // ---- business units ----
  server.registerTool(
    "business_unit",
    {
      title: "Business Unit",
      description: "Business unit operations (list/get).",
      inputSchema: z.object({
        op: z.enum(["list", "get"]).describe("Operation to perform"),
        page_size: z.number().optional().describe("Number of results per page"),
        include: z.string().optional().describe("Related resources to include"),
        expand: z.string().optional().describe("Fields to expand"),
        business_unit_id: z.number().optional().describe("Business unit ID"),
      }),
    },
    async (args) => {
      switch (args.op) {
        case "list": {
          const params = buildParams({
            page_size: args.page_size,
            include: args.include,
            expand: args.expand,
          });
          return jsonToolResult(await client.listBusinessUnits(params));
        }
        case "get":
          if (args.business_unit_id === undefined) {
            return jsonToolResult({
              error: "business_unit_id is required for op=get",
            });
          }
          return jsonToolResult(await client.getBusinessUnit(args.business_unit_id));
      }
    }
  );

  // NOTE: intentionally no `user` or `scan` tools in compact mode.

  // ---- countermeasures ----
  server.registerTool(
    "countermeasure",
    {
      title: "Countermeasure",
      description: "Countermeasure operations (list/get/update/addNote/statusChoices).",
      inputSchema: z.object({
        op: z
          .enum(["list", "get", "update", "addNote", "statusChoices"])
          .describe("Operation to perform"),
        project_id: z.number().optional().describe("Project ID"),
        countermeasure_id: z.union([z.number(), z.string()]).optional().describe("Countermeasure ID"),
        status: z.string().optional().describe("New status (name, slug, or ID)"),
        notes: z.string().optional().describe("Status note"),
        note: z.string().optional().describe("Note text to add"),
        page_size: z.number().optional().describe("Number of results per page"),
        risk_relevant: z.boolean().optional().describe("Filter by risk relevance (default true)"),
      }),
    },
    async (args) => {
      switch (args.op) {
        case "list": {
          if (args.project_id === undefined) {
            return jsonToolResult({ error: "project_id is required for op=list" });
          }
          const params: SDElementsQueryParams = {
            risk_relevant: args.risk_relevant ?? true,
          };
          if (args.status !== undefined) params.status = args.status;
          if (args.page_size !== undefined) params.page_size = args.page_size;
          return jsonToolResult(await client.listTasks(args.project_id, params));
        }
        case "get": {
          if (args.project_id === undefined) {
            return jsonToolResult({ error: "project_id is required for op=get" });
          }
          if (args.countermeasure_id === undefined) {
            return jsonToolResult({ error: "countermeasure_id is required for op=get" });
          }
          const normalizedId = normalizeCountermeasureId(
            args.project_id,
            args.countermeasure_id
          );
          const params = { risk_relevant: args.risk_relevant ?? true };
          return jsonToolResult(
            await client.getTask(args.project_id, normalizedId, params)
          );
        }
        case "update": {
          if (args.project_id === undefined) {
            return jsonToolResult({ error: "project_id is required for op=update" });
          }
          if (args.countermeasure_id === undefined) {
            return jsonToolResult({ error: "countermeasure_id is required for op=update" });
          }
          const normalizedId = normalizeCountermeasureId(
            args.project_id,
            args.countermeasure_id
          );
          const data: Record<string, unknown> = {};
          if (args.status !== undefined) {
            data.status = await resolveStatusToId(args.status, client);
          }
          if (args.notes !== undefined) data.status_note = args.notes;
          if (Object.keys(data).length === 0) {
            return jsonToolResult({
              error: "No update data provided. Specify either 'status' or 'notes'.",
            });
          }
          return jsonToolResult(await client.updateTask(args.project_id, normalizedId, data));
        }
        case "addNote": {
          if (args.project_id === undefined) {
            return jsonToolResult({ error: "project_id is required for op=addNote" });
          }
          if (args.countermeasure_id === undefined) {
            return jsonToolResult({ error: "countermeasure_id is required for op=addNote" });
          }
          if (!args.note) {
            return jsonToolResult({ error: "note is required for op=addNote" });
          }
          const normalizedId = normalizeCountermeasureId(
            args.project_id,
            args.countermeasure_id
          );
          return jsonToolResult(
            await client.addTaskNote(args.project_id, normalizedId, args.note)
          );
        }
        case "statusChoices": {
          const result = await client.listTaskStatuses();
          return jsonToolResult({
            status_choices: result.results || [],
            status_names: (result.results || []).map((s) => s.name).filter(Boolean),
            note: "These status choices are standardized across all projects",
          });
        }
      }
    }
  );

  // ---- surveys ----
  server.registerTool(
    "survey",
    {
      title: "Survey",
      description:
        "Survey operations (get structure, get selected answers, update by IDs, mutate by text, commit draft, add question comment).",
      inputSchema: z.object({
        op: z
          .enum([
            "getProjectSurvey",
            "getAnswersForProject",
            "updateByIds",
            "findAnswers",
            "mutateByText",
            "commitDraft",
            "addQuestionComment",
          ])
          .describe("Operation to perform"),
        project_id: z.number().optional().describe("Project ID"),
        format: z
          .enum(["summary", "detailed", "grouped"])
          .optional()
          .default("summary")
          .describe("Output format for getAnswersForProject"),
        answers: z.array(z.string()).optional().describe("Answer IDs to select"),
        answers_to_deselect: z
          .array(z.string())
          .optional()
          .describe("Answer IDs to deselect"),
        survey_complete: z.boolean().optional().describe("Commit draft after update"),
        search_texts: z.array(z.string()).optional().describe("Answer texts to search for"),
        mode: z.enum(["add", "replace", "remove"]).optional().default("add"),
        texts: z.array(z.string()).optional().describe("Answer texts to add/replace/remove"),
        replace_all: z
          .boolean()
          .optional()
          .default(true)
          .describe("When mode=replace, deselect existing answers not in new list"),
        question_id: z.string().optional().describe("Survey question ID"),
        comment: z.string().optional().describe("Comment text"),
      }),
    },
    async (args) => {
      switch (args.op) {
        case "getProjectSurvey":
          if (args.project_id === undefined) {
            return jsonToolResult({ error: "project_id is required for op=getProjectSurvey" });
          }
          return jsonToolResult(await client.getProjectSurvey(args.project_id));

        case "updateByIds": {
          if (args.project_id === undefined) {
            return jsonToolResult({ error: "project_id is required for op=updateByIds" });
          }
          if (!args.answers) {
            return jsonToolResult({ error: "answers is required for op=updateByIds" });
          }
          const data = {
            answers: args.answers,
            answers_to_deselect: args.answers_to_deselect,
            survey_complete: args.survey_complete,
          };
          return jsonToolResult(await client.updateProjectSurvey(args.project_id, data));
        }

        case "findAnswers": {
          // Included for parity with existing tool signature, but search is library-scoped.
          void args.project_id;
          if (!args.search_texts) {
            return jsonToolResult({ error: "search_texts is required for op=findAnswers" });
          }
          return jsonToolResult(await client.findAnswersByText(args.search_texts));
        }

        case "mutateByText": {
          if (args.project_id === undefined) {
            return jsonToolResult({ error: "project_id is required for op=mutateByText" });
          }
          if (!args.texts) {
            return jsonToolResult({ error: "texts is required for op=mutateByText" });
          }
          if (args.mode === "add") {
            await client.loadLibraryAnswers();
            const searchResults = await client.findAnswersByText(args.texts, 0.75);

            const answerIds: string[] = [];
            const notFound: string[] = [];
            for (const [text, info] of Object.entries(searchResults)) {
              if (info?.id) answerIds.push(info.id);
              else notFound.push(text);
            }

            const addedAnswers: string[] = [];
            const failedAnswers: Array<{ text: string; error: string }> = [];
            for (const answerId of answerIds) {
              try {
                await client.addAnswerToSurveyDraft(args.project_id, answerId, true);
                addedAnswers.push(answerId);
              } catch (error) {
                const errorMsg = error instanceof Error ? error.message : String(error);
                failedAnswers.push({
                  text: args.texts[answerIds.indexOf(answerId)] ?? "",
                  error: errorMsg,
                });
              }
            }

            return jsonToolResult({
              success: addedAnswers.length > 0,
              added_count: addedAnswers.length,
              added_answers: addedAnswers,
              failed_answers: failedAnswers.length > 0 ? failedAnswers : undefined,
              not_found: notFound.length > 0 ? notFound : undefined,
              search_results: searchResults,
            });
          }

          if (args.mode === "remove") {
            const currentSurvey = await client.getProjectSurvey(args.project_id);
            const surveyData = currentSurvey as { answers?: string[] };
            const currentAnswerIds = surveyData.answers || [];

            const searchResults = await client.findAnswersByText(args.texts);
            const idsToDeselect: string[] = [];
            const notFound: string[] = [];
            for (const [text, info] of Object.entries(searchResults)) {
              if (info?.id) idsToDeselect.push(info.id);
              else notFound.push(text);
            }

            const data = {
              answers: currentAnswerIds,
              answers_to_deselect: idsToDeselect,
            };
            const updateResult = await client.updateProjectSurvey(args.project_id, data);

            const removedAnswers: Record<string, unknown> = {};
            for (const [text, info] of Object.entries(searchResults)) {
              if (info?.id) removedAnswers[text] = info;
            }

            return jsonToolResult({
              success: true,
              removed_answers: removedAnswers,
              ids_deselected: idsToDeselect,
              not_found: notFound,
              remaining_answer_count: currentAnswerIds.length - idsToDeselect.length,
              update_result: updateResult,
            });
          }

          // replace
          const replace_all = args.replace_all ?? true;
          const searchResults = await client.findAnswersByText(args.texts);

          const answerIds: string[] = [];
          const notFound: string[] = [];
          for (const [text, info] of Object.entries(searchResults)) {
            if (info?.id) answerIds.push(info.id);
            else notFound.push(text);
          }

          if (notFound.length > 0) {
            return jsonToolResult({
              error: `Could not find answers for: ${notFound.join(", ")}`,
              search_results: searchResults,
            });
          }

          let answersToDeselect: string[] | undefined;
          if (replace_all) {
            const currentSurvey = await client.getProjectSurvey(args.project_id);
            const surveyData = currentSurvey as { answers?: string[] };
            const currentAnswerIds = new Set(surveyData.answers || []);
            const newAnswerIds = new Set(answerIds);
            const toDeselect = [...currentAnswerIds].filter((id) => !newAnswerIds.has(id));
            if (toDeselect.length > 0) answersToDeselect = toDeselect;
          }

          const data = {
            answers: answerIds,
            answers_to_deselect: answersToDeselect,
            survey_complete: args.survey_complete,
          };
          const updateResult = await client.updateProjectSurvey(args.project_id, data);

          return jsonToolResult({
            success: true,
            matched_answers: searchResults,
            answer_ids_used: answerIds,
            replace_all,
            update_result: updateResult,
          });
        }

        case "getAnswersForProject": {
          if (args.project_id === undefined) {
            return jsonToolResult({
              error: "project_id is required for op=getAnswersForProject",
            });
          }
          const survey = await client.getProjectSurvey(args.project_id);
          const surveyData = survey as {
            answers?: string[];
            sections?: Array<{
              title?: string;
              questions?: Array<{
                id?: string;
                text?: string;
                answers?: Array<{ id?: string; text?: string }>;
              }>;
            }>;
          };

          const currentAnswerIds = surveyData.answers || [];
          if (currentAnswerIds.length === 0) {
            return jsonToolResult({
              project_id: args.project_id,
              message: "No answers are currently assigned to this survey",
              answer_count: 0,
            });
          }

          const answerDetails: Record<
            string,
            { text: string; question: string; section: string; question_id?: string }
          > = {};

          for (const section of surveyData.sections || []) {
            const sectionTitle = section.title || "Untitled Section";
            for (const question of section.questions || []) {
              const questionText = question.text || "Untitled Question";
              for (const answer of question.answers || []) {
                const answerId = answer.id;
                if (answerId && currentAnswerIds.includes(answerId)) {
                  answerDetails[answerId] = {
                    text: answer.text || "N/A",
                    question: questionText,
                    section: sectionTitle,
                    question_id: question.id,
                  };
                }
              }
            }
          }

          if (args.format === "summary") {
            return jsonToolResult({
              project_id: args.project_id,
              answer_count: currentAnswerIds.length,
              answers: Object.values(answerDetails).map((d) => d.text),
              answer_ids: currentAnswerIds,
            });
          }

          if (args.format === "detailed") {
            return jsonToolResult({
              project_id: args.project_id,
              answer_count: currentAnswerIds.length,
              answers: Object.entries(answerDetails).map(([aid, details]) => ({
                text: details.text,
                question: details.question,
                answer_id: aid,
              })),
            });
          }

          // grouped
          const grouped: Record<string, Array<{ question: string; answer: string }>> = {};
          for (const details of Object.values(answerDetails)) {
            const section = details.section;
            if (!grouped[section]) grouped[section] = [];
            grouped[section].push({ question: details.question, answer: details.text });
          }
          return jsonToolResult({
            project_id: args.project_id,
            answer_count: currentAnswerIds.length,
            sections: grouped,
          });
        }

        case "commitDraft":
          if (args.project_id === undefined) {
            return jsonToolResult({ error: "project_id is required for op=commitDraft" });
          }
          return jsonToolResult(await client.commitSurveyDraft(args.project_id));

        case "addQuestionComment":
          if (args.project_id === undefined) {
            return jsonToolResult({ error: "project_id is required for op=addQuestionComment" });
          }
          if (!args.question_id) {
            return jsonToolResult({ error: "question_id is required for op=addQuestionComment" });
          }
          if (!args.comment) {
            return jsonToolResult({ error: "comment is required for op=addQuestionComment" });
          }
          return jsonToolResult(
            await client.addSurveyQuestionComment(
              args.project_id,
              args.question_id,
              args.comment
            )
          );
      }
    }
  );

  // Keep the generic tools (api_request + test_connection) available in compact mode.
  registerGenericTools(server, client);
}

