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
