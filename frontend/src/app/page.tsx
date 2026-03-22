"use client";

import { useCallback, useState, useEffect } from "react";
import dynamic from "next/dynamic";

// Components
import UploadZone from "@/components/UploadZone";
import KPICards from "@/components/KPICards";
import AIInsights from "@/components/AIInsights";
import RiskHeatmap from "@/components/RiskHeatmap";
import YearCharts from "@/components/YearCharts";
import RadarChart from "@/components/RadarChart";
import CrossYearComparison from "@/components/CrossYearComparison";
import SmartAlerts from "@/components/SmartAlerts";
import AITransparencyPanel from "@/components/AITransparencyPanel";
import StabilityScore from "@/components/StabilityScore";
import ScenarioToggle from "@/components/ScenarioToggle";
import PredictiveTrend from "@/components/PredictiveTrend";
import ConfidenceScore from "@/components/ConfidenceScore";
import DownloadReport from "@/components/DownloadReport";
import FinancialSummaryPanel from "@/components/FinancialSummaryPanel";

const KnowledgeGraphView = dynamic(() => import("@/components/KnowledgeGraphView"), { ssr: false });

import {
  uploadAndProcessPdf,
  analyzeFinancial,
  getGenAIAnalysis,
  compareTrends,
  buildKnowledgeGraph,
  indexReport,
} from "@/lib/api";

// Currency conversion rates (USD base)
const EXCHANGE_RATES: Record<string, number> = { USD: 1.0, INR: 83.0, EUR: 0.92, GBP: 0.79 };
const CURRENCY_SYMBOLS: Record<string, string> = { USD: "$", INR: "₹", EUR: "€", GBP: "£" };

function convertCurrency(amount: number, from: string, to: string): number {
  if (from === to) return amount;
  const fromRate = EXCHANGE_RATES[from] || 1;
  const toRate = EXCHANGE_RATES[to] || 1;
  return amount * (toRate / fromRate);
}

// Interfaces
interface DocumentData {
  company_name?: string | null;
  report_year?: string | null;
  raw_text: string;
  extracted_tables: unknown[];
}

interface FinancialData {
  revenue?: number | null;
  net_income?: number | null;
  assets?: number | null;
  liabilities?: number | null;
  gross_margin?: number | null;
  profit_margin?: number | null;
  risks?: string[];
  risk_score?: number | null;
  detected_currency?: string;
}

interface LLMData {
  executive_summary?: string | null;
  financial_performance_overview?: string | null;
  risk_analysis?: string | null;
  trend_detection?: string | null;
  investment_recommendation?: string | null;
  red_flags?: string[];
  confidence_score?: number | null;
  investor_slides?: { title: string; bullets: string[] }[];
  compliance?: {
    ifrs_mentioned?: boolean;
    gaap_mentioned?: boolean;
    esg_mentioned?: boolean;
    standard_notes?: string;
  };
}

interface TrendData {
  visual_data?: {
    labels?: string[];
    series?: {
      revenue?: (number | null)[];
      net_income?: (number | null)[];
      operating_expenses?: (number | null)[];
      profit_margin?: (number | null)[];
    }
  };
  growth_analysis?: { year_over_year?: unknown[] };
}

interface GraphData {
  nodes: { id: string; type: string; label: string }[];
  edges: { source: string; target: string; type: string }[];
}

