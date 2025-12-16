/**
 * SD Elements API Client (TypeScript)
 * Based on SD Elements API v2 Documentation: https://docs.sdelements.com/master/api/
 */

// --- Interfaces & Types ---

export interface SDElementsConfig {
  host: string;
  apiKey: string;
  timeout?: number;
}

export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

/**
 * SD Elements API Query Parameters
 * Supports: pagination, include, exclude, expand, and custom filtering
 * Reference: https://docs.sdelements.com/master/api/#introduction
 */
export interface SDElementsQueryParams {
  // Pagination parameters
  page?: number;
  page_size?: number;
  cursor?: string;

  // Field manipulation parameters
  include?: string; // Comma-separated list of fields to include
  exclude?: string; // Comma-separated list of fields to exclude
  expand?: string; // Comma-separated list of fields to expand

  // Custom filtering (dynamic field names with lookups)
  // Examples: name__iexact, id__in, created__gte, etc.
  [key: string]: string | number | boolean | undefined;
}

/**
 * SD Elements API Default Pagination Response
 * Reference: https://docs.sdelements.com/master/api/#default-pagination
 */
export interface SDElementsPaginatedResponse<T = unknown> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface RequestOptions {
  params?: Record<string, string | number | boolean | undefined>;
  data?: unknown;
  headers?: Record<string, string>;
}

export interface SurveyUpdatePayload {
  answers: string[];
  answers_to_deselect?: string[];
  survey_complete?: boolean;
}

export interface SurveyUpdateResult {
  success: boolean;
  selectedCount: number;
  deselectedCount: number;
  targetAnswers: string[];
  deselectedAnswers: string[] | null;
  missingAnswers: string[] | null;
  errors: string[] | null;
  draftCommitted: boolean;
  commitResult?: unknown;
  commitError?: string;
  note?: string;
}

export interface AnswerMatch {
  id: string;
  text: string;
  question: string;
  matchType: "exact" | "substring" | "fuzzy" | "none";
  similarity: number;
}

export interface CubeQuery {
  schema: string;
  dimensions?: string[];
  measures?: string[];
  filters?: Array<{ member: string; operator: string; values?: string[] }>;
  order?: Array<[string, "asc" | "desc"]>;
  limit?: number;
  [key: string]: unknown;
}

// --- SD Elements API Resource Interfaces ---
// Based on: https://docs.sdelements.com/master/api/

export interface SDElementsProject {
  id: number;
  name: string;
  slug: string;
  description?: string;
  application: number | SDElementsApplication;
  profile: string | SDElementsProfile;
  phase?: number | SDElementsPhase;
  status?: string;
  priority?: string;
  risk_policy?: number | SDElementsRiskPolicy;
  created?: string;
  last_modified?: string;
  url?: string;
  [key: string]: unknown;
}

export interface SDElementsApplication {
  id: number;
  name: string;
  slug: string;
  description?: string;
  business_unit: number | SDElementsBusinessUnit;
  created?: string;
  last_modified?: string;
  url?: string;
  [key: string]: unknown;
}

export interface SDElementsBusinessUnit {
  id: number;
  name: string;
  slug: string;
  description?: string;
  created?: string;
  last_modified?: string;
  url?: string;
  [key: string]: unknown;
}

export interface SDElementsProfile {
  id: string;
  name: string;
  description?: string;
  default?: boolean;
  [key: string]: unknown;
}

export interface SDElementsPhase {
  id: number;
  name: string;
  slug: string;
  order?: number;
  [key: string]: unknown;
}

export interface SDElementsRiskPolicy {
  id: number;
  name: string;
  description?: string;
  [key: string]: unknown;
}

export interface SDElementsUser {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active?: boolean;
  business_unit?: number | SDElementsBusinessUnit;
  role?: string;
  [key: string]: unknown;
}

