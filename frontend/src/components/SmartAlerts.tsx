"use client";

interface SmartAlertsProps {
    data: {
        revenue?: number | null;
        net_income?: number | null;
        profit_margin?: number | null;
        liabilities?: number | null;
        assets?: number | null;
        risk_score?: number | null;
    };
}

export default function SmartAlerts({ data }: SmartAlertsProps) {
    const alerts: { type: "warning" | "negative" | "info"; message: string }[] = [];

    // Logic 1: Revenue Up but Profit Margin Low (Efficiency Issue)
    // Assuming we had previous year data effectively, but here checking static thresholds
    if (data.profit_margin && data.profit_margin < 5) {
        alerts.push({
            type: "warning",
            message: "Profit margin is below 5%, indicating potential efficiency issues despite revenue generation."
        });
    }

    // Logic 2: High Debt Ratio
    if (data.liabilities && data.assets) {
        const debtRatio = (data.liabilities / data.assets) * 100;
        if (debtRatio > 70) {
            alerts.push({
                type: "negative",
                message: `High Debt-to-Asset ratio (${debtRatio.toFixed(1)}%). Company is highly leveraged.`
            });
        }
    }

    // Logic 3: High Risk Score
    if (data.risk_score && data.risk_score > 65) {
        alerts.push({
            type: "negative",
            message: "Composite Risk Score exceeds 65/100. Significant operational or market risks detected."
        });
    }

    // Logic 4: Net Income Negative
    if (data.net_income && data.net_income < 0) {
        alerts.push({
            type: "negative",
            message: "Company reported a net loss for the period."
        });
    }

    if (alerts.length === 0) return null;

    return (
        <div className="glass-card p-6 border-l-4 border-l-primary bg-gradient-to-r from-primary/5 to-transparent">
            <h3 className="section-header mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="icon animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                AI Smart Alerts
            </h3>

            <div className="space-y-3">
                {alerts.map((alert, idx) => (
                    <div
                        key={idx}
                        className={`flex gap-3 items-start p-3 rounded-lg text-sm
              ${alert.type === 'negative'
                                ? 'bg-red-50 text-red-800 dark:bg-red-900/20 dark:text-red-300'
                                : alert.type === 'warning'
                                    ? 'bg-amber-50 text-amber-800 dark:bg-amber-900/20 dark:text-amber-300'
                                    : 'bg-blue-50 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300'
                            }
            `}
                    >
                        <span className="mt-0.5 text-lg leading-none">
                            {alert.type === 'negative' ? '⚠️' : alert.type === 'warning' ? '⚡' : 'ℹ️'}
                        </span>
                        <span>{alert.message}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
