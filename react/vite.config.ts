import { TanStackRouterVite } from "@tanstack/router-vite-plugin";
import react from "@vitejs/plugin-react-swc";
import { defineConfig } from "vite";
import { VitePWA, VitePWAOptions } from "vite-plugin-pwa";

const pwaOptions: Partial<VitePWAOptions> = {
  mode: "development",
  base: "/",
  includeAssets: ["public/**/*"],
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
    enabled: true,
    /* when using generateSW the PWA plugin will switch to classic */
    type: "module",
    navigateFallback: "index.html",
  },
};

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

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    TanStackRouterVite(),
    VitePWA({ ...pwaOptions, registerType: "autoUpdate" }),
  ],
});
