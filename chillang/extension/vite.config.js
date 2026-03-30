import { svelte } from "@sveltejs/vite-plugin-svelte";
import { cpSync, existsSync, rmSync } from "fs";
import { resolve } from "path";
import { defineConfig } from "vite";

function flattenHtml() {
  return {
    name: "flatten-html",
    closeBundle() {
      const nested = resolve(__dirname, "dist/src/wordbank/wordbank.html");
      const flat = resolve(__dirname, "dist/wordbank.html");
      if (existsSync(nested)) {
        cpSync(nested, flat);
        rmSync(resolve(__dirname, "dist/src"), { recursive: true });
      }
    },
  };
}

const target = process.env.BUILD_TARGET;

// Content script build: IIFE (no imports, runs in page context)
const contentConfig = defineConfig({
  plugins: [svelte({ emitCss: false })],
  build: {
    outDir: "dist",
    emptyOutDir: false,
    lib: {
      entry: resolve(__dirname, "src/content/content.js"),
      name: "ChilLangContent",
      formats: ["iife"],
      fileName: () => "content.js",
    },
  },
});

// Service worker + wordbank build: ES modules
const mainConfig = defineConfig({
  plugins: [svelte({ emitCss: false }), flattenHtml()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        "service-worker": resolve(
          __dirname,
          "src/background/service-worker.js"
        ),
        wordbank: resolve(__dirname, "src/wordbank/wordbank.html"),
      },
      output: {
        entryFileNames: "[name].js",
        chunkFileNames: "chunks/[name]-[hash].js",
        assetFileNames: "assets/[name][extname]",
      },
    },
  },
});

export default target === "content" ? contentConfig : mainConfig;
