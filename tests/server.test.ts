import { describe, expect, it, vi, afterEach } from "vitest";
import { createServer, setupSignalHandlers } from "../src/server.js";

describe("src/server", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    delete process.env.SDE_HOST;
    delete process.env.SDE_API_KEY;
  });

  it("createServer returns a server instance when env vars are present", () => {
    process.env.SDE_HOST = "https://example.test";
    process.env.SDE_API_KEY = "abc";

    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        return new Response(JSON.stringify({ results: [] }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }) as unknown as typeof fetch
    );

    const server = createServer();
    expect(server).toBeTruthy();
    const connect = (server as unknown as { connect?: unknown }).connect;
    expect(connect).toBeTypeOf("function");
  });

  it("setupSignalHandlers registers SIGINT and SIGTERM handlers and exits after cleanup", async () => {
    const handlers = new Map<string, () => Promise<void>>();
    const onSpy = vi
      .spyOn(process, "on")
      .mockImplementation((event: unknown, listener: unknown) => {
        handlers.set(String(event), listener as () => Promise<void>);
        return process;
      });

    const cleanup = vi.fn().mockResolvedValue(undefined);
    const exitSpy = vi.spyOn(process, "exit").mockImplementation(((
      _code?: number
    ) => {
      void _code;
      return undefined as never;
    }) as unknown as typeof process.exit);

    setupSignalHandlers(cleanup);

    expect(onSpy).toHaveBeenCalledWith("SIGINT", expect.any(Function));
    expect(onSpy).toHaveBeenCalledWith("SIGTERM", expect.any(Function));

    await handlers.get("SIGINT")?.();
    expect(cleanup).toHaveBeenCalledTimes(1);
    expect(exitSpy).toHaveBeenCalledWith(0);

    await handlers.get("SIGTERM")?.();
    expect(cleanup).toHaveBeenCalledTimes(2);
    expect(exitSpy).toHaveBeenCalledWith(0);
  });
});