export interface SDElementsTask {
  id: string; // Format: "projectId-TtaskNumber" e.g., "123-T456"
  title: string;
  description?: string;
  status: string;
  phase?: string;
  priority?: string;
  assigned_to?: number | SDElementsUser;
  project: number | SDElementsProject;
  [key: string]: unknown;
}

export interface SDElementsTaskStatus {
  id: string;
  name: string;
  slug: string;
  description?: string;
  [key: string]: unknown;
}

export interface SDElementsSurveyAnswer {
  id: string;
  text: string;
  question: string | number;
  selected?: boolean;
  valid?: boolean;
  display_text?: string;
  section?: string;
  [key: string]: unknown;
}

export interface SDElementsSurveyDraft {
  answers: SDElementsSurveyAnswer[];
  [key: string]: unknown;
}

// --- Utility Functions ---

/**
 * Calculates Sørensen–Dice coefficient (0.0 to 1.0)
 * Standalone pure function to keep the class clean.
 */
function calculateSimilarity(str1: string, str2: string): number {
  const s1 = str1.toLowerCase().replace(/\s+/g, "");
  const s2 = str2.toLowerCase().replace(/\s+/g, "");

  if (s1 === s2) return 1.0;
  if (s1.length < 2 || s2.length < 2) return 0.0;

  const bigrams1 = new Map<string, number>();
  for (let i = 0; i < s1.length - 1; i++) {
    const bigram = s1.substring(i, i + 2);
    bigrams1.set(bigram, (bigrams1.get(bigram) || 0) + 1);
  }

  let intersection = 0;
  for (let i = 0; i < s2.length - 1; i++) {
    const bigram = s2.substring(i, i + 2);
    const count = bigrams1.get(bigram);
    if (count && count > 0) {
      intersection++;
      bigrams1.set(bigram, count - 1);
    }
  }

  return (2.0 * intersection) / (s1.length - 1 + s2.length - 1);
}

// --- Main Client ---

export class SDElementsClient {
  private readonly host: string;
  private readonly baseUrl: string;
  private readonly apiKey: string;
  private readonly defaultTimeout: number;

  // Cache state
  private jwtToken: string | null = null;
  private jwtExpiresAt: number | null = null;
  private libraryAnswersCache: SDElementsSurveyAnswer[] | null = null;

  constructor(config: SDElementsConfig) {
    // Normalize host by removing trailing slash
    const host = config.host.replace(/\/$/, "");
    this.host = host;
    this.baseUrl = `${host}/api/v2`;
    this.apiKey = config.apiKey;
    this.defaultTimeout = config.timeout ?? 30000;
  }

  /**
   * Return the SD Elements host (without /api/v2).
   * Matches upstream Python api_client.host.
   */
  getHost(): string {
    return this.host;
  }

