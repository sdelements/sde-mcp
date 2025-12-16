import { defineConfig } from "vitest/config";

// Avoid process forking in constrained environments (e.g., sandbox/CI) which can
// trigger EPERM on worker teardown. Threads keep everything in-process.
export default defineConfig({
  test: {
    environment: "node",
    pool: "threads",
    include: ["tests/**/*.test.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov", "html"],
      reportsDirectory: "coverage",
      all: true,
      include: ["src/**/*.ts"],
      exclude: [
        "**/*.d.ts",
        "**/*.test.ts",
        "**/*.spec.ts",
        "dist/**",
        "node_modules/**",
      ],
    },
  },
});





