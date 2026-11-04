// Serves Monaco's prebuilt files from this app (copied to public/monaco by scripts/copy-monaco.mjs).
// The ESM build is hundreds of modules, which Vite's dev server can't pre-bundle, and the
// @monaco-editor/react default would load from a CDN at runtime.
import { loader } from "@monaco-editor/react";

loader.config({ paths: { vs: "/monaco/vs" } });

export const EDITOR_FONT = '"JetBrains Mono Variable", "JetBrains Mono", ui-monospace, Consolas, monospace';

let fontsMeasured = null;

/** Monaco measures character widths once, when the first editor is created. If the code font is still downloading
 * at that moment it measures a fallback font instead, and every click lands a little off where the caret goes (more
 * so further along a line). So: load the code font (regular and bold, which keywords use), then have every editor
 * measure again. */
function remeasureWhenFontLoads(monaco) {
  if (!document.fonts) return;
  fontsMeasured ??= Promise.all(
    ["400", "700"].map((weight) => document.fonts.load(`${weight} 14px "JetBrains Mono Variable"`)),
  )
    .then(() => document.fonts.ready)
    .then(() => monaco.editor.remeasureFonts())
    .catch(() => {});
}

/** Aurora colours for Monaco, and the font fix above. Pass as `beforeMount` on every <Editor>; running it twice is
 * harmless. */
export function defineEditorThemes(monaco) {
  remeasureWhenFontLoads(monaco);
  monaco.editor.defineTheme("aurora-light", {
    base: "vs",
    inherit: true,
    rules: [
      { token: "keyword", foreground: "1d4ed8", fontStyle: "bold" },
      { token: "string", foreground: "b45309" },
      { token: "number", foreground: "0e7490" },
      { token: "comment", foreground: "6b7794", fontStyle: "italic" },
      { token: "type", foreground: "0f766e" },
    ],
    colors: {
      "editor.background": "#f8fafe",
      "editor.foreground": "#111827",
      "editorLineNumber.foreground": "#9aa8c7",
      "editorLineNumber.activeForeground": "#1d4ed8",
      "editor.lineHighlightBackground": "#f1f5fc",
      "editor.selectionBackground": "#cfe0fb",
      "editorCursor.foreground": "#2563eb",
      "editorIndentGuide.background1": "#e5ebf6",
    },
  });
  monaco.editor.defineTheme("aurora-dark", {
    base: "vs-dark",
    inherit: true,
    rules: [
      { token: "keyword", foreground: "93c5fd", fontStyle: "bold" },
      { token: "string", foreground: "fcd34d" },
      { token: "number", foreground: "67e8f9" },
      { token: "comment", foreground: "8090b3", fontStyle: "italic" },
      { token: "type", foreground: "5eead4" },
    ],
    colors: {
      "editor.background": "#0c1424",
      "editor.foreground": "#e6edfb",
      "editorLineNumber.foreground": "#4a5a7d",
      "editorLineNumber.activeForeground": "#93c5fd",
      "editor.lineHighlightBackground": "#111d33",
      "editor.selectionBackground": "#1e3a6e",
      "editorCursor.foreground": "#93c5fd",
      "editorIndentGuide.background1": "#1a2540",
    },
  });
}

export const editorTheme = (dark) => (dark ? "aurora-dark" : "aurora-light");
