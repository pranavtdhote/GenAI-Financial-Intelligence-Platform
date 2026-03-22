"use client";

import { useState } from "react";

interface CrossYearComparisonProps {
    currentYearData: {
        year: string;
        revenue: number;
        net_income: number;
        profit_margin: number;
    };
    previousYearData?: {
        year: string;
        revenue: number;
        net_income: number;
        profit_margin: number;
    };
}

export default function CrossYearComparison({ currentYearData, previousYearData }: CrossYearComparisonProps) {
    if (!previousYearData) return null;

    const calculateGrowth = (current: number, previous: number) => {
        if (!previous) return 0;
        return ((current - previous) / previous) * 100;
    };

    const metrics = [
        {
            label: "Revenue",
            current: currentYearData.revenue,
            previous: previousYearData.revenue,
            format: (val: number) => `$${(val / 1e6).toFixed(1)}M`,
        },
        {
            label: "Net Income",
            current: currentYearData.net_income,
            previous: previousYearData.net_income,
            format: (val: number) => `$${(val / 1e6).toFixed(1)}M`,
        },
        {
            label: "Profit Margin",
            current: currentYearData.profit_margin,
            previous: previousYearData.profit_margin,
            format: (val: number) => `${val.toFixed(1)}%`,
        },
    ];

    return (
        <div className="glass-card p-6">
            <h3 className="section-header mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
                </svg>
                Year-over-Year Growth
            </h3>

            <div className="overflow-x-auto">
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-card-border text-left">
                            <th className="py-2 text-muted font-medium">Metric</th>
                            <th className="py-2 text-right text-muted font-medium">{previousYearData.year}</th>
                            <th className="py-2 text-right text-muted font-medium">{currentYearData.year}</th>
                            <th className="py-2 text-right text-muted font-medium">Growth</th>
                        </tr>
                    </thead>
                    <tbody>
                        {metrics.map((m) => {
                            const growth = calculateGrowth(m.current, m.previous);
                            const isPositive = growth > 0;

                            return (
                                <tr key={m.label} className="border-b border-card-border last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                    <td className="py-3 font-medium text-foreground">{m.label}</td>
                                    <td className="py-3 text-right text-muted-foreground">{m.format(m.previous)}</td>
                                    <td className="py-3 text-right text-foreground font-semibold">{m.format(m.current)}</td>
                                    <td className="py-3 text-right">
                                        <span
                                            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold
                        ${isPositive
                                                    ? "bg-positive/10 text-positive"
                                                    : "bg-negative/10 text-negative"
                                                }
                      `}
                                        >
                                            {isPositive ? "↑" : "↓"} {Math.abs(growth).toFixed(1)}%
                                        </span>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
