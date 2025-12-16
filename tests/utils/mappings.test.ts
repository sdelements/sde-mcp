import { describe, expect, it } from "vitest";
import { extractAnswerTextsFromContext } from "../../src/utils/mappings.js";

describe("extractAnswerTextsFromContext", () => {
  it("returns [] for empty context", () => {
    expect(extractAnswerTextsFromContext("", [{ text: "TypeScript" }])).toEqual(
      []
    );
  });

  it("matches technology keywords against available answers (case-insensitive) and de-dupes", () => {
    const ctx = `
      We are building a RESTful API in TypeScript on Node.js with Express.
      This is definitely a web app, not a desktop app.
    `;

    const available = [
      { text: "REST API" },
      { text: "TypeScript" },
      { text: "Node.js" },
      { text: "Express" },
      { text: "Web Application" },
    ];

    const matched = extractAnswerTextsFromContext(ctx, available);

    // Order matters (keyword list order + then fuzzy scan), so assert as exact array.
    expect(matched).toEqual([
      "REST API",
      "Web Application",
      "TypeScript",
      "Node.js",
      "Express",
    ]);
  });

  it("does whole-word matching for short keywords (e.g., 'go' shouldn't match 'mongodb')", () => {
    const ctx = `We use MongoDB heavily.`;

    const available = [{ text: "Go" }, { text: "MongoDB" }];
    const matched = extractAnswerTextsFromContext(ctx, available);

    // "MongoDB" should match; "Go" should NOT match via 'go' inside 'mongodb'
    expect(matched).toContain("MongoDB");
    expect(matched).not.toContain("Go");
  });

  it("matches direct mentions of available answers as whole words (longer answers first)", () => {
    const ctx = `This service emits JSON, reads YAML, and uses Google Cloud Platform.`;

    const available = [
      { text: "JSON" },
      { text: "YAML" },
      { text: "Google Cloud Platform" },
    ];

    const matched = extractAnswerTextsFromContext(ctx, available);
    expect(matched).toEqual(["Google Cloud Platform", "JSON", "YAML"]);
  });
});


