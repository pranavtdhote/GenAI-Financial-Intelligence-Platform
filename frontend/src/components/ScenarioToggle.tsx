"use client";

import { useState } from "react";

interface ScenarioToggleProps {
    currentRevenue: number;
}

export default function ScenarioToggle({ currentRevenue }: ScenarioToggleProps) {
    const [scenario, setScenario] = useState<"conservative" | "moderate" | "aggressive">("moderate");

    const rates = {
        conservative: 1.02, // 2% growth
        moderate: 1.05,     // 5% growth
        aggressive: 1.12,   // 12% growth
    };

    const projected = currentRevenue * rates[scenario];

    return (
        <div className="glass-card p-6">
            <h3 className="section-header mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                Scenario Analysis
            </h3>

            <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-lg mb-6">
                {(["conservative", "moderate", "aggressive"] as const).map((s) => (
                    <button
                        key={s}
                        onClick={() => setScenario(s)}
                        className={`flex-1 py-1.5 text-xs font-medium rounded-md capitalize transition-all
              ${scenario === s
                                ? "bg-white dark:bg-slate-600 shadow-sm text-foreground"
                                : "text-muted hover:text-foreground"
                            }
            `}
                    >
                        {s}
                    </button>
                ))}
            </div>

            <div className="text-center">
                <p className="text-xs text-muted font-medium uppercase mb-1">Projected Revenue (Next FY)</p>
                <p className="text-2xl font-bold text-primary animate-count-up">
                    ${(projected / 1e6).toFixed(1)}M
                </p>
                <p className="text-xs text-positive mt-1">
                    {((rates[scenario] - 1) * 100).toFixed(0)}% Growth
                </p>
            </div>
        </div>
    );
}