export default function Dashboard() {
  const [documentData, setDocumentData] = useState<DocumentData | null>(null);
  const [financialData, setFinancialData] = useState<FinancialData | null>(null);
  const [llmData, setLlmData] = useState<LLMData | null>(null);
  const [trendData, setTrendData] = useState<TrendData | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Theme State
  const [darkMode, setDarkMode] = useState(false);

  // Currency State
  const [currency, setCurrency] = useState("USD");
  const [baseCurrency, setBaseCurrency] = useState("USD");

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const isDark = document.documentElement.classList.contains('dark');
      setDarkMode(isDark);
    }
  }, []);

  const toggleTheme = () => {
    if (darkMode) {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
      setDarkMode(false);
    } else {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
      setDarkMode(true);
    }
  };

  const processPdf = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      const doc = await uploadAndProcessPdf(file);
      setDocumentData(doc);

      const fin = await analyzeFinancial({
        raw_text: doc.raw_text,
        extracted_tables: doc.extracted_tables || [],
      });
      setFinancialData(fin);

      // Set detected base currency
      const detected = fin.detected_currency || "USD";
      setBaseCurrency(detected);
      setCurrency(detected);

      // Parallelize independent calls
      const [llm, graph] = await Promise.all([
        getGenAIAnalysis({
          raw_text: doc.raw_text,
          financial_data: fin,
          company_name: doc.company_name,
        }),
        buildKnowledgeGraph({
          llm_output: {},
          company_name: doc.company_name,
          financial_data: fin,
        })
      ]);

      setLlmData(llm);
      setGraphData(graph);

      // Trend Analysis
      if (fin.revenue || fin.assets) {
        const records = [
          { year: parseInt(doc.report_year || "0") || new Date().getFullYear(), ...fin },
        ];
        const trend = await compareTrends(records);
        setTrendData(trend);
      }

      // Indexing (Fire and forget)
      indexReport({
        report_id: `report-${Date.now()}`,
        raw_text: doc.raw_text,
        company_name: doc.company_name,
        report_year: doc.report_year,
      }).catch(() => { });

    } catch (e) {
      const msg = e instanceof Error ? e.message : "Processing failed";
      setError(
        msg.includes("fetch") || msg.includes("Failed")
          ? "Backend unavailable. Ensure the backend is running on port 8000."
          : msg
      );
    } finally {
      setLoading(false);
    }
  }, []);

  // Currency conversion helper
  const cv = (val: number | null | undefined): number | null | undefined => {
    if (val == null) return val;
    return convertCurrency(val, baseCurrency, currency);
  };

  // Prepare data for components
  const kpiData = financialData ? {
    revenue: cv(financialData.revenue),
    net_income: cv(financialData.net_income),
    assets: cv(financialData.assets),
    liabilities: cv(financialData.liabilities),
    gross_margin: financialData.gross_margin,
    profit_margin: financialData.profit_margin,
    risk_score: financialData.risk_score,
    rnd_growth: null
  } : {};

  const radarData = financialData ? {
    profit_margin: financialData.profit_margin,
    debt_ratio: financialData.liabilities && financialData.assets ? (financialData.liabilities / financialData.assets) * 100 : 0,
    asset_growth: 5,
    rnd_intensity: 15,
    liquidity: 1.5,
  } : {};

  const processingStats = {
    extracted_source_count: documentData ? Math.floor(documentData.raw_text.length / 100) : 0,
    validation_status: (llmData?.confidence_score || 0) > 0.7 ? "verified" : "check_needed",
    llm_model: "Groq Llama-3 70B",
    processing_time: "~4.2s"
  } as const;

  // Prepare Cross Year Data 
  const currentYear = documentData?.report_year || new Date().getFullYear().toString();
  const crossYearCurrent = financialData && financialData.revenue ? {
    year: currentYear,
    revenue: cv(financialData.revenue) || 0,
    net_income: cv(financialData.net_income) || 0,
    profit_margin: financialData.profit_margin || 0,
  } : null;

  const crossYearPrevious = trendData?.visual_data?.labels?.length && trendData.visual_data.labels.length > 1
    ? {
      year: trendData.visual_data.labels[trendData.visual_data.labels.length - 2],
      revenue: cv(trendData.visual_data.series?.revenue?.[trendData.visual_data.labels.length - 2]) || 0,
      net_income: cv(trendData.visual_data.series?.net_income?.[trendData.visual_data.labels.length - 2]) || 0,
      profit_margin: trendData.visual_data.series?.profit_margin?.[trendData.visual_data.labels.length - 2] || 0,
    }
    : undefined;

  const revenueHistory = trendData?.visual_data?.series?.revenue?.filter((v): v is number => v !== null) || [];
  const historyYears = trendData?.visual_data?.labels || [];

  return (
    <div className="min-h-screen transition-colors duration-300">
      {/* ── Header ────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-card-border bg-white/80 dark:bg-slate-900/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent shadow-lg shadow-primary/20">
              <span className="text-xl font-bold text-white">G</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-foreground leading-none">GenAI Financial</h1>
              <p className="text-xs text-muted">Intelligence Platform</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Currency Switcher */}
            <select
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className="h-10 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 text-sm font-medium text-foreground focus:outline-none focus:ring-2 focus:ring-primary/30 transition-colors cursor-pointer"
              title="Select display currency"
            >
              {Object.entries(CURRENCY_SYMBOLS).map(([code, sym]) => (
                <option key={code} value={code}>{sym} {code}</option>
              ))}
            </select>

            {documentData && <DownloadReport documentData={documentData} financialData={financialData || undefined} llmData={llmData || undefined} />}
            <button
              onClick={toggleTheme}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {darkMode ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* ── Main Content ──────────────────────────────────────── */}
      <main className="mx-auto max-w-[1600px] px-6 py-8 space-y-8">
        {/* Upload Section */}
        <section className="animate-fade-in">
          <UploadZone onProcess={processPdf} isProcessing={loading} />
        </section>

        {/* Error Banner */}
        {error && (
          <div className="animate-slide-up rounded-xl border border-red-200 bg-red-50 p-4 text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-400 flex items-center gap-3">
            <span className="font-medium">Error: {error}</span>
          </div>
        )}

        {/* ── Dashboard Content ─────────────────────────────── */}
        {documentData && (
          <div className="space-y-8 animate-slide-up">

            {/* Row 1: KPI Cards */}
            {financialData && <KPICards data={kpiData} currency={currency} />}

            {/* Row 2: Stability + Confidence + Scenario (3-col) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="delay-1 animate-fade-in">
                <StabilityScore score={financialData?.risk_score ? Math.max(0, 100 - financialData.risk_score) : 75} />
              </div>
              <div className="delay-2 animate-fade-in glass-card p-4 flex items-center justify-center">
                {llmData?.confidence_score != null
                  ? <ConfidenceScore score={llmData.confidence_score} />
                  : <div className="text-muted text-sm text-center p-6">AI Confidence Score will appear here</div>
                }
              </div>
              <div className="delay-3 animate-fade-in">
                <ScenarioToggle currentRevenue={cv(financialData?.revenue) || 0} />
              </div>
            </div>

            {/* Row 3: AI Insights + Smart Alerts (full width) */}
            {llmData && <AIInsights data={llmData} confidenceScore={llmData.confidence_score} />}
            {financialData && <SmartAlerts data={financialData} />}

            {/* Row 4: Revenue & Income Chart + Margins Chart (2-col) */}
            <YearCharts visualData={trendData?.visual_data} currency={currency} />

            {/* Row 5: Predictive Trend + Risk Heatmap + Radar (3-col) */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              <div className="animate-fade-in">
                {revenueHistory.length >= 2
                  ? <PredictiveTrend history={revenueHistory} years={historyYears} />
                  : (
                    <div className="glass-card p-6 flex flex-col items-center justify-center text-center" style={{ minHeight: "180px" }}>
                      <h3 className="section-header mb-2">
                        <svg xmlns="http://www.w3.org/2000/svg" className="icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                        </svg>
                        AI Trend Forecast
                      </h3>
                      <p className="text-sm text-muted">Upload 2+ years of data to enable predictive trend analysis</p>
                    </div>
                  )
                }
              </div>
              <div className="animate-fade-in">
                {financialData && (
                  <div className="glass-card p-6" style={{ minHeight: "180px" }}>
                    <RiskHeatmap risks={financialData.risks || []} riskScore={financialData.risk_score} />
                  </div>
                )}
              </div>
              <div className="animate-fade-in" style={{ height: "380px" }}>
                <RadarChart data={radarData} />
              </div>
            </div>

            {/* Row 6: Knowledge Graph + Financial Summary (2-col) */}
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
              <div className="xl:col-span-2" style={{ height: "550px" }}>
                {graphData && graphData.nodes?.length > 0
                  ? <KnowledgeGraphView graphData={graphData} />
                  : (
                    <div className="glass-card p-6 h-full flex items-center justify-center text-muted text-center">
                      <div>
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                        </svg>
                        <p className="text-sm">Knowledge Graph will appear here after analysis</p>
                      </div>
                    </div>
                  )
                }
              </div>
              <div className="animate-fade-in">
                {crossYearCurrent && crossYearPrevious ? (
                  <CrossYearComparison
                    currentYearData={crossYearCurrent}
                    previousYearData={crossYearPrevious}
                  />
                ) : (
                  <FinancialSummaryPanel
                    financialData={financialData}
                    currency={currency}
                    companyName={documentData.company_name}
                    reportYear={currentYear}
                  />
                )}
              </div>
            </div>

            {/* Row 7: AI Transparency */}
            <AITransparencyPanel data={processingStats} />
          </div>
        )}
      </main>
    </div>
  );
}
