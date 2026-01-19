import * as Sentry from "@sentry/node";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { registerAll } from "./tools/index";

const PACKAGE_VERSION: string = (() => {
  try {
    const __filename = fileURLToPath(import.meta.url);
    const __dirname = path.dirname(__filename);
    const pkgPath = path.resolve(__dirname, "..", "package.json");
    const raw = readFileSync(pkgPath, "utf8");
    const parsed = JSON.parse(raw) as { version?: unknown };
    return typeof parsed.version === "string" ? parsed.version : "0.0.0";
  } catch {
    return "0.0.0";
  }
})();

let sentryInitialized = false;

function wrapServerWithSentry(server: McpServer): McpServer {
  const dsn = process.env.MCP_SENTRY_DSN?.trim();
  if (!dsn) return server;

  if (!sentryInitialized) {
    Sentry.init({
      dsn,
      tracesSampleRate: 1.0,
    });
    sentryInitialized = true;
  }

  return Sentry.wrapMcpServerWithSentry(server, {
    recordInputs: false,
    recordOutputs: false,
  });
}

export function createServer(
  creds?: import("./tools/index").SdeCredentials
): McpServer {
  const baseServer = new McpServer({
    name: "sde-mcp",
    version: PACKAGE_VERSION,
  });
  const server = wrapServerWithSentry(baseServer);

  registerAll(server, creds);

  return server;
}

export function setupSignalHandlers(cleanup: () => Promise<void>): void {
  process.on("SIGINT", async () => {
    await cleanup();
    process.exit(0);
  });

  process.on("SIGTERM", async () => {
    await cleanup();
    process.exit(0);
  });
}
