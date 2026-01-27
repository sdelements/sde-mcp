import { randomUUID } from "node:crypto";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { isInitializeRequest } from "@modelcontextprotocol/sdk/types.js";
import type { IncomingMessage, ServerResponse } from "node:http";
import { createServer, setupSignalHandlers } from "./mcp";
import { checkNodeVersion } from "./utils/version";

type SessionEntry = {
  transport: StreamableHTTPServerTransport;
  server: ReturnType<typeof createServer>;
};

type SdeCreds = {
  host: string;
  apiKey: string;
};

function normalizeSdeHost(
  value: string,
  options?: { allowInsecure?: boolean }
): string | null {
  const trimmed = value.trim();
  if (!trimmed) return null;

  let parsed: URL;
  try {
    parsed = new URL(trimmed);
  } catch {
    return null;
  }

  const allowInsecure =
    options?.allowInsecure ?? process.env.SDE_ALLOW_INSECURE_HTTP === "true";
  if (
    parsed.protocol !== "https:" &&
    !(allowInsecure && parsed.protocol === "http:")
  ) {
    return null;
  }
  if (parsed.username || parsed.password) return null;
  if (parsed.search || parsed.hash) return null;
  if (parsed.pathname && parsed.pathname !== "/") return null;

  return parsed.origin;
}

function redactSdeCredsFromInitBody(body: unknown): unknown {
  if (!body || typeof body !== "object") return body;

  // Avoid accidentally forwarding credentials to the MCP layer (and any logs/telemetry
  // it may have). We still *read* creds from body for compatibility, but we redact
  // them before handing the init payload to the transport.
  const clone = structuredClone(body) as Record<string, unknown>;

  delete clone.sde_host;
  delete clone.sde_api_key;

  const params = clone.params;
  if (params && typeof params === "object") {
    const paramsObj = params as Record<string, unknown>;
    delete paramsObj.sde_host;
    delete paramsObj.sde_api_key;
  }

  return clone;
}

// Expose internals for unit tests (not part of public API).
export const __test__ = {
  redactSdeCredsFromInitBody,
  readSdeCredsFromRequest,
  normalizeSdeHost,
};

function assertNoSdeEnvForHttpMode(): void {
  // In HTTP mode, the *client* is expected to supply SD Elements credentials.
  // Refuse to start if the server process has these set to avoid accidental leakage.
  const forbidden = ["SDE_HOST", "SDE_API_KEY"] as const;
  const present = forbidden.filter((k) => {
    const v = process.env[k];
    return typeof v === "string" && v.length > 0;
  });

  if (present.length > 0) {
    throw new Error(
      `Refusing to start HTTP mode while ${present.join(
        ", "
      )} is set. Unset these env vars so the HTTP client must provide credentials.`
    );
  }
}

function readWhitelist(): Set<string> {
  const raw = process.env.MCP_SDE_INSTANCE_ALLOWLIST;
  if (!raw) {
    throw new Error(
      "Missing MCP_SDE_INSTANCE_ALLOWLIST. HTTP mode requires a comma-separated list of allowed SDE hosts."
    );
  }

  const entries = raw.split(",").map((entry) => ({
    raw: entry,
    normalized: normalizeSdeHost(entry),
  }));

  const invalidEntries = entries
    .filter((entry) => !entry.normalized)
    .map((entry) => entry.raw.trim())
    .filter((entry) => entry.length > 0);

  if (invalidEntries.length > 0) {
    throw new Error(
      `Invalid MCP_SDE_INSTANCE_ALLOWLIST entries: ${invalidEntries.join(
        ", "
      )}. Expected https://host (or http://host when SDE_ALLOW_INSECURE_HTTP=true).`
    );
  }

  const normalizedEntries = entries
    .map((entry) => entry.normalized)
    .filter((entry): entry is string => Boolean(entry));

  if (normalizedEntries.length === 0) {
    throw new Error(
      "MCP_SDE_INSTANCE_ALLOWLIST is empty. Provide at least one allowed SDE host."
    );
  }

  return new Set(normalizedEntries);
}

