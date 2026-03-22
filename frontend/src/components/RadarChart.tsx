"use client";

import {
    ResponsiveContainer,
    RadarChart,
    Radar,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    Tooltip
} from "recharts";

interface RatioRadarChartProps {
    data: {
        profit_margin?: number | null;
        debt_ratio?: number | null;
        asset_growth?: number | null;
        rnd_intensity?: number | null;
        liquidity?: number | null;
    };
}

export default function RatioRadarChart({ data }: RatioRadarChartProps) {
    const chartData = [
        { subject: "Profit", A: Math.min(100, Math.max(0, (data.profit_margin || 0) * 2)), fullMark: 100 },
        { subject: "Safety", A: Math.min(100, Math.max(0, 100 - (data.debt_ratio || 0))), fullMark: 100 },
        { subject: "Growth", A: Math.min(100, Math.max(0, (data.asset_growth || 0) + 50)), fullMark: 100 },
        { subject: "R&D", A: Math.min(100, Math.max(0, (data.rnd_intensity || 0) * 5)), fullMark: 100 },
        { subject: "Liquidity", A: Math.min(100, Math.max(0, (data.liquidity || 1) * 20)), fullMark: 100 },
    ];

    return (
        <div className="glass-card p-6 h-full flex flex-col">
            <h3 className="section-header mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
                </svg>
                Financial Health Radar
            </h3>

            <div className="flex-1 w-full" style={{ height: "280px" }}>
                <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="65%" data={chartData}>
                        <PolarGrid stroke="var(--card-border)" />
                        <PolarAngleAxis
                            dataKey="subject"
                            tick={{ fill: "var(--muted)", fontSize: 11, fontWeight: 500 }}
                        />
                        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                        <Radar
                            name="Score"
                            dataKey="A"
                            stroke="var(--primary)"
                            fill="var(--primary)"
                            fillOpacity={0.4}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: "var(--card)",
                                borderColor: "var(--card-border)",
                                borderRadius: "var(--radius-sm)",
                                color: "var(--foreground)"
                            }}
                        />
                    </RadarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
