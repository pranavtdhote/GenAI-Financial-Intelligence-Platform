function getApiBase(): string {
  if (typeof window !== "undefined") {
    // Use relative URL - Next.js rewrites /api/v1/* to backend (no CORS, works for localhost + LAN)
    return "/api/v1";
  }
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
}

const API_BASE = getApiBase();

async function parseErrorResponse(res: Response): Promise<string> {
  if (res.status === 502 || res.status === 504) {
    return "Backend unavailable. Ensure the backend is running on port 8000.";
  }
  const text = await res.text();
  try {
    const json = JSON.parse(text) as {
      detail?: string | { msg?: string }[] | { message?: string; inconsistencies?: string[] };
    };
    if (typeof json.detail === "string") return json.detail;
    if (Array.isArray(json.detail) && json.detail[0]?.msg) return json.detail[0].msg;
    if (json.detail && typeof json.detail === "object" && "message" in json.detail) {
      const d = json.detail as { message?: string; inconsistencies?: string[] };
      return d.inconsistencies?.length
        ? `${d.message} ${d.inconsistencies.slice(0, 5).join("; ")}`
        : (d.message ?? "Validation error");
    }
  } catch {
    /* ignore */
  }
  return text || `Request failed (${res.status})`;
}

export async function uploadAndProcessPdf(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/documents/process`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await parseErrorResponse(res));
  return res.json();
}

export async function analyzeFinancial(data: { raw_text: string; extracted_tables: unknown[] }) {
  const res = await fetch(`${API_BASE}/financial/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await parseErrorResponse(res));
  return res.json();
}

export async function getGenAIAnalysis(data: {
  raw_text: string;
  financial_data: Record<string, unknown>;
  company_name?: string;
}) {
  const res = await fetch(`${API_BASE}/llm/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await parseErrorResponse(res));
  return res.json();
}

export async function compareTrends(financial_records: Record<string, unknown>[]) {
  const res = await fetch(`${API_BASE}/trends/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ financial_records }),
  });
  if (!res.ok) throw new Error(await parseErrorResponse(res));
  return res.json();
}

export async function buildKnowledgeGraph(data: {
  llm_output: Record<string, unknown>;
  company_name?: string;
  financial_data?: Record<string, unknown>;
}) {
  const res = await fetch(`${API_BASE}/knowledge-graph/build`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await parseErrorResponse(res));
  return res.json();
}

export async function indexReport(data: {
  report_id: string;
  raw_text: string;
  company_name?: string;
  report_year?: string;
}) {
  const res = await fetch(`${API_BASE}/vector/index`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(await parseErrorResponse(res));
  return res.json();
}
