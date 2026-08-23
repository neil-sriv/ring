import { defineConfig } from "@vite-pwa/assets-generator/config"

/* Terracotta tile color — mirrors --color-primary in src/app.css and the
   <rect> fill in public/assets/images/logo.svg. Maskable and Apple icons are
   composited on it so the tile bleeds to the edges under any platform mask. */
const TILE = "#ba512c"

/* Regenerate the raster icons in public/assets/images/ from logo.svg:
     pnpm run generate-pwa-assets
   Padding is 0 everywhere because logo.svg already carries its own margin:
   the ring sits inside the center 70%, which is inside the maskable safe zone. */
export default defineConfig({
  images: ["public/assets/images/logo.svg"],
  preset: {
    transparent: {
      sizes: [64, 192, 512],
      favicons: [[48, "favicon.ico"]],
      padding: 0,
      resizeOptions: { fit: "contain", background: "transparent" },
    },
    maskable: {
      sizes: [512],
      padding: 0,
      resizeOptions: { fit: "contain", background: TILE },
    },
    apple: {
      sizes: [180],
      padding: 0,
      resizeOptions: { fit: "contain", background: TILE },
    },
  },
})
