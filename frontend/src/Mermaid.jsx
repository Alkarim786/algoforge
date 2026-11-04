import { useEffect, useId, useState } from "react";
import { usePrefersDark } from "./theme.js";

let mermaidModule;
const loadMermaid = () => (mermaidModule ??= import("mermaid").then((module) => module.default));

// Node colour shows its role: steps blue, decisions amber, start/end green.
const PALETTE = {
  light: {
    step: "fill:#eef3ff,stroke:#5b7cf0,color:#1b2559",
    decision: "fill:#fff4e0,stroke:#e0a03a,color:#4a3300",
    terminal: "fill:#e6f5ec,stroke:#38a169,color:#123d27",
    theme: {
      lineColor: "#8a94a6",
      textColor: "#1c2026",
      primaryTextColor: "#1c2026",
      edgeLabelBackground: "#ffffff",
      clusterBkg: "#f7f8fa",
      clusterBorder: "#d6dae1",
      titleColor: "#4a5160",
    },
  },
  dark: {
    step: "fill:#1e2846,stroke:#7c9cff,color:#e3e9ff",
    decision: "fill:#3a2d12,stroke:#e9b04d,color:#ffe8bf",
    terminal: "fill:#15342a,stroke:#4cc38a,color:#d4f5e3",
    theme: {
      lineColor: "#7d8796",
      textColor: "#e8eaed",
      primaryTextColor: "#e8eaed",
      edgeLabelBackground: "#1d2126",
      clusterBkg: "#181c21",
      clusterBorder: "#3a414b",
      titleColor: "#aab2bd",
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
            fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
            fontSize: "14px",
            ...palette.theme,
          },
          themeCSS: [
            ".node rect { rx: 8px; ry: 8px; }",
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
