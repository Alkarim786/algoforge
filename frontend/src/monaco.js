// Serves Monaco's prebuilt files from this app (copied to public/monaco by scripts/copy-monaco.mjs).
// The ESM build is hundreds of modules, which Vite's dev server can't pre-bundle, and the
// @monaco-editor/react default would load from a CDN at runtime.
import { loader } from "@monaco-editor/react";

loader.config({ paths: { vs: "/monaco/vs" } });

export const EDITOR_FONT = '"JetBrains Mono Variable", "JetBrains Mono", ui-monospace, Consolas, monospace';

/** Aurora colours for Monaco. Pass as `beforeMount` on every <Editor>; defining a theme twice is harmless. */
export function defineEditorThemes(monaco) {
  monaco.editor.defineTheme("aurora-light", {
    base: "vs",
    inherit: true,
    rules: [
      { token: "keyword", foreground: "6d28d9", fontStyle: "bold" },
      { token: "string", foreground: "b45309" },
      { token: "number", foreground: "0e7490" },
      { token: "comment", foreground: "7a7398", fontStyle: "italic" },
      { token: "type", foreground: "0f766e" },
    ],
    colors: {
      "editor.background": "#fbfaff",
      "editor.foreground": "#1b1533",
      "editorLineNumber.foreground": "#a39cc4",
      "editorLineNumber.activeForeground": "#6d28d9",
      "editor.lineHighlightBackground": "#f3f0ff",
      "editor.selectionBackground": "#ddd0ff",
      "editorCursor.foreground": "#6d28d9",
      "editorIndentGuide.background1": "#ece8fb",
    },
  });
  monaco.editor.defineTheme("aurora-dark", {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "keyword", foreground: "c4b5fd", fontStyle: "bold" },
      { token: "string", foreground: "fcd34d" },
      { token: "number", foreground: "67e8f9" },
      { token: "comment", foreground: "8c84b3", fontStyle: "italic" },
      { token: "type", foreground: "5eead4" },
    ],
    colors: {
      "editor.background": "#120f22",
      "editor.foreground": "#f0ecff",
      "editorLineNumber.foreground": "#5d5585",
      "editorLineNumber.activeForeground": "#c4b5fd",
      "editor.lineHighlightBackground": "#1a1630",
      "editor.selectionBackground": "#3b2f6e",
      "editorCursor.foreground": "#c4b5fd",
      "editorIndentGuide.background1": "#241e40",
    },
  });
}

export const editorTheme = (dark) => (dark ? "aurora-dark" : "aurora-light");