function readSdeCredsFromRequest(req: {
  headers: Record<string, unknown>;
  body: unknown;
}): SdeCreds | null {
  // Node/Express lower-case header keys, even if the client sends `SDE_HOST`.
  // Support both the "env-like" names and the earlier x-* variants.
  const headerHost = req.headers["sde_host"] ?? req.headers["x-sde-host"];
  const headerApiKey =
    req.headers["sde_api_key"] ?? req.headers["x-sde-api-key"];

  const host =
    typeof headerHost === "string"
      ? headerHost
      : typeof (req.body as { sde_host?: unknown } | null)?.sde_host ===
        "string"
      ? ((req.body as { sde_host?: unknown }).sde_host as string)
      : typeof (req.body as { params?: { sde_host?: unknown } } | null)?.params
          ?.sde_host === "string"
      ? ((req.body as { params: { sde_host: unknown } }).params
          .sde_host as string)
      : null;

  const apiKey =
    typeof headerApiKey === "string"
      ? headerApiKey
      : typeof (req.body as { sde_api_key?: unknown } | null)?.sde_api_key ===
        "string"
      ? ((req.body as { sde_api_key?: unknown }).sde_api_key as string)
      : typeof (req.body as { params?: { sde_api_key?: unknown } } | null)
          ?.params?.sde_api_key === "string"
      ? ((req.body as { params: { sde_api_key: unknown } }).params
          .sde_api_key as string)
      : null;

  if (!host || !apiKey) return null;
  const normalizedHost = normalizeSdeHost(host);
  if (!normalizedHost) return null;
  return { host: normalizedHost, apiKey };
}

function readEnvPort(value: string | undefined, fallback: number): number {
  if (!value) return fallback;
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export async function main(): Promise<void> {
  checkNodeVersion();
  assertNoSdeEnvForHttpMode();
  const whitelist = readWhitelist();

  const host = process.env.MCP_HOST ?? "127.0.0.1";
  const port = readEnvPort(process.env.MCP_PORT, 3000);

  const app = createMcpExpressApp({ host });

  // Store per-session server/transport; Streamable HTTP requires a session for non-init requests.
  const sessions = new Map<string, SessionEntry>();

  app.all("/mcp", async (req, res) => {
    try {
      const sessionIdHeader = req.headers["mcp-session-id"];
      const sessionId =
        typeof sessionIdHeader === "string" ? sessionIdHeader : undefined;

      const isInitRequest =
        req.method === "POST" && isInitializeRequest(req.body as unknown);

      let entry: SessionEntry | undefined;
      if (sessionId) {
        entry = sessions.get(sessionId);
      }

      if (!entry) {
        if (!isInitRequest) {
          res.status(400).json({
            jsonrpc: "2.0",
            error: {
              code: -32000,
              message: "Bad Request: No valid session ID provided",
            },
            id: null,
          });
          return;
        }

        const creds = readSdeCredsFromRequest({
          headers: req.headers as unknown as Record<string, unknown>,
          body: req.body,
        });
        if (!creds) {
          res.status(400).json({
            jsonrpc: "2.0",
            error: {
              code: -32000,
              message:
                "Missing SD Elements credentials for HTTP mode. Provide SDE_HOST and SDE_API_KEY headers (or sde_host/sde_api_key in the initialize request).",
            },
            id: null,
          });
          return;
        }

        if (!whitelist.has(creds.host)) {
          res.status(403).json({
            jsonrpc: "2.0",
            error: {
              code: -32000,
              message:
                "Forbidden: SDE_HOST is not allowed by MCP_SDE_INSTANCE_ALLOWLIST.",
            },
            id: null,
          });
          return;
        }

        const server = createServer({ host: creds.host, apiKey: creds.apiKey });
        const transport = new StreamableHTTPServerTransport({
          sessionIdGenerator: () => randomUUID(),
          onsessioninitialized: (sid) => {
            sessions.set(sid, { transport, server });
          },
          onsessionclosed: (sid) => {
            sessions.delete(sid);
          },
        });

        transport.onclose = () => {
          const sid = transport.sessionId;
          if (sid) sessions.delete(sid);
        };

        await server.connect(transport);
        entry = { transport, server };
      }

      const bodyForTransport = isInitRequest
        ? redactSdeCredsFromInitBody(req.body)
        : req.body;

      await entry.transport.handleRequest(
        req as unknown as IncomingMessage,
        res as unknown as ServerResponse,
        bodyForTransport
      );
    } catch (error: unknown) {
      console.error("Error handling MCP HTTP request:", error);
      if (!(res as unknown as { headersSent?: boolean }).headersSent) {
        res.status(500).json({
          jsonrpc: "2.0",
          error: { code: -32603, message: "Internal server error" },
          id: null,
        });
      }
    }
  });

  setupSignalHandlers(async () => {
    const closing = Array.from(sessions.values()).map(async ({ server }) => {
      await server.close();
    });
    await Promise.allSettled(closing);
  });

  await new Promise<void>((resolve, reject) => {
    app.listen(port, host, (err?: unknown) => {
      if (err) reject(err);
      else resolve();
    });
  });

  console.log(`MCP server running on http://${host}:${port}/mcp`);
}
