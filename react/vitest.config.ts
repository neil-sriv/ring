import path from "node:path"
import { defineConfig } from "vitest/config"

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    environment: "jsdom",
    include: [
      "src/hooks/**/*.test.ts",
      "src/hooks/**/*.test.tsx",
      "src/components/Loops/EditLoop.test.tsx",
      "src/components/Loops/AddLoop.test.tsx",
      "src/components/Loops/AddAdhocLoop.test.tsx",
    ],
    setupFiles: ["./src/test-setup.ts"],
  },
})
