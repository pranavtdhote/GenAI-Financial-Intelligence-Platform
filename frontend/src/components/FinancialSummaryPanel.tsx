"use client";

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

interface FinancialSummaryPanelProps {
    financialData: {
        revenue?: number | null;
        net_income?: number | null;
        assets?: number | null;
        liabilities?: number | null;
        gross_margin?: number | null;
        profit_margin?: number | null;
        risk_score?: number | null;
    } | null;
    currency?: string;
    companyName?: string | null;
    reportYear?: string;
}

export default function FinancialSummaryPanel({ financialData, currency = "USD", companyName, reportYear }: FinancialSummaryPanelProps) {
    if (!financialData) {
        return (
            <div className="glass-card p-6 flex items-center justify-center text-muted text-center" style={{ minHeight: "300px" }}>
                <div>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 mx-auto mb-2 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p className="text-sm">Financial data will appear after analysis</p>
                </div>
            </div>
        );
    }

    const metrics = [
        { label: "Revenue", value: financialData.revenue, isCurrency: true, icon: "💰" },
        { label: "Net Income", value: financialData.net_income, isCurrency: true, icon: "📊" },
        { label: "Total Assets", value: financialData.assets, isCurrency: true, icon: "🏦" },
        { label: "Liabilities", value: financialData.liabilities, isCurrency: true, icon: "📉" },
        { label: "Profit Margin", value: financialData.profit_margin, isCurrency: false, icon: "📈", suffix: "%" },
        { label: "Risk Score", value: financialData.risk_score, isCurrency: false, icon: "⚠️", suffix: "/100" },
    ];

    const debtRatio = financialData.liabilities && financialData.assets
        ? ((financialData.liabilities / financialData.assets) * 100).toFixed(1)
        : null;

    return (
        <div className="glass-card p-6 h-full">
            <h3 className="section-header mb-1">
                <svg xmlns="http://www.w3.org/2000/svg" className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                Financial Summary
            </h3>
            {companyName && (
                <p className="text-xs text-muted mb-4">{companyName} {reportYear ? `• ${reportYear}` : ""}</p>
            )}

            <div className="space-y-3">
                {metrics.map((m) => (
                    <div key={m.label} className="flex items-center justify-between py-2 border-b border-card-border last:border-0">
                        <div className="flex items-center gap-2">
                            <span className="text-base">{m.icon}</span>
                            <span className="text-sm font-medium text-muted">{m.label}</span>
                        </div>
                        <span className="text-sm font-bold text-foreground">
                            {m.value != null
                                ? m.isCurrency
                                    ? formatCurrency(m.value, currency)
                                    : `${m.value.toFixed(1)}${m.suffix || ""}`
                                : "—"
                            }
                        </span>
                    </div>
                ))}

                {/* Derived metric: Debt Ratio */}
                {debtRatio && (
                    <div className="flex items-center justify-between py-2">
                        <div className="flex items-center gap-2">
                            <span className="text-base">🔄</span>
                            <span className="text-sm font-medium text-muted">Debt-to-Asset Ratio</span>
                        </div>
                        <span className={`text-sm font-bold ${parseFloat(debtRatio) > 50 ? "text-negative" : "text-positive"}`}>
                            {debtRatio}%
                        </span>
                    </div>
                )}
            </div>
        </div>
    );
}
