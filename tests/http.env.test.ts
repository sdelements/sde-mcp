import { afterEach, describe, expect, it } from "vitest";
import { main as httpMain } from "../src/http";

describe("src/http (env isolation)", () => {
  afterEach(() => {
    delete process.env.SDE_HOST;
    delete process.env.SDE_API_KEY;
    delete process.env.MCP_SDE_INSTANCE_ALLOWLIST;
    delete process.env.SDE_ALLOW_INSECURE_HTTP;
  });

  it("refuses to start in HTTP mode when SDE_HOST is set", async () => {
    process.env.SDE_HOST = "https://example.test";
    await expect(httpMain()).rejects.toThrow(/SDE_HOST/);
  });

  it("refuses to start in HTTP mode when SDE_API_KEY is set", async () => {
    process.env.SDE_API_KEY = "secret";
    await expect(httpMain()).rejects.toThrow(/SDE_API_KEY/);
  });

  it("refuses to start in HTTP mode when both are set", async () => {
    process.env.SDE_HOST = "https://example.test";
    process.env.SDE_API_KEY = "secret";
    await expect(httpMain()).rejects.toThrow(
      /SDE_HOST, SDE_API_KEY|SDE_API_KEY, SDE_HOST/
    );
  });

  it("refuses to start in HTTP mode when allowlist is missing", async () => {
    await expect(httpMain()).rejects.toThrow(/MCP_SDE_INSTANCE_ALLOWLIST/);
  });

  it("refuses to start in HTTP mode when allowlist is empty", async () => {
    process.env.MCP_SDE_INSTANCE_ALLOWLIST = " , ";
    await expect(httpMain()).rejects.toThrow(/MCP_SDE_INSTANCE_ALLOWLIST/);
  });

  it("refuses to start in HTTP mode when allowlist has invalid hosts", async () => {
    process.env.MCP_SDE_INSTANCE_ALLOWLIST = "https://example.test/path";
    await expect(httpMain()).rejects.toThrow(
      /Invalid MCP_SDE_INSTANCE_ALLOWLIST/
    );
  });

  it("refuses to start in HTTP mode when allowlist uses http without unsafe flag", async () => {
    process.env.MCP_SDE_INSTANCE_ALLOWLIST = "http://example.test";
    await expect(httpMain()).rejects.toThrow(/MCP_SDE_INSTANCE_ALLOWLIST/);
  });
});
