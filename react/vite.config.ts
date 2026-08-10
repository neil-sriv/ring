import path from "node:path"
import tailwindcss from "@tailwindcss/vite"
import { TanStackRouterVite } from "@tanstack/router-vite-plugin"
import react from "@vitejs/plugin-react-swc"
import { defineConfig } from "vite"
import { VitePWA, type VitePWAOptions } from "vite-plugin-pwa"
import topLevelAwait from "vite-plugin-top-level-await"
import wasm from "vite-plugin-wasm"

const pwaOptions: Partial<VitePWAOptions> = {
  mode: "development",
  base: "/",
  includeAssets: ["public/**/*"],
  srcDir: "src",
  filename: "sw.js",
  strategies: "injectManifest",
  manifest: {
    name: process.env.ENVIRONMENT === "LOCAL" ? "Ring localhost" : "Ring",
    short_name: "Ring",
    theme_color: "#051a3b",
    icons: [
      {
        src: "/assets/images/pwa-192x192.png", // <== don't add slash, for testing
        sizes: "192x192",
        type: "image/png",
      },
      {
        src: "/assets/images/pwa-512x512.png", // <== don't remove slash, for testing
        sizes: "512x512",
        type: "image/png",
      },
      {
        src: "/assets/images/pwa-512x512.png", // <== don't add slash, for testing
        sizes: "512x512",
        type: "image/png",
        purpose: "any maskable",
      },
    ],
  },
  devOptions: {
    // Opt out with SW_DEV=false (cloud HTTP Vite). Default remains enabled when unset.
    enabled: process.env.SW_DEV !== "false",
    /* when using generateSW the PWA plugin will switch to classic */
    type: "module",
    navigateFallback: "index.html",
  },
  injectManifest: {
    maximumFileSizeToCacheInBytes: 3 * 1024 * 1024,
  },
}

// const replaceOptions = { __DATE__: new Date().toISOString() };
// const claims = process.env.CLAIMS === "true";
// const reload = process.env.RELOAD_SW === "true";
// const selfDestroying = process.env.SW_DESTROY === "true";

// if (process.env.SW === "true") {
//   pwaOptions.srcDir = "src";
//   pwaOptions.filename = claims ? "claims-sw.ts" : "prompt-sw.ts";
//   pwaOptions.strategies = "injectManifest";
//   (pwaOptions.manifest as Partial<ManifestOptions>).name =
//     "PWA Inject Manifest";
//   (pwaOptions.manifest as Partial<ManifestOptions>).short_name = "PWA Inject";
//   pwaOptions.injectManifest = {
//     minify: false,
//     enableWorkboxModulesLogs: true,
//   };
// }

// if (claims) pwaOptions.registerType = "autoUpdate";

// if (reload) {
//   // @ts-expect-error just ignore
//   replaceOptions.__RELOAD_SW__ = "true";
// }

// Mirror SW_DEV into the client so main.tsx can skip registerSW when the
// VitePWA dev service worker is disabled (e.g. Cursor Cloud HTTP Vite).
const swDevEnabled = process.env.SW_DEV !== "false"

// https://vitejs.dev/config/
export default defineConfig({
  define: {
    "import.meta.env.VITE_SW_DEV": JSON.stringify(
      swDevEnabled ? "true" : "false",
    ),
  },
  plugins: [
    tailwindcss(),
    react(),
    TanStackRouterVite(),
    VitePWA({ ...pwaOptions, registerType: "autoUpdate" }),
    wasm(),
    topLevelAwait(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api/v1": {
        target: "http://localhost:8001",
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
