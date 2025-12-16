/**
 * Project-related tools
 * Translated from: https://github.com/sdelements/sde-mcp/blob/master/src/sde_mcp_server/tools/projects.py
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { SDElementsClient } from "../utils/apiClient.js";
import { extractAnswerTextsFromContext } from "../utils/mappings.js";
import { buildParams, jsonToolResult } from "./_shared.js";

// Type definitions for API responses
interface Profile {
  id: string;
  name: string;
  default?: boolean;
}

interface Application {
  id: number;
  name: string;
  description?: string;
}

interface Project {
  id: number;
  name: string;
  url?: string;
  application: number | { id: number };
}

interface BusinessUnit {
  id: number;
  name: string;
}

/**
 * Detect profile from project name/description context
 */
function detectProfileFromContext(
  name: string,
  description: string,
  profiles: Profile[]
): string | null {
  const context = `${name} ${description}`.toLowerCase();

  // Profile detection patterns
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
      if (context.includes(keyword)) {
        return profile.id;
      }
    }
  }

  return null;
}

/**
 * Register all project-related tools
 */
export function registerProjectTools(
  server: McpServer,
  client: SDElementsClient
): void {
  // List projects
  server.registerTool(
    "list_projects",
    {
      title: "List Projects",
      description: "List all projects in SD Elements",
      inputSchema: z.object({
        page_size: z.number().optional().describe("Number of results per page"),
        include: z.string().optional().describe("Related resources to include"),
        expand: z.string().optional().describe("Fields to expand"),
      }),
    },
    async ({ page_size, include, expand }) => {
      const params = buildParams({ page_size, include, expand });
      const result = await client.listProjects(params);

      return jsonToolResult(result);
    }
  );

  // Get project
  server.registerTool(
    "get_project",
    {
      title: "Get Project",
      description:
        "Get details of a specific project. Use list_countermeasures to see countermeasures for a project, not this tool.",
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project"),
        page_size: z.number().optional().describe("Number of results per page"),
        include: z.string().optional().describe("Related resources to include"),
        expand: z.string().optional().describe("Fields to expand"),
      }),
    },
    async ({ project_id, page_size, include, expand }) => {
      const params = buildParams({ page_size, include, expand });
      const result = await client.getProject(project_id, params);

      return jsonToolResult(result);
    }
  );

  // List profiles
  server.registerTool(
    "list_profiles",
    {
      title: "List Profiles",
      description: "List all available profiles in SD Elements",
      inputSchema: z.object({
        page_size: z.number().optional().describe("Number of results per page"),
      }),
    },
    async ({ page_size }) => {
      const params = page_size ? { page_size } : {};
      const result = await client.listProfiles(params);

      return jsonToolResult(result);
    }
  );

  // List risk policies
  server.registerTool(
    "list_risk_policies",
    {
      title: "List Risk Policies",
      description: "List all available risk policies in SD Elements",
      inputSchema: z.object({
        page_size: z.number().optional().describe("Number of results per page"),
      }),
    },
    async ({ page_size }) => {
      const params = page_size ? { page_size } : {};
      const result = await client.listRiskPolicies(params);

      return jsonToolResult(result);
    }
  );

  // Get risk policy
  server.registerTool(
    "get_risk_policy",
    {
      title: "Get Risk Policy",
      description: "Get details of a specific risk policy",
      inputSchema: z.object({
        risk_policy_id: z.number().describe("ID of the risk policy"),
        page_size: z.number().optional().describe("Number of results per page"),
      }),
    },
    async ({ risk_policy_id, page_size }) => {
      const params = page_size ? { page_size } : {};
      const result = await client.getRiskPolicy(risk_policy_id, params);

      return jsonToolResult(result);
    }
  );

  // Create project
  server.registerTool(
    "create_project",
    {
      title: "Create Project",
      description:
        "Create a new project in SD Elements. If name is not specified, prompts user to provide it. If profile is not specified, attempts to detect it from project name/description (e.g., 'mobile project' → Mobile profile). If detection fails, prompts user to select from available profiles.",
      inputSchema: z.object({
        application_id: z.number().describe("ID of the application"),
        name: z.string().optional().describe("Name of the project"),
        description: z
          .string()
          .optional()
          .describe("Description of the project"),
        phase_id: z.number().optional().describe("Phase ID"),
        profile_id: z.string().optional().describe("Profile ID"),
      }),
    },
    async ({ application_id, name, description, phase_id, profile_id }) => {
      // For now, name and profile_id are required (elicitation not implemented yet)
      if (!name) {
        return jsonToolResult({
          error: "Project name is required. Please provide the 'name' parameter.",
        });
      }

      let resolvedProfileId = profile_id;

      // Try to detect profile if not provided
      if (!resolvedProfileId) {
        const profilesResponse = await client.listProfiles({ page_size: 1000 });
        const profilesData = profilesResponse as { results: Profile[] };
        const profiles = profilesData.results || [];

        if (profiles.length === 0) {
          return jsonToolResult({
            error: "No profiles available. Cannot create project without a profile.",
          });
        }

        // Try to detect profile
        const detectedProfileId = detectProfileFromContext(
          name,
          description || "",
          profiles
        );

        if (detectedProfileId) {
          resolvedProfileId = detectedProfileId;
        } else {
          // Use default profile if available
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
        name,
        application: application_id,
      };

      if (description) data.description = description;
      if (phase_id) data.phase_id = phase_id;
      if (resolvedProfileId) data.profile = resolvedProfileId;

      const result = await client.createProject(data);

      return jsonToolResult(result);
    }
  );

  // Update project
  server.registerTool(
    "update_project",
    {
      title: "Update Project",
      description:
        "Update an existing project (name, description, status, or risk_policy). Use when user says 'update', 'change', 'modify', or 'rename'. Do NOT use for 'archive', 'delete', or 'remove' - use delete_project instead.\n\nIMPORTANT: risk_policy must be the numeric ID of the risk policy (e.g., 1, 2, 3), not the name. Use list_risk_policies to find the correct ID.",
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project to update"),
        name: z.string().optional().describe("New name for the project"),
        description: z.string().optional().describe("New description"),
        status: z.string().optional().describe("New status"),
        risk_policy: z
          .union([z.number(), z.string()])
          .optional()
          .describe("Risk policy ID (must be numeric)"),
      }),
    },
    async ({ project_id, name, description, status, risk_policy }) => {
      // Validate risk_policy is numeric if provided
      let resolvedRiskPolicy: number | undefined;
      if (risk_policy !== undefined && risk_policy !== null) {
        if (typeof risk_policy === "string") {
          const parsed = parseInt(risk_policy, 10);
          if (isNaN(parsed)) {
          return jsonToolResult({
            error: `risk_policy must be an integer ID, got string that cannot be converted: ${risk_policy}`,
            suggestion:
              "Use list_risk_policies to find the correct risk policy ID (numeric value)",
          });
          }
          resolvedRiskPolicy = parsed;
        } else if (typeof risk_policy === "number") {
          resolvedRiskPolicy = risk_policy;
        } else {
        return jsonToolResult({
          error: `risk_policy must be an integer ID, got ${typeof risk_policy}: ${risk_policy}`,
          suggestion:
            "Use list_risk_policies to find the correct risk policy ID (numeric value)",
        });
        }
      }

      const data: Record<string, unknown> = {};
      if (name !== undefined) data.name = name;
      if (description !== undefined) data.description = description;
      if (status !== undefined) data.status = status;
      if (resolvedRiskPolicy !== undefined)
        data.risk_policy = resolvedRiskPolicy;

      if (Object.keys(data).length === 0) {
        return jsonToolResult({
          error:
            "No update data provided. Specify at least one field to update (name, description, status, or risk_policy).",
        });
      }

      try {
        const result = await client.updateProject(project_id, data);
        return jsonToolResult(result);
      } catch (error: unknown) {
        const errorMsg = error instanceof Error ? error.message : String(error);
        if (
          errorMsg.toLowerCase().includes("risk_policy") ||
          errorMsg.toLowerCase().includes("risk policy")
        ) {
          return jsonToolResult({
            error: `Failed to update risk_policy: ${errorMsg}`,
            suggestion:
              "Use list_risk_policies to verify the risk policy ID is correct.",
          });
        }
        throw error;
      }
    }
  );

  // Delete project
  server.registerTool(
    "delete_project",
    {
      title: "Delete Project",
      description:
        "Delete a project. Use when user says 'delete', 'remove', 'archive', or wants to permanently remove a project. Do NOT use update_project for archiving.",
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project to delete"),
      }),
    },
    async ({ project_id }) => {
      const result = await client.deleteProject(project_id);

      return jsonToolResult(result);
    }
  );

  // Create project from code
  server.registerTool(
    "create_project_from_code",
    {
      title: "Create Project From Code",
      description:
        "Create application and project in SD Elements. Returns the project survey structure with all available questions and answers.\n\nIMPORTANT: Before determining survey answers, the AI client MUST search the workspace codebase for evidence of survey answers and security requirements.",
      inputSchema: z.object({
        application_id: z
          .number()
          .optional()
          .describe("ID of existing application"),
        application_name: z
          .string()
          .optional()
          .describe("Name for new application"),
        application_description: z
          .string()
          .optional()
          .describe("Description for new application"),
        business_unit_id: z.number().optional().describe("Business unit ID"),
        business_unit_name: z
          .string()
          .optional()
          .describe("Business unit name"),
        project_name: z.string().optional().describe("Name of the project"),
        project_description: z
          .string()
          .optional()
          .describe("Description of the project"),
        profile_id: z.string().optional().describe("Profile ID"),
        reuse_existing_project: z
          .boolean()
          .optional()
          .default(false)
          .describe("Reuse existing project if found"),
      }),
    },
    async ({
      application_id,
      application_name,
      application_description,
      business_unit_id,
      business_unit_name,
      project_name,
      project_description,
      profile_id,
      reuse_existing_project = false,
    }) => {
      try {
        let applicationIdResolved = application_id;
        let applicationWasExisting = false;
        let appResult: Application | null = null;

        // Resolve application
        if (!applicationIdResolved) {
          if (application_name) {
            // Check for existing application
            const appsResponse = await client.listApplications({
              page_size: 1000,
            });
            const appsData = appsResponse as { results: Application[] };
            const apps = appsData.results || [];
            const existingApp = apps.find(
              (app) =>
                app.name?.trim().toLowerCase() ===
                application_name.trim().toLowerCase()
            );

            if (existingApp) {
              applicationIdResolved = existingApp.id;
              appResult = existingApp;
              applicationWasExisting = true;
            } else {
              // Create new application
              let businessUnitIdResolved = business_unit_id;

              if (!businessUnitIdResolved && business_unit_name) {
                const busResponse = await client.listBusinessUnits({
                  page_size: 1000,
                });
                const busData = busResponse as { results: BusinessUnit[] };
                const businessUnits = busData.results || [];
                const matchingBu = businessUnits.find(
                  (bu) =>
                    bu.name?.trim().toLowerCase() ===
                    business_unit_name.trim().toLowerCase()
                );
                if (matchingBu) {
                  businessUnitIdResolved = matchingBu.id;
                }
              }

              if (!businessUnitIdResolved) {
                try {
                  const currentUser = await client.getCurrentUser();
                  const userData = currentUser as {
                    business_unit: number | { id: number };
                  };
                  const userBusinessUnit = userData.business_unit;
                  if (userBusinessUnit) {
                    businessUnitIdResolved =
                      typeof userBusinessUnit === "object"
                        ? userBusinessUnit.id
                        : userBusinessUnit;
                  }
                } catch {
                  // Ignore error
                }
              }

              if (!businessUnitIdResolved) {
                const busResponse = await client.listBusinessUnits({
                  page_size: 1000,
                });
                const busData = busResponse as { results: BusinessUnit[] };
                const businessUnits = busData.results || [];
                if (businessUnits.length > 0) {
                  businessUnitIdResolved = businessUnits[0].id;
                }
              }

              if (!businessUnitIdResolved) {
                return {
                  content: [
                    {
                      type: "text",
                      text: JSON.stringify(
                        {
                          error:
                            "Cannot create application: No business unit found",
                        },
                        null,
                        2
                      ),
                    },
                  ],
                };
              }

              const appData: Record<string, unknown> = {
                name: application_name,
                business_unit: businessUnitIdResolved,
              };
              if (application_description) {
                appData.description = application_description;
              }

              const appCreateResult = await client.createApplication(appData);
              appResult = appCreateResult as Application;
              applicationIdResolved = appResult.id;
            }
          } else {
            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(
                    {
                      error:
                        "Either application_id or application_name must be provided",
                    },
                    null,
                    2
                  ),
                },
              ],
            };
          }
        } else {
          applicationWasExisting = true;
        }

        // Resolve profile
        let profileIdResolved = profile_id;
        let profileDetected = false;
        let profileName: string | null = null;

        if (!profileIdResolved) {
          const profilesResponse = await client.listProfiles({
            page_size: 1000,
          });
          const profilesData = profilesResponse as { results: Profile[] };
          const profiles = profilesData.results || [];

          if (profiles.length > 0) {
            const detectedProfileId = detectProfileFromContext(
              project_name || "",
              project_description || "",
              profiles
            );

            if (detectedProfileId) {
              profileIdResolved = detectedProfileId;
              profileDetected = true;
              const profile = profiles.find((p) => p.id === profileIdResolved);
              if (profile) {
                profileName = profile.name || "Unknown";
              }
            } else {
              // Use default profile
              const defaultProfile = profiles.find((p) => p.default);
              if (defaultProfile) {
                profileIdResolved = defaultProfile.id;
                profileName = defaultProfile.name;
              }
            }
          } else {
            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(
                    {
                      error:
                        "No profiles available. Cannot create project without a profile.",
                    },
                    null,
                    2
                  ),
                },
              ],
            };
          }
        }

        // Check for existing project
        let existingProject: Project | null = null;
        let projectWasExisting = false;

        try {
          const projectsResponse = await client.listProjects({
            page_size: 1000,
          });
          const projectsData = projectsResponse as { results: Project[] };
          const projects = projectsData.results || [];

          for (const proj of projects) {
            const projApp = proj.application;
            const projAppId =
              typeof projApp === "object" ? projApp.id : projApp;

            if (
              projAppId === applicationIdResolved &&
              proj.name?.trim().toLowerCase() ===
                project_name?.trim().toLowerCase()
            ) {
              existingProject = proj;
              break;
            }
          }
        } catch (error) {
          console.error("Warning: Could not list existing projects:", error);
        }

        let projectResult: Project;
        let projectId: number;

        if (existingProject) {
          if (reuse_existing_project) {
            projectResult = existingProject;
            projectId = projectResult.id;
            projectWasExisting = true;
          } else {
            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(
                    {
                      error: `A project with the name '${project_name}' already exists in this application (ID: ${existingProject.id}).`,
                      existing_project_id: existingProject.id,
                      suggestion:
                        "Either provide a different project_name, or set reuse_existing_project=true to reuse the existing project.",
                    },
                    null,
                    2
                  ),
                },
              ],
            };
          }
        } else {
          // Create project
          const projectData: Record<string, unknown> = {
            name: project_name || "New Project",
            application: applicationIdResolved,
          };

          if (project_description) {
            projectData.description = project_description;
          }
          if (profileIdResolved) {
            projectData.profile = profileIdResolved;
          }

          const projectCreateResult = await client.createProject(projectData);
          projectResult = projectCreateResult as Project;
          projectId = projectResult.id;
          projectWasExisting = false;
        }

        // Get survey structure
        const surveyStructure = await client.getProjectSurvey(projectId);

        // Load library answers
        await client.loadLibraryAnswers();
        const libraryAnswers = client.getLibraryAnswersCache() || [];

        interface LibraryAnswer {
          id: string;
          text?: string;
          display_text?: string;
          section?: string;
        }

        const availableAnswersSummary = libraryAnswers
          .slice(0, 100)
          .map((answer: LibraryAnswer) => ({
            id: answer.id,
            text: answer.text || "",
            question: answer.display_text || "",
            section: answer.section || "",
          }));

        // Suggested answers from context (mirrors Python extract_answer_texts_from_context)
        const contextForMatching = [
          project_description || "",
          application_description || "",
          project_name || "",
        ]
          .filter(Boolean)
          .join(" ");

        const matchedAnswerTexts = extractAnswerTextsFromContext(
          contextForMatching,
          libraryAnswers
        );

        const matchedAnswers = libraryAnswers
          .filter(
            (ans) =>
              ans.text &&
              matchedAnswerTexts.includes(ans.text) &&
              ans.id
          )
          .slice(0, 50)
          .map((ans) => ({
            id: ans.id,
            text: ans.text as string,
            question: ans.display_text || "",
            section: ans.section || "",
          }));

        // Get draft state
        interface DraftAnswer {
          selected?: boolean;
        }

        interface DraftState {
          answers?: DraftAnswer[];
          error?: string;
        }

        let draftState: DraftState | null = null;
        let selectedAnswersCount = 0;

        try {
          const draftResponse = await client.get(
            `projects/${projectId}/survey/draft/`
          );
          draftState = draftResponse as DraftState;
          const selectedAnswers = (draftState.answers || []).filter(
            (a) => a.selected
          );
          selectedAnswersCount = selectedAnswers.length;
        } catch (error) {
          draftState = { error: String(error) };
        }

        interface SurveySection {
          questions?: unknown[];
        }

        interface SurveyStructure {
          sections?: SurveySection[];
        }

        const surveyData = surveyStructure as SurveyStructure;
        const totalQuestions =
          surveyData.sections?.reduce(
            (sum, s) => sum + (s.questions?.length || 0),
            0
          ) || 0;

        const result = {
          success: true,
          application: {
            id: applicationIdResolved,
            name: appResult?.name || application_name || "unknown",
            was_existing: applicationWasExisting,
          },
          project: {
            id: projectId,
            name: projectResult.name,
            url: projectResult.url,
            was_existing: projectWasExisting,
          },
          profile: profileIdResolved
            ? {
                id: profileIdResolved,
                name: profileName,
                detected: profileDetected,
              }
            : null,
          survey_structure: {
            note: "This contains all available survey questions and answers. Review these options and use your AI knowledge to determine which answers are appropriate for this project.",
            total_questions: totalQuestions,
            total_answers: libraryAnswers.length,
            available_answers: availableAnswersSummary,
            suggested_answers_from_context: matchedAnswers,
            full_survey: surveyStructure,
          },
          survey_draft_state: {
            selected_answers_count: selectedAnswersCount,
            has_answers: selectedAnswersCount > 0,
            draft_available: draftState !== null && !draftState.error,
          },
          next_steps: {
            step_1:
              "Review the survey_structure to see all available questions and answers",
            step_2:
              "Use your AI knowledge to determine appropriate answers based on the project context",
            step_3:
              "Call add_survey_answers_by_text or set_project_survey_by_text to set the answers",
            step_4:
              "Call commit_survey_draft to publish the survey and generate countermeasures",
            important:
              "The survey draft is NOT committed automatically. You must commit it after setting answers.",
          },
        };

        return {
          content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
        };
      } catch (error: unknown) {
        const errorMessage =
          error instanceof Error ? error.message : String(error);
        const errorType =
          error instanceof Error ? error.constructor.name : typeof error;

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  error: errorMessage,
                  error_type: errorType,
                },
                null,
                2
              ),
            },
          ],
        };
      }
    }
  );
}
