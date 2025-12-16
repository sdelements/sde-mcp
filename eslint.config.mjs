// @ts-check

import eslint from "@eslint/js";
import { defineConfig } from "eslint/config";
import tseslint from "typescript-eslint";

export default defineConfig(
  {
    // Place global ignores in a configuration object
    ignores: ["dist/**/*", "build/**/*"],
  },
  eslint.configs.recommended,
  tseslint.configs.recommended
);
