"use client";

import { useState } from "react";

interface AIInsightsProps {
  data: {
    executive_summary?: string | null;
    financial_performance_overview?: string | null;
    risk_analysis?: string | null;
    trend_detection?: string | null;
    investment_recommendation?: string | null;
    red_flags?: string[];
    investor_slides?: { title: string; bullets: string[] }[];
    compliance?: {
      ifrs_mentioned?: boolean;
      gaap_mentioned?: boolean;
      esg_mentioned?: boolean;
      standard_notes?: string;
    };
  };
  confidenceScore?: number | null;
}

export default function AIInsights({ data, confidenceScore }: AIInsightsProps) {
  const [activeTab, setActiveTab] = useState("exec");

  const tabs = [
    { id: "exec", label: "Executive Summary", content: data.executive_summary },
    { id: "fin", label: "Financial Analysis", content: data.financial_performance_overview },
    { id: "risk", label: "Risk Analysis", content: data.risk_analysis },
    { id: "trend", label: "Trend Detection", content: data.trend_detection },
    { id: "rec", label: "Recommendation", content: data.investment_recommendation },
  ];

  const renderMarkdown = (text: string) => {
    if (!text) return <p className="text-muted italic">No analysis available for this section.</p>;

    return text.split("\n").map((line, i) => {
      if (line.startsWith("## ")) {
        return <h4 key={i} className="mt-6 mb-3 text-lg font-bold text-foreground">{line.replace("## ", "")}</h4>;
      }
      if (line.startsWith("### ")) {
        return <h5 key={i} className="mt-4 mb-2 text-md font-bold text-foreground/90">{line.replace("### ", "")}</h5>;
      }
      if (line.trim().startsWith("* ") || line.trim().startsWith("- ")) {
        const content = line.trim().substring(2);
        return (
          <li key={i} className="ml-4 list-disc text-sm text-foreground/80 my-1 pl-1">
            {renderBold(content)}
          </li>
        );
      }
      if (!line.trim()) return <div key={i} className="h-3" />;

      return (
        <p key={i} className="text-sm text-foreground/80 leading-relaxed mb-2">
          {renderBold(line)}
        </p>
      );
    });
  };

  const renderBold = (text: string) => {
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={index} className="font-semibold text-foreground">{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  return (
    <div className="glass-card flex flex-col h-full min-h-[500px]">
      <div className="p-6 border-b border-card-border">
        <div className="flex justify-between items-start mb-6">
          <div>
            <h3 className="section-header">
              <svg xmlns="http://www.w3.org/2000/svg" className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              AI-Generated Insights
            </h3>
            <p className="text-sm text-muted mt-1">Deep analysis powered by Groq Llama-3 70B</p>
          </div>

          <div className="flex gap-2">
            {data.compliance?.ifrs_mentioned && <span className="badge badge-info">IFRS</span>}
            {data.compliance?.gaap_mentioned && <span className="badge badge-info">GAAP</span>}
            {data.compliance?.esg_mentioned && <span className="badge badge-positive">ESG</span>}
          </div>
        </div>

        <div className="flex gap-2 overflow-x-auto pb-2 custom-scrollbar">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`tab-btn ${activeTab === tab.id ? "active" : ""}`}
            >
              {tab.label}
            </button>
          ))}
          {data.red_flags && data.red_flags.length > 0 && (
            <button
              onClick={() => setActiveTab("flags")}
              className={`tab-btn text-negative hover:bg-negative/10 ${activeTab === "flags" ? "active bg-negative/10 text-negative font-bold" : ""}`}
            >
              Red Flags ({data.red_flags.length})
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 p-6 overflow-y-auto custom-scrollbar animate-fade-in group">
        {activeTab === "flags" ? (
          <div className="space-y-4">
            <div className="p-4 rounded-lg bg-red-50/50 border border-red-200 dark:bg-red-900/10 dark:border-red-900/30">
              <h4 className="flex items-center gap-2 font-bold text-negative mb-4">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Critical Risk Factors Detected
              </h4>
              <ul className="space-y-3">
                {data.red_flags?.map((flag, i) => (
                  <li key={i} className="flex gap-3 text-sm text-foreground/80">
                    <span className="text-negative font-bold">•</span>
                    {flag}
                  </li>
                ))}
              </ul>
            </div>
            <p className="text-xs text-muted text-center pt-4">
              These flags are automatically extracted patterns indicating potential financial distress or governance issues.
            </p>
          </div>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {renderMarkdown(tabs.find(t => t.id === activeTab)?.content || "")}
          </div>
        )}
      </div>

      <div className="p-4 border-t border-card-border bg-card/50 text-xs text-muted flex justify-between items-center">
        <span>
          Generated: {new Date().toLocaleDateString()}
        </span>
        {confidenceScore != null && (
          <span className={`font-semibold ${confidenceScore > 0.7 ? "text-positive" : "text-warning"}`}>
            confidence: {Math.round(confidenceScore * 100)}%
          </span>
        )}
      </div>
    </div>
  );
}
