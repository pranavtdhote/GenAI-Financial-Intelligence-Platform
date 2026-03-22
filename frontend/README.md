# Financial Report Analysis Dashboard

Modern Next.js dashboard for AI-driven financial report analysis. Investor-focused, professional design.

## Features

- **Upload PDF** – Drag-and-drop or click to upload financial reports
- **Structured Data** – Extracted revenue, net income, assets, margins
- **AI Insights** – Executive summary, risk analysis, investment recommendation
- **Risk Heatmap** – Visual risk factor severity
- **Year Comparison Charts** – Revenue, net income, growth (Recharts)
- **Knowledge Graph** – Entity relationships visualization (react-force-graph-2d)
- **Download Report (PDF)** – Export analysis as PDF
- **Confidence Score** – Indicator for AI output reliability

## Tech Stack

- **Next.js** (App Router)
- **Tailwind CSS**
- **Recharts** – Year comparison charts
- **react-force-graph-2d** – Knowledge graph visualization
- **jspdf** – PDF export

## Setup

```bash
npm install
cp .env.local.example .env.local
# Edit .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

Ensure the FastAPI backend is running at `http://localhost:8000`.

## Run

```bash
npm run dev
```

Open http://localhost:3000.

## API Integration

The dashboard calls these backend endpoints:

- `POST /api/v1/documents/process` – Upload & process PDF
- `POST /api/v1/financial/analyze` – Extract financial metrics
- `POST /api/v1/llm/analyze` – GenAI insights
- `POST /api/v1/knowledge-graph/build` – Build knowledge graph
- `POST /api/v1/trends/compare` – Year comparison (single-year for now)
- `POST /api/v1/vector/index` – Index report for semantic search
