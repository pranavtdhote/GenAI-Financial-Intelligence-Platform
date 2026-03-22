"use client";

interface KPICardsProps {
    data: {
        revenue?: number | null;
        net_income?: number | null;
        assets?: number | null;
        liabilities?: number | null;
        gross_margin?: number | null;
        profit_margin?: number | null;
        risk_score?: number | null;
        rnd_growth?: number | null;
    };
    currency?: string;
}

const CURRENCY_SYMBOLS: Record<string, string> = { USD: "$", INR: "₹", EUR: "€", GBP: "£" };

function formatCurrency(n: number, currency: string = "USD") {
    const sym = CURRENCY_SYMBOLS[currency] || "$";
    const abs = Math.abs(n);
    const sign = n < 0 ? "-" : "";

    if (currency === "INR") {
        if (abs >= 1e7) return `${sign}${sym}${(abs / 1e7).toFixed(2)} Cr`;
        if (abs >= 1e5) return `${sign}${sym}${(abs / 1e5).toFixed(2)} L`;
        return `${sign}${sym}${abs.toLocaleString("en-IN")}`;
    }

    if (abs >= 1e9) return `${sign}${sym}${(abs / 1e9).toFixed(2)}B`;
    if (abs >= 1e6) return `${sign}${sym}${(abs / 1e6).toFixed(2)}M`;
    if (abs >= 1e3) return `${sign}${sym}${(abs / 1e3).toFixed(2)}K`;
    return `${sign}${sym}${abs.toFixed(2)}`;
}

export default function KPICards({ data, currency = "USD" }: KPICardsProps) {
    const debtRatio = data.liabilities && data.assets ? (data.liabilities / data.assets) * 100 : null;

    const metrics = [
        {
            label: "Revenue",
            value: data.revenue,
            format: (n: number) => formatCurrency(n, currency),
            trend: "up",
            color: "text-foreground"
        },
        {
            label: "Net Income",
            value: data.net_income,
            format: (n: number) => formatCurrency(n, currency),
            trend: data.net_income && data.net_income > 0 ? "up" : "down",
            color: "text-foreground"
        },
        {
            label: "Profit Margin",
            value: data.profit_margin,
            format: (n: number) => `${n.toFixed(1)}%`,
            trend: data.profit_margin && data.profit_margin > 15 ? "up" : "neutral",
            color: "text-accent"
        },
        {
            label: "Debt Ratio",
            value: debtRatio,
            format: (n: number) => `${n.toFixed(1)}%`,
            trend: debtRatio && debtRatio > 50 ? "down" : "up",
            color: "text-warning",
            inverse: true
        },
        {
            label: "Total Assets",
            value: data.assets,
            format: (n: number) => formatCurrency(n, currency),
            trend: "up",
            color: "text-primary"
        },
        {
            label: "Risk Score",
            value: data.risk_score,
            format: (n: number) => `${n}/100`,
            trend: data.risk_score && data.risk_score > 50 ? "down" : "up",
            color: data.risk_score && data.risk_score > 50 ? "text-negative" : "text-positive",
            inverse: true
        }
    ];

    return (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {metrics.map((m, i) => (
                <div
                    key={m.label}
                    className={`kpi-card group cursor-default delay-${i + 1} animate-fade-in`}
                >
                    <div className="flex flex-col h-full justify-between">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-semibold uppercase tracking-wider text-muted-light">
                                {m.label}
                            </span>
                            {m.value != null && (
                                <span className={`
                  flex items-center justify-center w-5 h-5 rounded-full text-[10px]
                  ${(m.trend === "up" && !m.inverse) || (m.trend === "down" && m.inverse)
                                        ? "bg-positive/10 text-positive"
                                        : (m.trend === "down" && !m.inverse) || (m.trend === "up" && m.inverse)
                                            ? "bg-negative/10 text-negative"
                                            : "bg-slate-100 dark:bg-slate-800 text-slate-500"
                                    }
                `}>
                                    {m.trend === "up" ? "↑" : m.trend === "down" ? "↓" : "−"}
                                </span>
                            )}
                        </div>

                        <div className="mt-1">
                            <span className={`text-xl font-bold tracking-tight ${m.color}`}>
                                {m.value != null ? m.format(m.value) : "—"}
                            </span>
                        </div>

                        <div className="mt-2 h-1 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                            <div
                                className={`h-full rounded-full opacity-50 ${m.trend === "up" ? "bg-positive" : "bg-primary"}`}
                                style={{ width: `${Math.min(90, Math.max(15, (m.value || 0) > 0 ? 65 : 25))}%` }}
                            />
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}
