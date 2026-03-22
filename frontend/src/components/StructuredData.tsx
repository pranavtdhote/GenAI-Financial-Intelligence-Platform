"use client";

interface StructuredDataProps {
  data: {
    revenue?: number | null;
    net_income?: number | null;
    assets?: number | null;
    liabilities?: number | null;
    gross_margin?: number | null;
    profit_margin?: number | null;
  };
  companyName?: string | null;
  reportYear?: string | null;
}

function formatCurrency(n: number) {
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e3) return `$${(n / 1e3).toFixed(2)}K`;
  return `$${n.toFixed(2)}`;
}

export default function StructuredData({ data, companyName, reportYear }: StructuredDataProps) {
  const metrics = [
    { label: "Revenue", value: data.revenue, format: formatCurrency },
    { label: "Net Income", value: data.net_income, format: formatCurrency },
    { label: "Assets", value: data.assets, format: formatCurrency },
    { label: "Liabilities", value: data.liabilities, format: formatCurrency },
    { label: "Gross Margin", value: data.gross_margin, format: (n: number) => `${n}%` },
    { label: "Profit Margin", value: data.profit_margin, format: (n: number) => `${n}%` },
  ];

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
      <h3 className="mb-4 text-lg font-semibold text-slate-800 dark:text-slate-100">Structured Financial Data</h3>
      {(companyName || reportYear) && (
        <p className="mb-4 text-sm text-slate-600 dark:text-slate-400">
          {companyName} {reportYear && `• FY ${reportYear}`}
        </p>
      )}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        {metrics.map((m) => (
          <div key={m.label} className="rounded-lg bg-slate-50 p-4 dark:bg-slate-700/50">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
              {m.label}
            </p>
            <p className="mt-1 text-lg font-semibold text-slate-800 dark:text-slate-100">
              {m.value != null ? m.format(m.value) : "—"}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
