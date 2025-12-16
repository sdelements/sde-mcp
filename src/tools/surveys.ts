/**
 * Survey-related tools
 * Translated from: https://github.com/sdelements/sde-mcp/blob/master/src/sde_mcp_server/tools/surveys.py
 */

import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { SDElementsClient } from "../utils/apiClient.js";
import { jsonToolResult } from "./_shared.js";

/**
 * Register all survey-related tools
 */
export function registerSurveyTools(
  server: McpServer,
  client: SDElementsClient
): void {
  // Get project survey
  server.registerTool(
    "get_project_survey",
    {
      title: "Get Project Survey",
      description:
        "Get the complete survey structure for a project (all available questions and ALL possible answers). Use this to see what survey questions exist and what answers are available. Use get_survey_answers_for_project to see only the answers that are currently selected for a project.",
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project"),
      }),
    },
    async ({ project_id }) => {
      const result = await client.getProjectSurvey(project_id);

      return jsonToolResult(result);
    }
  );

  // Update project survey
  server.registerTool(
    "update_project_survey",
    {
      title: "Update Project Survey",
      description:
        "Update project survey with answer IDs. Selects answers in 'answers' list and optionally deselects answers in 'answers_to_deselect' list.",
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project"),
        answers: z.array(z.string()).describe("List of answer IDs to select"),
        answers_to_deselect: z
          .array(z.string())
          .optional()
          .describe("List of answer IDs to deselect"),
        survey_complete: z
          .boolean()
          .optional()
          .describe("Mark survey as complete"),
      }),
    },
    async ({ project_id, answers, answers_to_deselect, survey_complete }) => {
      const data = {
        answers,
        answers_to_deselect,
        survey_complete,
      };

      const result = await client.updateProjectSurvey(project_id, data);

      return jsonToolResult(result);
    }
  );

  // Find survey answers
  server.registerTool(
    "find_survey_answers",
    {
      title: "Find Survey Answers",
      description: "Find survey answers by text",
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project"),
        search_texts: z
          .array(z.string())
          .describe("List of answer texts to search for"),
      }),
    },
    async ({ project_id, search_texts }) => {
      // Tool signature includes project_id for consistency with other survey tools,
      // but this operation searches the shared answer library (not project-scoped).
      void project_id;
      const result = await client.findAnswersByText(search_texts);

      return jsonToolResult(result);
    }
  );

  // Set project survey by text
  server.registerTool(
    "set_project_survey_by_text",
    {
      title: "Set Project Survey By Text",
      description:
        "Set/REPLACE all project survey answers by text. This REPLACES all existing answers with the new ones. Use ONLY when user wants to completely replace all answers. Use add_survey_answers_by_text if user says 'add' or wants to keep existing answers.\n\nIf replace_all is True (default), deselects all current answers not in the new list. If False, only selects the new answers without deselecting existing ones.",
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project"),
        answer_texts: z
          .array(z.string())
          .describe("List of answer texts to set"),
        replace_all: z
          .boolean()
          .optional()
          .default(true)
          .describe("Replace all existing answers"),
        survey_complete: z
          .boolean()
          .optional()
          .describe("Mark survey as complete"),
      }),
    },
    async ({
      project_id,
      answer_texts,
      replace_all = true,
      survey_complete,
    }) => {
      const searchResults = await client.findAnswersByText(answer_texts);
      const answerIds: string[] = [];
      const notFound: string[] = [];

      for (const [text, info] of Object.entries(searchResults)) {
        if (info?.id) {
          answerIds.push(info.id);
        } else {
          notFound.push(text);
        }
      }

      if (notFound.length > 0) {
        const result = {
          error: `Could not find answers for: ${notFound.join(", ")}`,
          search_results: searchResults,
        };

        return jsonToolResult(result);
      }

      let answersToDeselect: string[] | undefined;

      // If replace_all is true, get current answers and deselect those not in the new list
      if (replace_all) {
        const currentSurvey = await client.getProjectSurvey(project_id);
        const surveyData = currentSurvey as { answers?: string[] };
        const currentAnswerIds = new Set(surveyData.answers || []);
        const newAnswerIds = new Set(answerIds);
        const toDeselect = [...currentAnswerIds].filter(
          (id) => !newAnswerIds.has(id)
        );

        if (toDeselect.length > 0) {
          answersToDeselect = toDeselect;
        }
      }

      const data = {
        answers: answerIds,
        answers_to_deselect: answersToDeselect,
        survey_complete,
      };

      const updateResult = await client.updateProjectSurvey(project_id, data);
      const result = {
        success: true,
        matched_answers: searchResults,
        answer_ids_used: answerIds,
        replace_all,
        update_result: updateResult,
      };

      return jsonToolResult(result);
    }
  );

  // Remove survey answers by text
  server.registerTool(
    "remove_survey_answers_by_text",
    {
      title: "Remove Survey Answers By Text",
      description:
        "Remove survey answers by text. This explicitly deselects the specified answers while keeping all other answers unchanged.",
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project"),
        answer_texts_to_remove: z
          .array(z.string())
          .describe("List of answer texts to remove"),
      }),
    },
    async ({ project_id, answer_texts_to_remove }) => {
      // Get current answers to preserve them
      const currentSurvey = await client.getProjectSurvey(project_id);
      const surveyData = currentSurvey as { answers?: string[] };
      const currentAnswerIds = surveyData.answers || [];

      // Find answer IDs for the texts to remove
      const searchResults = await client.findAnswersByText(
        answer_texts_to_remove
      );

      const idsToDeselect: string[] = [];
      const notFound: string[] = [];

      for (const [text, info] of Object.entries(searchResults)) {
        if (info?.id) {
          idsToDeselect.push(info.id);
        } else {
          notFound.push(text);
        }
      }

      // Use explicit deselection - keep all current answers, just deselect the specified ones
      const data = {
        answers: currentAnswerIds, // Keep all current answers
        answers_to_deselect: idsToDeselect, // Explicitly deselect these
      };

      const updateResult = await client.updateProjectSurvey(project_id, data);

      const removedAnswers: Record<string, unknown> = {};
      for (const [text, info] of Object.entries(searchResults)) {
        if (info?.id) {
          removedAnswers[text] = info;
        }
      }

      const result = {
        success: true,
        removed_answers: removedAnswers,
        ids_deselected: idsToDeselect,
        not_found: notFound,
        remaining_answer_count: currentAnswerIds.length - idsToDeselect.length,
        update_result: updateResult,
      };

      return jsonToolResult(result);
    }
  );

  // Add survey answers by text
  server.registerTool(
    "add_survey_answers_by_text",
    {
      title: "Add Survey Answers By Text",
      description:
        "ADD survey answers by text to existing answers. Use when user says 'add', 'include', or wants to add to existing answers. This ADDS new answers while preserving all existing ones. Use set_project_survey_by_text ONLY if user explicitly wants to REPLACE all answers.",
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project"),
        answer_texts_to_add: z
          .array(z.string())
          .describe("List of answer texts to add"),
      }),
    },
    async ({ project_id, answer_texts_to_add }) => {
      // Load library answers if not already loaded
      await client.loadLibraryAnswers();

      // Find answers by text
      const searchResults = await client.findAnswersByText(
        answer_texts_to_add,
        0.75
      );

      const answerIds: string[] = [];
      const notFound: string[] = [];

      for (const [text, info] of Object.entries(searchResults)) {
        if (info?.id) {
          answerIds.push(info.id);
        } else {
          notFound.push(text);
        }
      }

      // Add each answer to the survey draft with auto-resolve dependencies
      const addedAnswers: string[] = [];
      const failedAnswers: Array<{ text: string; error: string }> = [];

      for (const answerId of answerIds) {
        try {
          await client.addAnswerToSurveyDraft(project_id, answerId, true);
          addedAnswers.push(answerId);
        } catch (error) {
          const errorMsg =
            error instanceof Error ? error.message : String(error);
          failedAnswers.push({
            text: answer_texts_to_add[answerIds.indexOf(answerId)],
            error: errorMsg,
          });
        }
      }

      const result = {
        success: addedAnswers.length > 0,
        added_count: addedAnswers.length,
        added_answers: addedAnswers,
        failed_answers: failedAnswers.length > 0 ? failedAnswers : undefined,
        not_found: notFound.length > 0 ? notFound : undefined,
        search_results: searchResults,
      };

      return jsonToolResult(result);
    }
  );

  // Get survey answers for project
  server.registerTool(
    "get_survey_answers_for_project",
    {
      title: "Get Survey Answers For Project",
      description:
        "Get the survey answers FOR A PROJECT that are currently selected/assigned. Use when user asks 'show me the survey answers for project X', 'what answers are set for project', 'survey answers for project', or 'current answers for project'. Returns only the answers that are currently selected for the project, not all available answers. Use get_project_survey to see the full survey structure with all available questions and answers.",
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project"),
        format: z
          .enum(["summary", "detailed", "grouped"])
          .optional()
          .default("summary")
          .describe("Output format"),
      }),
    },
    async ({ project_id, format = "summary" }) => {
      const survey = await client.getProjectSurvey(project_id);
      const surveyData = survey as {
        answers?: string[];
        sections?: Array<{
          title?: string;
          questions?: Array<{
            id?: string;
            text?: string;
            answers?: Array<{
              id?: string;
              text?: string;
            }>;
          }>;
        }>;
      };

      const currentAnswerIds = surveyData.answers || [];

      if (currentAnswerIds.length === 0) {
        const result = {
          project_id,
          message: "No answers are currently assigned to this survey",
          answer_count: 0,
        };

        return jsonToolResult(result);
      }

      const answerDetails: Record<
        string,
        {
          text: string;
          question: string;
          section: string;
          question_id?: string;
        }
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

      let result: unknown;

      if (format === "summary") {
        result = {
          project_id,
          answer_count: currentAnswerIds.length,
          answers: Object.values(answerDetails).map((d) => d.text),
          answer_ids: currentAnswerIds,
        };
      } else if (format === "detailed") {
        result = {
          project_id,
          answer_count: currentAnswerIds.length,
          answers: Object.entries(answerDetails).map(([aid, details]) => ({
            text: details.text,
            question: details.question,
            answer_id: aid,
          })),
        };
      } else if (format === "grouped") {
        const grouped: Record<
          string,
          Array<{ question: string; answer: string }>
        > = {};
        for (const details of Object.values(answerDetails)) {
          const section = details.section;
          if (!grouped[section]) {
            grouped[section] = [];
          }
          grouped[section].push({
            question: details.question,
            answer: details.text,
          });
        }
        result = {
          project_id,
          answer_count: currentAnswerIds.length,
          sections: grouped,
        };
      } else {
        result = { error: `Unknown format: ${format}` };
      }

      return {
        content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
      };
    }
  );

  // Commit survey draft
  server.registerTool(
    "commit_survey_draft",
    {
      title: "Commit Survey Draft",
      description:
        "Commit the survey draft to publish the survey and generate countermeasures",
      inputSchema: z.object({
        project_id: z.number().describe("ID of the project"),
      }),
    },
    async ({ project_id }) => {
      const result = await client.commitSurveyDraft(project_id);

      return jsonToolResult(result);
    }
  );

  // Add survey question comment
  server.registerTool(
    "add_survey_question_comment",
    {
      title: "Add Survey Question Comment",
      description:
        "Add a comment to a survey question. Use this to explain why specific answers were selected for a question, providing context and justification for survey answer choices.\n\nThis is especially useful when setting project survey answers to document the reasoning behind answer selections.\n\nExample: Add a comment to question Q1 in project 123 explaining that Python was selected because the project uses Django.",
      inputSchema: z.object({
        project_id: z.number().describe("The project ID"),
        question_id: z
          .string()
          .describe(
            'The question ID (e.g., "Q1", "CQ1", "Q123"). Find question IDs by calling get_project_survey.'
          ),
        comment: z
          .string()
          .describe(
            "The comment text explaining why answers were selected for this question"
          ),
      }),
    },
    async ({ project_id, question_id, comment }) => {
      const result = await client.addSurveyQuestionComment(
        project_id,
        question_id,
        comment
      );

      return jsonToolResult(result);
    }
  );
}