  /**
   * Core Fetch Wrapper
   */
  private async request<T = unknown>(
    method: HttpMethod,
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const cleanEndpoint = endpoint.replace(/^\//, "");
    const url = new URL(`${this.baseUrl}/${cleanEndpoint}`);

    // Append Query Params
    if (options.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.defaultTimeout);

    const fetchConfig: RequestInit = {
      method,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Token ${this.apiKey}`,
        Accept: "application/json",
        ...options.headers,
      },
      signal: controller.signal,
    };

    if (options.data && method !== "GET") {
      fetchConfig.body = JSON.stringify(options.data);
    }

    try {
      const response = await fetch(url.toString(), fetchConfig);
      clearTimeout(timeoutId);

      // Handle 204 No Content immediately
      if (response.status === 204) {
        return {} as T;
      }

      // Attempt to parse JSON regardless of status
      let responseBody: unknown;
      const textBody = await response.text();
      try {
        responseBody = textBody ? JSON.parse(textBody) : {};
      } catch {
        responseBody = { raw: textBody };
      }

      if (!response.ok) {
        const getStringField = (
          obj: unknown,
          key: string
        ): string | undefined => {
          if (!obj || typeof obj !== "object") return undefined;
          const value = (obj as Record<string, unknown>)[key];
          return typeof value === "string" ? value : undefined;
        };

        // Formatting standard JavaScript Error
        const status = response.status;
        const msg =
          getStringField(responseBody, "detail") ||
          getStringField(responseBody, "error") ||
          getStringField(responseBody, "message") ||
          textBody ||
          "Unknown Error";

        let errorPrefix = `[SDElements] HTTP ${status}`;
        if (status === 401) errorPrefix += " (Unauthorized)";
        if (status === 403) errorPrefix += " (Forbidden)";
        if (status === 404) errorPrefix += " (Not Found)";

        throw new Error(`${errorPrefix}: ${JSON.stringify(msg)}`);
      }

      return responseBody as T;
    } catch (error: unknown) {
      clearTimeout(timeoutId);
      if (error instanceof Error) {
        if (error.name === "AbortError")
          throw new Error(
            `[SDElements] Request timed out after ${this.defaultTimeout}ms`
          );
        throw error; // Rethrow standard errors
      }
      throw new Error(`[SDElements] Unexpected error: ${String(error)}`);
    }
  }

  // --- HTTP Helpers ---

  /**
   * Helper to build SD Elements query parameters
   * Supports include, exclude, expand, and custom filtering
   */
  private buildQueryParams(
    params?: SDElementsQueryParams
  ): Record<string, string | number | boolean | undefined> {
    if (!params) return {};

    const query: Record<string, string | number | boolean | undefined> = {};

    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        query[key] = value;
      }
    }

    return query;
  }

  get<T>(
    path: string,
    params?: SDElementsQueryParams | RequestOptions["params"]
  ) {
    const queryParams = params
      ? this.buildQueryParams(params as SDElementsQueryParams)
      : undefined;
    return this.request<T>("GET", path, { params: queryParams });
  }

  private post<T>(path: string, data?: unknown) {
    return this.request<T>("POST", path, { data });
  }

  private patch<T>(path: string, data?: unknown) {
    return this.request<T>("PATCH", path, { data });
  }

  private delete<T>(path: string) {
    return this.request<T>("DELETE", path);
  }

  // --- Projects ---
  // Reference: https://docs.sdelements.com/master/api/#projects

  async listProjects(
    params?: SDElementsQueryParams
  ): Promise<SDElementsPaginatedResponse<SDElementsProject>> {
    return this.get<SDElementsPaginatedResponse<SDElementsProject>>(
      "projects/",
      params
    );
  }

  async getProject(
    id: number,
    params?: SDElementsQueryParams
  ): Promise<SDElementsProject> {
    return this.get<SDElementsProject>(`projects/${id}/`, params);
  }

  async createProject(
    data: Partial<SDElementsProject>
  ): Promise<SDElementsProject> {
    return this.post<SDElementsProject>("projects/", data);
  }

  async updateProject(
    id: number,
    data: Partial<SDElementsProject>
  ): Promise<SDElementsProject> {
    return this.patch<SDElementsProject>(`projects/${id}/`, data);
  }

  async deleteProject(id: number): Promise<void> {
    return this.delete<void>(`projects/${id}/`);
  }

  // --- Survey Workflow ---
  // Reference: https://docs.sdelements.com/master/api/#project-survey

  async getProjectSurvey(
    projectId: number,
    params?: SDElementsQueryParams
  ): Promise<unknown> {
    return this.get(`projects/${projectId}/survey/`, params);
  }

  async getProjectSurveyDraft(
    projectId: number
  ): Promise<SDElementsSurveyDraft> {
    return this.get<SDElementsSurveyDraft>(
      `projects/${projectId}/survey/draft/`
    );
  }

  async commitSurveyDraft(projectId: number): Promise<unknown> {
    return this.post(`projects/${projectId}/survey/draft/`);
  }

  /**
   * Add a comment to a survey question.
   * Endpoint: projects/{project_id}/survey/comments/
   * Payload: { question: "<QID>", text: "<comment>" }
   */
  async addSurveyQuestionComment(
    projectId: number,
    questionId: string,
    comment: string
  ): Promise<{
    success: boolean;
    project_id: number;
    question_id: string;
    comment?: string;
    comment_id?: unknown;
    author?: string;
    created?: unknown;
    result?: unknown;
    error?: string;
    suggestion?: string;
  }> {
    try {
      const result = await this.post<Record<string, unknown>>(
        `projects/${projectId}/survey/comments/`,
        { question: questionId, text: comment }
      );

      const authorObj = (result as { author?: { email?: string } }).author;

      return {
        success: true,
        project_id: projectId,
        question_id: questionId,
        comment,
        comment_id: (result as { id?: unknown }).id,
        author: authorObj?.email ?? "Unknown",
        created: (result as { created?: unknown }).created,
        result,
      };
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      return {
        success: false,
        project_id: projectId,
        question_id: questionId,
        error: `Failed to add comment: ${msg}`,
        suggestion:
          "Verify the question ID exists in the survey. You can find question IDs by calling get_project_survey.",
      };
    }
  }

  /**
   * Complex logic to update survey answers via the Draft API.
   * Handles prerequisites by selecting answers sequentially.
   */
  async updateProjectSurvey(
    projectId: number,
    payload: SurveyUpdatePayload
  ): Promise<SurveyUpdateResult> {
    // 1. Get Draft
    let draft = await this.get<SDElementsSurveyDraft>(
      `projects/${projectId}/survey/draft/`
    ).catch(() => ({ answers: [] }));

    const targetIds = new Set(payload.answers);
    const deselectIds = new Set(payload.answers_to_deselect ?? []);
    const errors: string[] = [];

    let selectedCount = 0;
    let deselectedCount = 0;

    // 2. Deselect explicitly
    for (const id of deselectIds) {
      const exists = draft.answers.find((a) => a.id === id && a.selected);
      if (exists) {
        try {
          await this.patch(`projects/${projectId}/survey/draft/${id}/`, {
            selected: "false",
          });
          deselectedCount++;
        } catch (e: unknown) {
          const errorMsg = e instanceof Error ? e.message : String(e);
          errors.push(`Failed to deselect ${id}: ${errorMsg}`);
        }
      }
    }

    // 3. Select sequentially (refreshing draft to catch auto-enabled prerequisites)
    for (const id of targetIds) {
      // Refresh draft state to ensure validity checks are current
      try {
        draft = await this.get<SDElementsSurveyDraft>(
          `projects/${projectId}/survey/draft/`
        );
      } catch (e: unknown) {
        const errorMsg = e instanceof Error ? e.message : String(e);
        errors.push(`Draft refresh failed: ${errorMsg}`);
        continue;
      }

      const answer = draft.answers.find((a) => a.id === id);

      if (answer && !answer.selected) {
        try {
          await this.patch(`projects/${projectId}/survey/draft/${id}/`, {
            selected: "true",
          });
          selectedCount++;
        } catch (e: unknown) {
          const errorMsg = e instanceof Error ? e.message : String(e);
          errors.push(`Failed to select ${id}: ${errorMsg}`);
        }
      }
    }

    // 4. Verify results
    const finalDraft = await this.get<SDElementsSurveyDraft>(
      `projects/${projectId}/survey/draft/`
    );
    const finalSelectedIds = new Set(
      finalDraft.answers.filter((a) => a.selected).map((a) => a.id)
    );
    const missingAnswers = [...targetIds].filter(
      (id) => !finalSelectedIds.has(id)
    );

    const result: SurveyUpdateResult = {
      success: true,
      selectedCount,
      deselectedCount,
      targetAnswers: Array.from(targetIds),
      deselectedAnswers: deselectIds.size ? Array.from(deselectIds) : null,
      missingAnswers: missingAnswers.length ? missingAnswers : null,
      errors: errors.length ? errors : null,
      draftCommitted: false,
    };

    // 5. Commit if requested
    if (payload.survey_complete) {
      try {
        result.commitResult = await this.post(
          `projects/${projectId}/survey/draft/`
        );
        result.draftCommitted = true;
      } catch (e: unknown) {
        const errorMsg = e instanceof Error ? e.message : String(e);
        result.commitError = errorMsg;
      }
    } else {
      result.note = "Draft updated. Call commit to finalize.";
    }

    return result;
  }

  /**
   * Resolves dependencies automatically by searching for required prerequisites.
   */
  async addAnswerToSurveyDraft(
    projectId: number,
    answerId: string,
    autoResolve = true
  ): Promise<{
    success: boolean;
    dependenciesAdded?: string[];
    message?: string;
  }> {
    let draft = await this.get<SDElementsSurveyDraft>(
      `projects/${projectId}/survey/draft/`
    );
    let target = draft.answers.find((a) => a.id === answerId);

    if (!target) throw new Error(`Answer ${answerId} not found in survey`);
    if (target.selected) return { success: true, message: "Already selected" };

    // Handle invalid answers (likely missing prerequisites)
    if (!target.valid) {
      if (!autoResolve) throw new Error("Answer invalid (unmet dependencies)");

      const questionId = target.question;
      const dependenciesAdded: string[] = [];

      // Find potential prerequisites within the same question group
      const potentialPrereqs = draft.answers.filter(
        (a) => a.valid && !a.selected && a.question === questionId
      );

      for (const prereq of potentialPrereqs) {
        try {
          // Try selecting prereq
          await this.patch(`projects/${projectId}/survey/draft/${prereq.id}/`, {
            selected: "true",
          });
          dependenciesAdded.push(prereq.id);

          // Re-check target validity
          draft = await this.get<SDElementsSurveyDraft>(
            `projects/${projectId}/survey/draft/`
          );
          target = draft.answers.find((a) => a.id === answerId);

          if (target && target.valid) {
            await this.patch(
              `projects/${projectId}/survey/draft/${answerId}/`,
              { selected: "true" }
            );
            return {
              success: true,
              dependenciesAdded,
              message: "Resolved dependencies",
            };
          }
        } catch {
          // Continue to next potential prereq if this one failed
          continue;
        }
      }
      throw new Error("Could not automatically resolve dependencies");
    }

    // Direct selection
    await this.patch(`projects/${projectId}/survey/draft/${answerId}/`, {
      selected: "true",
    });
    return { success: true };
  }

  // --- Library & Search ---
  // Reference: https://docs.sdelements.com/master/api/#library-answers

  async loadLibraryAnswers(): Promise<void> {
    try {
      const res = await this.get<
        SDElementsPaginatedResponse<SDElementsSurveyAnswer>
      >("library/answers/", {
        page_size: 10000,
      });
      this.libraryAnswersCache = res.results || [];
    } catch {
      this.libraryAnswersCache = [];
    }
  }

  async findAnswersByText(
    searchTexts: string[],
    fuzzyThreshold = 0.75
  ): Promise<Record<string, AnswerMatch | null>> {
    if (!this.libraryAnswersCache) await this.loadLibraryAnswers();
    const cache = this.libraryAnswersCache || [];

    const results: Record<string, AnswerMatch | null> = {};
    const searchMap = new Map(searchTexts.map((t) => [t.toLowerCase(), t]));

    // 1. Exact & Substring Match
    for (const item of cache) {
      const itemText = (item.text || "").toLowerCase();

      for (const [searchLower, originalKey] of searchMap) {
        if (results[originalKey]) continue; // Already found

        if (itemText === searchLower) {
          results[originalKey] = {
            id: item.id,
            text: item.text,
            question: item.display_text || "",
            matchType: "exact",
            similarity: 1.0,
          };
        } else if (itemText.includes(searchLower)) {
          results[originalKey] = {
            id: item.id,
            text: item.text,
            question: item.display_text || "",
            matchType: "substring",
            similarity: calculateSimilarity(searchLower, itemText),
          };
        }
      }
    }

    // 2. Fuzzy Match (for remaining)
    for (const key of searchTexts) {
      if (results[key]) continue;

      let bestMatch: AnswerMatch | null = null;
      let maxScore = 0;
      const keyLower = key.toLowerCase();

      for (const item of cache) {
        const score = calculateSimilarity(
          keyLower,
          (item.text || "").toLowerCase()
        );
        if (score > maxScore && score >= fuzzyThreshold) {
          maxScore = score;
          bestMatch = {
            id: item.id,
            text: item.text,
            question: item.display_text || "",
            matchType: "fuzzy",
            similarity: score,
          };
        }
      }
      results[key] = bestMatch;
    }

    return results;
  }

  // --- Tasks (Countermeasures) ---
  // Reference: https://docs.sdelements.com/master/api/#countermeasures

  async listTasks(
    projectId: number,
    params?: SDElementsQueryParams
  ): Promise<SDElementsPaginatedResponse<SDElementsTask>> {
    return this.get<SDElementsPaginatedResponse<SDElementsTask>>(
      `projects/${projectId}/tasks/`,
      params
    );
  }

  async getTask(
    projectId: number,
    taskId: string,
    params?: SDElementsQueryParams
  ): Promise<SDElementsTask> {
    // Ensure ID format "123-T456"
    const fullId = taskId.startsWith(`${projectId}`)
      ? taskId
      : `${projectId}-${taskId}`;
    return this.get<SDElementsTask>(
      `projects/${projectId}/tasks/${fullId}/`,
      params
    );
  }

  async updateTask(
    projectId: number,
    taskId: string,
    data: Partial<SDElementsTask> & { status_note?: string }
  ): Promise<SDElementsTask> {
    const fullId = taskId.startsWith(`${projectId}`)
      ? taskId
      : `${projectId}-${taskId}`;
    return this.patch<SDElementsTask>(
      `projects/${projectId}/tasks/${fullId}/`,
      data
    );
  }

  async addTaskNote(
    projectId: number,
    taskId: string,
    note: string
  ): Promise<unknown> {
    const fullId = taskId.startsWith(`${projectId}`)
      ? taskId
      : `${projectId}-${taskId}`;
    return this.post(`projects/${projectId}/tasks/${fullId}/notes/`, {
      text: note,
    });
  }

  async listTaskStatuses(
    params?: SDElementsQueryParams
  ): Promise<SDElementsPaginatedResponse<SDElementsTaskStatus>> {
    return this.get<SDElementsPaginatedResponse<SDElementsTaskStatus>>(
      "task-statuses/",
      params
    );
  }

  // --- Cube (Advanced Reports) ---

  private async getCubeJwt(): Promise<string> {
    if (this.jwtToken && this.jwtExpiresAt && Date.now() < this.jwtExpiresAt) {
      return this.jwtToken;
    }

    const res = await this.get<{ token: string }>("users/me/auth-token/");
    if (!res.token) throw new Error("[SDElements] Failed to retrieve Cube JWT");

    this.jwtToken = res.token;
    this.jwtExpiresAt = Date.now() + 50000; // 50 seconds buffer
    return this.jwtToken;
  }

  async executeCubeQuery(query: CubeQuery) {
    const token = await this.getCubeJwt();

    // CubeJS uses a GET request with a 'query' param containing JSON
    const url = new URL(
      `${this.baseUrl.replace("/api/v2", "")}/cubejs-api/v1/load`
    );
    url.searchParams.append("query", JSON.stringify(query));

    const res = await fetch(url.toString(), {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!res.ok) {
      throw new Error(
        `[SDElements] Cube Query Failed: ${res.status} ${await res.text()}`
      );
    }
    return res.json();
  }

  // --- Applications ---
  // Reference: https://docs.sdelements.com/master/api/#applications

  async listApplications(
    params?: SDElementsQueryParams
  ): Promise<SDElementsPaginatedResponse<SDElementsApplication>> {
    return this.get<SDElementsPaginatedResponse<SDElementsApplication>>(
      "applications/",
      params
    );
  }

  async getApplication(
    id: number,
    params?: SDElementsQueryParams
  ): Promise<SDElementsApplication> {
    return this.get<SDElementsApplication>(`applications/${id}/`, params);
  }

  async createApplication(
    data: Partial<SDElementsApplication>
  ): Promise<SDElementsApplication> {
    return this.post<SDElementsApplication>("applications/", data);
  }

  async updateApplication(
    id: number,
    data: Partial<SDElementsApplication>
  ): Promise<SDElementsApplication> {
    return this.patch<SDElementsApplication>(`applications/${id}/`, data);
  }

  async deleteApplication(id: number): Promise<void> {
    return this.delete<void>(`applications/${id}/`);
  }

  // --- Business Units ---
  // Reference: https://docs.sdelements.com/master/api/#business-units

  async listBusinessUnits(
    params?: SDElementsQueryParams
  ): Promise<SDElementsPaginatedResponse<SDElementsBusinessUnit>> {
    return this.get<SDElementsPaginatedResponse<SDElementsBusinessUnit>>(
      "business-units/",
      params
    );
  }

  async getBusinessUnit(
    id: number,
    params?: SDElementsQueryParams
  ): Promise<SDElementsBusinessUnit> {
    return this.get<SDElementsBusinessUnit>(`business-units/${id}/`, params);
  }

  // --- Users ---
  // Reference: https://docs.sdelements.com/master/api/#users

  async listUsers(
    params?: SDElementsQueryParams
  ): Promise<SDElementsPaginatedResponse<SDElementsUser>> {
    return this.get<SDElementsPaginatedResponse<SDElementsUser>>(
      "users/",
      params
    );
  }

  async getUser(
    id: number,
    params?: SDElementsQueryParams
  ): Promise<SDElementsUser> {
    return this.get<SDElementsUser>(`users/${id}/`, params);
  }

  async getCurrentUser(
    params?: SDElementsQueryParams
  ): Promise<SDElementsUser> {
    return this.get<SDElementsUser>("users/me/", params);
  }

  // --- Profiles ---
  // Reference: https://docs.sdelements.com/master/api/#library-profiles

  async listProfiles(
    params?: SDElementsQueryParams
  ): Promise<SDElementsPaginatedResponse<SDElementsProfile>> {
    return this.get<SDElementsPaginatedResponse<SDElementsProfile>>(
      "profiles/",
      params
    );
  }

  async getProfile(
    id: string,
    params?: SDElementsQueryParams
  ): Promise<SDElementsProfile> {
    return this.get<SDElementsProfile>(`profiles/${id}/`, params);
  }

  // --- Risk Policies ---
  // Reference: https://docs.sdelements.com/master/api/#risk-policies

  async listRiskPolicies(
    params?: SDElementsQueryParams
  ): Promise<SDElementsPaginatedResponse<SDElementsRiskPolicy>> {
    return this.get<SDElementsPaginatedResponse<SDElementsRiskPolicy>>(
      "risk-policies/",
      params
    );
  }

  async getRiskPolicy(
    id: number,
    params?: SDElementsQueryParams
  ): Promise<SDElementsRiskPolicy> {
    return this.get<SDElementsRiskPolicy>(`risk-policies/${id}/`, params);
  }

  // --- Groups ---
  // Reference: api_client.py includes groups endpoints

  async listGroups(params?: SDElementsQueryParams): Promise<unknown> {
    return this.get("groups/", params);
  }

  async getGroup(id: number, params?: SDElementsQueryParams): Promise<unknown> {
    return this.get(`groups/${id}/`, params);
  }

  // --- Team Onboarding / Repository Scanning ---
  // Reference: api_client.py uses team-onboarding/connections/ and team-onboarding/scans/

  async listTeamOnboardingConnections(
    params?: SDElementsQueryParams
  ): Promise<unknown> {
    return this.get("team-onboarding/connections/", params);
  }

  async createTeamOnboardingConnection(data: Record<string, unknown>) {
    return this.post("team-onboarding/connections/", data);
  }

  async listTeamOnboardingScans(
    params?: SDElementsQueryParams
  ): Promise<unknown> {
    return this.get("team-onboarding/scans/", params);
  }

  async createTeamOnboardingScan(data: Record<string, unknown>) {
    return this.post("team-onboarding/scans/", data);
  }

  async getTeamOnboardingScan(id: number, params?: SDElementsQueryParams) {
    return this.get(`team-onboarding/scans/${id}/`, params);
  }

  // --- Project Diagrams ---
  // Reference: api_client.py uses project-diagrams/

  async listProjectDiagrams(projectId: number, params?: SDElementsQueryParams) {
    const merged: SDElementsQueryParams = { ...(params || {}), project: projectId };
    return this.get("project-diagrams/", merged);
  }

  async getProjectDiagram(diagramId: number, params?: SDElementsQueryParams) {
    return this.get(`project-diagrams/${diagramId}/`, params);
  }

  async createProjectDiagram(data: Record<string, unknown>) {
    return this.post("project-diagrams/", data);
  }

  async updateProjectDiagram(diagramId: number, data: Record<string, unknown>) {
    return this.patch(`project-diagrams/${diagramId}/`, data);
  }

  async deleteProjectDiagram(diagramId: number) {
    return this.delete(`project-diagrams/${diagramId}/`);
  }

  // --- Advanced Reports (Queries) ---
  // Reference: api_client.py uses queries/ and runs via Cube API

  async listAdvancedReports(params?: SDElementsQueryParams) {
    return this.get("queries/", params);
  }

  async getAdvancedReport(reportId: number, params?: SDElementsQueryParams) {
    return this.get(`queries/${reportId}/`, params);
  }

  async createAdvancedReport(data: Record<string, unknown>) {
    return this.post("queries/", data);
  }

  async updateAdvancedReport(reportId: number, data: Record<string, unknown>) {
    return this.patch(`queries/${reportId}/`, data);
  }

  async deleteAdvancedReport(reportId: number) {
    return this.delete(`queries/${reportId}/`);
  }

  /**
   * Run/execute an advanced report to get actual data results.
   * Mirrors python api_client.run_advanced_report.
   */
  async runAdvancedReport(reportId: number, params?: SDElementsQueryParams) {
    const queryDef = await this.getAdvancedReport(reportId, params);
    const cubeQuery = (queryDef as { query?: unknown }).query;
    if (cubeQuery && typeof cubeQuery === "object") {
      try {
        const data = await this.executeCubeQuery(cubeQuery as CubeQuery);
        return { query: queryDef, data };
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        return { query: queryDef, data: null, error: `Failed to execute cube query: ${msg}` };
      }
    }
    return queryDef;
  }

  // --- Cache Accessors ---

  getLibraryAnswersCache() {
    return this.libraryAnswersCache;
  }

  // --- Generic / Passthrough ---

  /**
   * Generic API request method
   * Use this for custom endpoints not covered by specific methods
   */
  async apiRequest<T = unknown>(
    method: HttpMethod,
    endpoint: string,
    data?: unknown,
    params?: SDElementsQueryParams
  ): Promise<T> {
    const queryParams = params ? this.buildQueryParams(params) : undefined;
    return this.request<T>(method, endpoint, { data, params: queryParams });
  }

  /**
   * Test the connection to SD Elements API
   */
  async testConnection(): Promise<boolean> {
    try {
      await this.get("users/me/");
      return true;
    } catch {
      return false;
    }
  }
}
