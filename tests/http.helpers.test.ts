import { describe, expect, it } from "vitest";
import { __test__ } from "../src/http";

describe("src/http helpers", () => {
  it("reads creds from headers (case-insensitive on the wire; lowercased in node)", () => {
    const creds = __test__.readSdeCredsFromRequest({
      headers: { sde_host: "https://example.test", sde_api_key: "abc" },
      body: {},
    });
    expect(creds).toEqual({ host: "https://example.test", apiKey: "abc" });
  });

  it("reads creds from init body (top-level)", () => {
    const creds = __test__.readSdeCredsFromRequest({
      headers: {},
      body: { sde_host: "https://example.test", sde_api_key: "abc" },
    });
    expect(creds).toEqual({ host: "https://example.test", apiKey: "abc" });
  });

  it("reads creds from init body (params.*)", () => {
    const creds = __test__.readSdeCredsFromRequest({
      headers: {},
      body: {
        params: { sde_host: "https://example.test", sde_api_key: "abc" },
      },
    });
    expect(creds).toEqual({ host: "https://example.test", apiKey: "abc" });
  });

  it("normalizes hosts when reading creds", () => {
    const creds = __test__.readSdeCredsFromRequest({
      headers: { sde_host: "https://example.test/", sde_api_key: "abc" },
      body: {},
    });
    expect(creds).toEqual({ host: "https://example.test", apiKey: "abc" });
  });

  it("normalizes host values for whitelist comparisons", () => {
    expect(__test__.normalizeSdeHost(" https://example.test/ ")).toBe(
      "https://example.test"
    );
    expect(__test__.normalizeSdeHost("http://example.test/")).toBe(
      "http://example.test"
    );
  });

  it("returns null for invalid host shapes", () => {
    expect(__test__.normalizeSdeHost("https://example.test/path")).toBeNull();
    expect(__test__.normalizeSdeHost("notaurl")).toBeNull();
  });

  it("allows http hosts only when unsafe flag is set", () => {
    const original = process.env.SDE_ALLOW_INSECURE_HTTP;
    delete process.env.SDE_ALLOW_INSECURE_HTTP;
    expect(__test__.normalizeSdeHost("http://example.test")).toBeNull();

    process.env.SDE_ALLOW_INSECURE_HTTP = "true";
    expect(__test__.normalizeSdeHost("http://example.test")).toBe(
      "http://example.test"
    );

    if (original === undefined) {
      delete process.env.SDE_ALLOW_INSECURE_HTTP;
    } else {
      process.env.SDE_ALLOW_INSECURE_HTTP = original;
    }
  });

  it("returns null when either host or apiKey is missing", () => {
    expect(
      __test__.readSdeCredsFromRequest({
        headers: { sde_host: "https://example.test" },
        body: {},
      })
    ).toBeNull();
    expect(
      __test__.readSdeCredsFromRequest({
        headers: { sde_api_key: "abc" },
        body: {},
      })
    ).toBeNull();
  });

  it("redacts creds from init body before handing to MCP transport", () => {
    const redacted = __test__.redactSdeCredsFromInitBody({
      jsonrpc: "2.0",
      method: "initialize",
      params: {
        sde_host: "https://example.test",
        sde_api_key: "abc",
        keep: 123,
      },
      sde_host: "https://example.test",
      sde_api_key: "abc",
    }) as Record<string, unknown>;

    expect(redacted.sde_host).toBeUndefined();
    expect(redacted.sde_api_key).toBeUndefined();
    expect(
      (redacted.params as Record<string, unknown>).sde_host
    ).toBeUndefined();
    expect(
      (redacted.params as Record<string, unknown>).sde_api_key
    ).toBeUndefined();
    expect((redacted.params as Record<string, unknown>).keep).toBe(123);
  });
});
