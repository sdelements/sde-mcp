export type PrimitiveParam = string | number | boolean;

/**
 * Build params object, filtering out null/undefined and non-primitive values.
 */
export function buildParams(
  params: Record<string, unknown>
): Record<string, PrimitiveParam> {
  const result: Record<string, PrimitiveParam> = {};
  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined) continue;
    if (
      typeof value === "string" ||
      typeof value === "number" ||
      typeof value === "boolean"
    ) {
      result[key] = value;
    }
  }
  return result;
}

/**
 * Standard MCP text response that pretty-prints JSON.
 */
export function jsonToolResult(obj: unknown) {
  return {
    content: [{ type: "text" as const, text: JSON.stringify(obj, null, 2) }],
  };
}
