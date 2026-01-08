#!/usr/bin/env node

import { main as mainStdio } from "./stdio";
import { main as mainHttp } from "./http";

export { createServer, setupSignalHandlers } from "./mcp";
export { main } from "./stdio";
export { main as mainHttp } from "./http";

function hasNpmConfigFlag(name: string): boolean {
  // `npm start --http` does not reliably forward argv, but npm *does* expose it
  // as `npm_config_http=true` in the environment.
  const envKey = `npm_config_${name}`;
  const raw = process.env[envKey];
  return raw === "true" || raw === "1" || raw === "";
}

function hasArgFlag(flag: string): boolean {
  return process.argv.includes(flag);
}

const useHttp = hasArgFlag("--http") || hasNpmConfigFlag("http");

(useHttp ? mainHttp : mainStdio)().catch((err: unknown) => {
  console.error(err);
  process.exit(1);
});