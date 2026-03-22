"use client";

import {
  AreaChart,
  Area,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Line
} from "recharts";

interface YearChartsProps {
  visualData?: {
    labels?: string[];
    series?: {
      revenue?: (number | null)[];
      net_income?: (number | null)[];
      operating_expenses?: (number | null)[];
      profit_margin?: (number | null)[];
    };
  };
  currency?: string;
}

const CURRENCY_SYMBOLS: Record<string, string> = { USD: "$", INR: "₹", EUR: "€", GBP: "£" };

function makeCurrencyFormatter(currency: string = "USD") {
  const sym = CURRENCY_SYMBOLS[currency] || "$";
  return (val: number) => {
    const abs = Math.abs(val);
    const sign = val < 0 ? "-" : "";
    if (currency === "INR") {
      if (abs >= 1e7) return `${sign}${sym}${(abs / 1e7).toFixed(1)} Cr`;
      if (abs >= 1e5) return `${sign}${sym}${(abs / 1e5).toFixed(1)} L`;
      return `${sign}${sym}${abs.toFixed(0)}`;
    }
    if (abs >= 1e9) return `${sign}${sym}${(abs / 1e9).toFixed(1)}B`;
    if (abs >= 1e6) return `${sign}${sym}${(abs / 1e6).toFixed(1)}M`;
    if (abs >= 1e3) return `${sign}${sym}${(abs / 1e3).toFixed(1)}K`;
    return `${sign}${sym}${abs.toFixed(0)}`;
  };
}

export default function YearCharts({ visualData, currency = "USD" }: YearChartsProps) {
  const formatCurrency = makeCurrencyFormatter(currency);

  if (!visualData?.labels || !visualData.series) {
    return (
      <div className="glass-card p-8 flex items-center justify-center text-muted" style={{ height: "350px" }}>
        <div className="text-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 mx-auto mb-2 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
          <p className="text-sm">No trend data available for visualization</p>
          <p className="text-xs mt-1">Upload a financial report to see charts</p>
        </div>
      </div>
    );
  }

  const chartData = visualData.labels.map((year, index) => ({
    year,
    revenue: visualData.series?.revenue?.[index] || 0,
    net_income: visualData.series?.net_income?.[index] || 0,
    expenses: visualData.series?.operating_expenses?.[index] || 0,
    margin: visualData.series?.profit_margin?.[index] || 0,
  }));

  const startRev = chartData[0]?.revenue || 0;
  const endRev = chartData[chartData.length - 1]?.revenue || 0;
  const years = chartData.length - 1;
  const cagr = startRev > 0 && years > 0
    ? ((Math.pow(endRev / startRev, 1 / years) - 1) * 100).toFixed(1)
    : null;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
      {/* ── Revenue & Income Chart ────────────────────────── */}
      <div className="glass-card p-6">
        <div className="flex justify-between items-start mb-4">
          <h3 className="section-header">
            <svg xmlns="http://www.w3.org/2000/svg" className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            Revenue &amp; Income
          </h3>
          {cagr && <span className="badge badge-info">CAGR: {cagr}%</span>}
        </div>

        <div style={{ width: "100%", height: "320px" }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
              <defs>
                <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="var(--primary)" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="colorNet" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--positive)" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="var(--positive)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--card-border)" />
              <XAxis dataKey="year" axisLine={false} tickLine={false} tick={{ fill: "var(--muted)", fontSize: 12 }} />
              <YAxis tickFormatter={formatCurrency} axisLine={false} tickLine={false} width={75} tick={{ fill: "var(--muted)", fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: "var(--card)", borderColor: "var(--card-border)", color: "var(--foreground)", borderRadius: "var(--radius-sm)" }}
                formatter={(val: number) => [formatCurrency(val), ""]}
                labelStyle={{ fontWeight: 600, marginBottom: 4 }}
              />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ color: "var(--foreground)" }} />
              <Area type="monotone" dataKey="revenue" name="Revenue" stroke="var(--primary)" fillOpacity={1} fill="url(#colorRev)" strokeWidth={3} dot={{ r: 3, fill: "var(--primary)" }} />
              <Area type="monotone" dataKey="net_income" name="Net Income" stroke="var(--positive)" fillOpacity={1} fill="url(#colorNet)" strokeWidth={3} dot={{ r: 3, fill: "var(--positive)" }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* ── Margins vs OpEx Chart ─────────────────────────── */}
      <div className="glass-card p-6">
        <h3 className="section-header mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Margins vs Opex
        </h3>

        <div style={{ width: "100%", height: "320px" }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--card-border)" />
              <XAxis dataKey="year" axisLine={false} tickLine={false} tick={{ fill: "var(--muted)", fontSize: 12 }} />
              <YAxis yAxisId="left" tickFormatter={formatCurrency} axisLine={false} tickLine={false} width={75} tick={{ fill: "var(--muted)", fontSize: 11 }} />
              <YAxis yAxisId="right" orientation="right" tickFormatter={(val) => `${val}%`} axisLine={false} tickLine={false} width={50} tick={{ fill: "var(--muted)", fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: "var(--card)", borderColor: "var(--card-border)", color: "var(--foreground)", borderRadius: "var(--radius-sm)" }}
                labelStyle={{ fontWeight: 600, marginBottom: 4 }}
              />
              <Legend verticalAlign="top" height={36} />
              <Bar yAxisId="left" dataKey="expenses" name="Op. Expenses" fill="var(--warning)" radius={[4, 4, 0, 0]} barSize={40} fillOpacity={0.8} />
              <Line yAxisId="right" type="monotone" dataKey="margin" name="Profit Margin %" stroke="var(--accent)" strokeWidth={3} dot={{ r: 4, fill: "var(--accent)", strokeWidth: 2, stroke: "#fff" }} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
