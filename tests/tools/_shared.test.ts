import { describe, expect, it } from "vitest";
import { buildParams, jsonToolResult } from "../../src/tools/_shared.js";

describe("tools/_shared", () => {
  describe("buildParams", () => {
    it("filters out null/undefined and keeps only primitive values", () => {
      const params = buildParams({
        a: "x",
        b: 1,
        c: true,
        d: null,
        e: undefined,
        f: { nested: "no" },
        g: [1, 2, 3],
        h: () => "no",
      });

      expect(params).toEqual({ a: "x", b: 1, c: true });
    });

    it("keeps empty string/0/false (valid primitives)", () => {
      const params = buildParams({
        empty: "",
        zero: 0,
        nope: false,
      });

      expect(params).toEqual({ empty: "", zero: 0, nope: false });
    });
  });

  describe("jsonToolResult", () => {
    it("wraps the object as MCP text content with pretty JSON", () => {
      const result = jsonToolResult({ ok: true, nested: { a: 1 } });
      expect(result.content).toHaveLength(1);
      expect(result.content[0].type).toBe("text");

      const text = result.content[0].text;
      expect(JSON.parse(text)).toEqual({ ok: true, nested: { a: 1 } });
      // Pretty-print includes newlines/indentation for nested objects
      expect(text).toContain("\n");
      expect(text).toContain('  "nested"');
    });
  });
});




