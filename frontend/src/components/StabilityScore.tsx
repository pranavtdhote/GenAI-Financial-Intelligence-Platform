"use client";

interface StabilityScoreProps {
    score: number;
}

export default function StabilityScore({ score }: StabilityScoreProps) {
    return (
        <div className="glass-card p-6 flex flex-col items-center justify-center text-center">
            <h3 className="text-sm font-semibold text-muted mb-4 uppercase tracking-wider">Financial Stability Score</h3>

            <div className="relative w-full h-4 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden mb-2">
                <div
                    className={`h-full transition-all duration-1000 ease-out rounded-full 
            ${score >= 80 ? 'bg-positive' : score >= 50 ? 'bg-warning' : 'bg-negative'}
          `}
                    style={{ width: `${score}%` }}
                />
            </div>

            <div className="flex items-baseline gap-1">
                <span className={`text-4xl font-bold ${score >= 80 ? 'text-positive' : score >= 50 ? 'text-warning' : 'text-negative'}`}>
                    {score}
                </span>
                <span className="text-muted text-sm">/ 100</span>
            </div>

            <p className="text-xs text-muted mt-2">
                Based on capital structure, liquidity, and profitability metrics.
            </p>
        </div>
    );
}
