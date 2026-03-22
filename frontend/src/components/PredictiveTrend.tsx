"use client";

interface PredictiveTrendProps {
    history: number[]; // Revenue history
    years: string[];
}

export default function PredictiveTrend({ history, years }: PredictiveTrendProps) {
    if (!history || history.length < 2) return null;

    // Simple Linear Regression
    const n = history.length;
    const x = Array.from({ length: n }, (_, i) => i); // 0, 1, 2...
    const y = history;

    const sumX = x.reduce((a, b) => a + b, 0);
    const sumY = y.reduce((a, b) => a + b, 0);
    const sumXY = x.reduce((acc, curr, i) => acc + curr * y[i], 0);
    const sumXX = x.reduce((acc, curr) => acc + curr * curr, 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    const nextYearIndex = n;
    const prediction = slope * nextYearIndex + intercept;
    const growthPct = ((prediction - history[n - 1]) / history[n - 1]) * 100;

    return (
        <div className="glass-card p-6 border-t-4 border-t-primary">
            <h3 className="section-header mb-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                AI Trend Forecast
            </h3>
            <p className="text-xs text-muted mb-4">Linear regression projection based on {n} years of data.</p>

            <div className="flex items-end gap-3">
                <div>
                    <span className="text-2xl font-bold text-foreground">
                        ${(prediction / 1e6).toFixed(1)}M
                    </span>
                    <p className="text-xs font-medium text-muted uppercase tracking-wider">Projected Next Year</p>
                </div>

                <div className={`mb-1 px-2 py-0.5 rounded text-xs font-bold ${growthPct >= 0 ? 'bg-positive/10 text-positive' : 'bg-negative/10 text-negative'}`}>
                    {growthPct >= 0 ? '+' : ''}{growthPct.toFixed(1)}%
                </div>
            </div>
        </div>
    );
}
