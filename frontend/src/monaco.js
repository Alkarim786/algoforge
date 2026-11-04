// Serves Monaco's prebuilt files from this app (copied to public/monaco by scripts/copy-monaco.mjs).
// The ESM build is hundreds of modules, which Vite's dev server can't pre-bundle, and the
// @monaco-editor/react default would load from a CDN at runtime.
import { loader } from "@monaco-editor/react";

loader.config({ paths: { vs: "/monaco/vs" } });
