"use client";

import dynamic from "next/dynamic";
import { useMemo, useRef, useState, useEffect } from "react";

interface GraphData {
  nodes: { id: string; type: string; label: string; data?: Record<string, unknown> }[];
  edges: { source: string; target: string; type: string }[];
}

interface KnowledgeGraphViewProps {
  graphData: GraphData;
}

const ForceGraph2D = dynamic(() => import("react-force-graph-2d").then((mod) => mod.default), {
  ssr: false,
  loading: () => (
    <div className="h-full w-full animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-muted">
      Loading Graph Visualization...
    </div>
  ),
});

export default function KnowledgeGraphView({ graphData }: KnowledgeGraphViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (!containerRef.current) return;

    // Set initial dimensions immediately
    const rect = containerRef.current.getBoundingClientRect();
    setDimensions({ width: rect.width, height: rect.height });

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setDimensions({ width, height });
        }
      }
    });

    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  if (!graphData?.nodes?.length) {
    return (
      <div className="glass-card p-6 h-full flex items-center justify-center text-muted text-center">
        <p className="text-sm">No entity data available for Knowledge Graph</p>
      </div>
    );
  }

  const nodeColors: Record<string, string> = {
    Company: "#0ea5e9",
    Revenue: "#059669",
    Risk: "#dc2626",
    Regulation: "#6366f1",
    Assets: "#06b6d4",
    Market: "#f59e0b",
    Person: "#ec4899",
    Location: "#8b5cf6",
  };

  const gData = {
    nodes: graphData.nodes.map((n) => ({
      id: n.id,
      name: n.label,
      type: n.type,
      val: n.type === "Company" ? 10 : 5
    })),
    links: graphData.edges.map((e) => ({ source: e.source, target: e.target })),
  };

  return (
    <div className="glass-card p-6 h-full flex flex-col">
      <div className="flex justify-between items-center mb-4 flex-shrink-0">
        <h3 className="section-header">
          <svg xmlns="http://www.w3.org/2000/svg" className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
          Entity Knowledge Graph
        </h3>

        <div className="flex flex-wrap gap-2 justify-end max-w-md">
          {Object.entries(nodeColors).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1.5 text-xs bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-full border border-transparent dark:border-slate-700">
              <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
              <span className="text-muted-foreground">{type}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Graph Container — takes remaining space */}
      <div
        ref={containerRef}
        className="flex-1 w-full overflow-hidden rounded-xl border border-card-border bg-slate-50/50 dark:bg-slate-900/50"
        style={{ minHeight: "350px" }}
      >
        {dimensions.width > 0 && dimensions.height > 0 && (
          <ForceGraph2D
            width={dimensions.width}
            height={dimensions.height}
            graphData={gData}
            nodeLabel="name"
            nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
              const label = node.name;
              const fontSize = Math.max(10 / globalScale, 3);
              const radius = node.type === "Company" ? 8 : 5;

              // Node circle
              ctx.beginPath();
              ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
              ctx.fillStyle = nodeColors[node.type] || "#94a3b8";
              ctx.fill();
              ctx.strokeStyle = "rgba(255,255,255,0.5)";
              ctx.lineWidth = 1;
              ctx.stroke();

              // Label
              ctx.font = `${fontSize}px Inter, sans-serif`;
              ctx.textAlign = "center";
              ctx.textBaseline = "top";
              ctx.fillStyle = "#64748b";
              ctx.fillText(label, node.x, node.y + radius + 2);
            }}
            linkColor={() => "rgba(148, 163, 184, 0.25)"}
            linkDirectionalArrowLength={3.5}
            linkDirectionalArrowRelPos={1}
            linkWidth={1.5}
            cooldownTicks={100}
            d3AlphaDecay={0.02}
            d3VelocityDecay={0.3}
            enableZoomInteraction={true}
            enablePanInteraction={true}
          />
        )}
      </div>
    </div>
  );
}
