"use client";

interface RiskHeatmapProps {
  risks: string[];
  riskScore?: number | null;
}

export default function RiskHeatmap({ risks, riskScore }: RiskHeatmapProps) {
  if (!risks?.length && riskScore == null) return null;

  // Classify risks based on keywords
  const classifiedRisks = risks.map(r => {
    const text = r.toLowerCase();
    let severity: "high" | "medium" | "low" = "low";
    let type = "Operational";

    // Severity logic
    if (text.match(/critical|severe|material|litigation|regulatory|fraud/)) severity = "high";
    else if (text.match(/significant|major|volatility|currency|compliance/)) severity = "medium";

    // Type logic
    if (text.match(/market|compet|demand|price/)) type = "Market";
    else if (text.match(/financ|credit|liquidity|rate|currenc/)) type = "Financial";
    else if (text.match(/regulat|law|compliance|gov/)) type = "Regulatory";
    else if (text.match(/tech|cyber|data|security/)) type = "Technology";

    return { text: r, severity, type };
  });

  const getBadgeColor = (severity: string) => {
    switch (severity) {
      case "high": return "badge-negative";
      case "medium": return "badge-warning";
      default: return "badge-info";
    }
  };

  return (
    <div className="glass-card p-6 h-full flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <h3 className="section-header">
          <svg xmlns="http://www.w3.org/2000/svg" className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          Risk Matrix
        </h3>
        {riskScore != null && (
          <div className="flex flex-col items-end">
            <span className="text-xs text-muted font-semibold uppercase">Overall Score</span>
            <span className={`text-2xl font-bold ${riskScore > 60 ? "text-negative" : riskScore > 30 ? "text-warning" : "text-positive"
              }`}>
              {riskScore}/100
            </span>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar space-y-3 max-h-[400px]">
        {classifiedRisks.length === 0 ? (
          <div className="text-center text-muted py-8">No specific risks identified.</div>
        ) : (
          classifiedRisks.map((risk, idx) => (
            <div
              key={idx}
              className={`
                p-4 rounded-lg border border-l-4 transition-all hover:translate-x-1
                ${risk.severity === 'high'
                  ? 'bg-red-50/50 border-red-200 border-l-red-500 dark:bg-red-900/10 dark:border-red-900'
                  : risk.severity === 'medium'
                    ? 'bg-amber-50/50 border-amber-200 border-l-amber-500 dark:bg-amber-900/10 dark:border-amber-900'
                    : 'bg-slate-50/50 border-slate-200 border-l-blue-400 dark:bg-slate-800/50 dark:border-slate-700'
                }
              `}
            >
              <div className="flex justify-between items-start mb-1">
                <span className="text-xs font-bold text-muted uppercase tracking-wider">{risk.type}</span>
                <span className={`badge ${getBadgeColor(risk.severity)}`}>
                  {risk.severity} Risk
                </span>
              </div>
              <p className="text-sm text-foreground/80 leading-relaxed">
                {risk.text}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
