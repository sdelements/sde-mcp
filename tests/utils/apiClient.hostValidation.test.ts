import { afterEach, describe, expect, it } from "vitest";
import { SDElementsClient } from "../../src/utils/apiClient";

describe("SDElementsClient host validation", () => {
  afterEach(() => {
    delete process.env.SDE_ALLOW_INSECURE_HTTP;
  });

  it("accepts a clean https origin and normalizes trailing slash", () => {
    const client = new SDElementsClient({
      host: "https://example.test/",
      apiKey: "abc",
    });
    expect(client.getHost()).toBe("https://example.test");
  });

  it("rejects http by default", () => {
    expect(
      () =>
        new SDElementsClient({
          host: "http://example.test",
          apiKey: "abc",
        })
    ).toThrow(/Refusing to use non-https host/);
  });

  it("allows http when SDE_ALLOW_INSECURE_HTTP=true", () => {
    process.env.SDE_ALLOW_INSECURE_HTTP = "true";
    const client = new SDElementsClient({
      host: "http://example.test",
      apiKey: "abc",
    });
    expect(client.getHost()).toBe("http://example.test");
  });

  it("rejects hosts with paths", () => {
    expect(
      () =>
        new SDElementsClient({
          host: "https://example.test/api",
          apiKey: "abc",
        })
    ).toThrow(/Host URL must be an origin only/);
  });

  it("rejects hosts with query/fragment", () => {
    expect(
      () =>
        new SDElementsClient({
          host: "https://example.test/?x=1",
          apiKey: "abc",
        })
    ).toThrow(/must not include query or fragment/);

    expect(
      () =>
        new SDElementsClient({
          host: "https://example.test/#x",
          apiKey: "abc",
        })
    ).toThrow(/must not include query or fragment/);
  });

  it("rejects hosts with embedded credentials", () => {
    expect(
      () =>
        new SDElementsClient({
          host: "https://user:pass@example.test",
          apiKey: "abc",
        })
    ).toThrow(/must not include credentials/);
  });
});


