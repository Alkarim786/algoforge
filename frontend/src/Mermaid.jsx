import { useEffect, useId, useState } from "react";
import { usePrefersDark } from "./theme.js";

let mermaidModule;
const loadMermaid = () => (mermaidModule ??= import("mermaid").then((module) => module.default));

// Node colour shows its role: steps blue, decisions amber, start/end teal.
const PALETTE = {
  light: {
    step: "fill:#e8f0fe,stroke:#2563eb,color:#0b2a6b",
    decision: "fill:#fff4dc,stroke:#d97706,color:#4a2c00",
    terminal: "fill:#dcf7f1,stroke:#0d9488,color:#0b3b36",
    theme: {
      lineColor: "#8e9ab5",
      textColor: "#111827",
      primaryTextColor: "#111827",
      edgeLabelBackground: "#ffffff",
      clusterBkg: "#f6f8fc",
      clusterBorder: "#dbe3f0",
      titleColor: "#55607a",
    },
  },
  dark: {
    step: "fill:#14264a,stroke:#60a5fa,color:#e1ecff",
    decision: "fill:#3a2a10,stroke:#f5b544,color:#ffe9c2",
    terminal: "fill:#0f3330,stroke:#2dd4bf,color:#d2fbf3",
    theme: {
      lineColor: "#7a8aad",
      textColor: "#e6edfb",
      primaryTextColor: "#e6edfb",
      edgeLabelBackground: "#111a2c",
      clusterBkg: "#0c1424",
      clusterBorder: "#22304d",
      titleColor: "#aab8d6",
    },
  },
};

const SHAPE = /(?<!subgraph\s)\b([A-Za-z_]\w*)\s*(\(\["|\{")/g;

/** Adds colour classes to a flowchart from its node shapes, so content files stay plain Mermaid. */
export function colourise(chart, palette = PALETTE.light) {
  if (!/^\s*(flowchart|graph)\b/.test(chart)) return chart;
  const decisions = new Set();
  const terminals = new Set();
  for (const [, id, opener] of chart.matchAll(SHAPE)) {
    (opener === '{"' ? decisions : terminals).add(id);
  }
  const lines = [chart.trimEnd(), `classDef default ${palette.step},stroke-width:1.5px`];
  lines.push(`classDef decision ${palette.decision},stroke-width:1.5px`);
  lines.push(`classDef terminal ${palette.terminal},stroke-width:1.5px`);
  if (decisions.size) lines.push(`class ${[...decisions].join(",")} decision`);
  if (terminals.size) lines.push(`class ${[...terminals].join(",")} terminal`);
  return lines.join("\n");
}

/** Renders hand-authored Mermaid text from our own content files. */
export default function MermaidDiagram({ chart }) {
  const dark = usePrefersDark();
  const id = `mermaid-${useId().replace(/[^a-zA-Z0-9]/g, "")}`;
  const [svg, setSvg] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let current = true;
    const palette = dark ? PALETTE.dark : PALETTE.light;
    loadMermaid()
      .then(async (mermaid) => {
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: "strict",
          theme: "base",
          themeVariables: {
            fontFamily: '"Plus Jakarta Sans Variable", system-ui, sans-serif',
            fontSize: "14px",
            ...palette.theme,
          },
          themeCSS: [
            ".node rect { rx: 10px; ry: 10px; }",
            // Edge labels otherwise keep the theme's dark default text, unreadable in dark mode.
            `.edgeLabel, .edgeLabel p, .edgeLabel span { font-size: 12px; color: ${palette.theme.titleColor} !important; }`,
            `.edgeLabel rect, .labelBkg { fill: ${palette.theme.edgeLabelBackground} !important; background: ${palette.theme.edgeLabelBackground} !important; }`,
            `.cluster-label, .cluster-label span { color: ${palette.theme.titleColor} !important; }`,
          ].join(" "),
          flowchart: { padding: 12, nodeSpacing: 36, rankSpacing: 40 },
        });
        const result = await mermaid.render(id, colourise(chart, palette));
        if (current) setSvg(result.svg);
      })
      .catch((failure) => current && setError(String(failure?.message ?? failure)));
    return () => {
      current = false;
    };
  }, [chart, dark, id]);

  if (error) {
    return (
      <div className="diagram diagram-error" role="alert">
        Couldn't draw this diagram: {error}
      </div>
    );
  }
  if (!svg) return <div className="diagram muted small">Drawing diagram…</div>;
  return <div className="diagram" role="img" aria-label="Diagram" dangerouslySetInnerHTML={{ __html: svg }} />;
}
