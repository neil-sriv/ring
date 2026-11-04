import { defineConfig } from "vitest/config"

export default defineConfig({
  test: {
    environment: "jsdom",
    include: ["src/hooks/**/*.test.ts", "src/hooks/**/*.test.tsx"],
    setupFiles: ["./src/test-setup.ts"],
  },
})
