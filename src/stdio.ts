import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { createServer, setupSignalHandlers } from "./mcp";
import { checkNodeVersion } from "./utils/version";

export async function main(): Promise<void> {
  checkNodeVersion();

  const server = createServer();
  setupSignalHandlers(async () => server.close());

  const stdioTransport = new StdioServerTransport();
  await server.connect(stdioTransport);
  console.error("MCP server running on stdio");
}
