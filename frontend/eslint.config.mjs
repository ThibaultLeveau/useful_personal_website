import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";
import storybook from "eslint-plugin-storybook";

export default defineConfig([
  ...nextVitals,
  ...nextTypescript,
  ...storybook.configs["flat/recommended"],
  globalIgnores([
    ".next/**",
    ".storybook-static/**",
    "coverage/**",
    "playwright-report/**",
    "test-results/**",
    "next-env.d.ts",
  ]),
]);
