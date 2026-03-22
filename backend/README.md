# Financial Report Analysis Platform

AI-driven financial report analysis for investors.

## Project Structure

- **backend/** – FastAPI REST API (document processing, financial parsing, LLM, vector DB, etc.)
- **frontend/** – Next.js dashboard (Tailwind, Recharts, knowledge graph visualization)

## Quick Start

1. **Backend**: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`
2. **Frontend**: `cd frontend && npm install && npm run dev`
3. Open http://localhost:3000 and upload a financial PDF.

---

# Backend

Production-ready FastAPI backend for a Generative AI–Driven Financial Report Analysis Platform.

## Features

- **Modular architecture** - Clean separation of concerns (routers, services, models)
- **Environment-based configuration** - `.env` support via pydantic-settings
- **Secure file upload** - PDF validation, size limits, secure filenames, path traversal protection
- **Structured logging** - Request/response and application logs
- **Error handling** - Global exception handler and validation error handler
- **CORS enabled** - Configurable for frontend integration
- **Scalable design** - Ready for LLM and OCR integration (FileService, metadata models)

## Quick Start

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or: `python -m app.main`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| POST | `/api/v1/files/upload` | Upload financial PDF |
| POST | `/api/v1/documents/process` | Upload & process PDF (text, tables, metadata) |
| POST | `/api/v1/documents/process/{stored_filename}` | Process previously uploaded PDF |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |

## Project Structure

```
backend/
├── app/
│   ├── main.py          # FastAPI app factory
│   ├── config.py        # Environment config
│   ├── routers/         # API routes
│   ├── services/        # Business logic (file upload, future: LLM/OCR)
│   ├── models/          # Pydantic schemas
│   ├── core/            # Logging, dependencies, security
│   └── middleware/      # Error handler, request logging
├── uploads/             # Stored PDF files
├── requirements.txt
└── .env
```

## Configuration

Configure via `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| APP_NAME | Financial Report Analysis API | Application name |
| DEBUG | false | Enable debug logging |
| HOST | 0.0.0.0 | Server host |
| PORT | 8000 | Server port |
| UPLOAD_DIR | uploads | Upload directory |
| MAX_UPLOAD_SIZE_MB | 50 | Max file size (MB) |
| ALLOWED_EXTENSIONS | .pdf | Comma-separated extensions |
| CORS_ORIGINS | ["*"] | JSON array (e.g., `["https://app.com"]`) |

## Financial Structuring Engine

The `/api/v1/financial/analyze` endpoint parses raw text and tables to extract:

- **Metrics**: revenue, net_income, expenses, assets, liabilities
- **Ratios**: gross_margin, profit_margin (computed)
- **Sections**: Risk Factors, MD&A, Financial Statements
- **Risks**: Extracted risk factor items
- **Growth indicators**: YoY %, change mentions
- **Validation**: Sanity checks on extracted numbers

**Request** (POST with JSON body):
```json
{
  "raw_text": "extracted text from document...",
  "extracted_tables": [[["Header1","Header2"],["Row1","Row2"]]]
}
```

**Response**:
```json
{
  "revenue": 100000000,
  "net_income": 15000000,
  "gross_margin": 45.5,
  "profit_margin": 15.0,
  "liabilities": 200000000,
  "assets": 500000000,
  "risks": ["Risk factor 1...", "Risk factor 2..."],
  "growth_indicators": [{"type": "yoy_growth", "value": "10", "unit": "%"}],
  "validation": {"valid": true, "warnings": [], "errors": []}
}
```

**Technologies**: Regex extraction, spaCy NER (MONEY entities), monetary value normalization.

**spaCy (optional)**: `pip install spacy && python -m spacy download en_core_web_sm` for NER.

## GenAI Intelligence Layer (Groq API)

The `/api/v1/llm/analyze` endpoint generates AI-powered financial analysis using **Groq API** with Grok-style intelligence.

**Grok-Style Analysis Features:**
- Sharp, intelligent, slightly bold insights
- Analytical and concise financial intelligence
- Free inference using LLaMA 3.3 70B Versatile model
- Fast response times with Groq's infrastructure

**Outputs:**
- Executive Summary
- Financial Performance Overview
- Risk Analysis
- Trend Detection
- Investment Recommendation (Buy/Hold/Sell)
- Red Flags
- Confidence Score (0–1)
- Investor Slides (5-slide deck)
- Compliance Indicators (IFRS, GAAP, ESG)

**Features:**
- Temperature 0.2 for reliable, deterministic output
- Hallucination guard: compares LLM numbers with extracted data; flags mismatches
- Structured JSON output with Markdown formatting
- Numerical validation instructions in prompt
- Automatic fallback on API errors

**Request** (POST with JSON body):
```json
{
  "raw_text": "document text...",
  "financial_data": {"revenue": 100000000, "net_income": 15000000, ...},
  "company_name": "Example Corp"
}
```

**Response** includes `hallucination_check` with `has_inconsistency` and `inconsistencies` if numbers diverge from extracted data.

**Config** (`.env`): 
- `GROQ_API_KEY` – Get free API key from https://console.groq.com
- `GROQ_MODEL` – Default: `llama-3.3-70b-versatile`
- `LLM_TEMPERATURE=0.2`
- `LLM_MAX_TOKENS=4096`

## Financial Trend Comparison Engine

The `/api/v1/trends/compare` endpoint compares multiple years of financial data.

**Capabilities:**
- Compare revenue growth across years
- Compute CAGR (Compound Annual Growth Rate)
- Rule-based anomaly detection (revenue up / profit down, margin decline, etc.)
- Year-over-year change
- Growth chart data (labels, series)
- Risk trend evolution

**Input** (POST with JSON body):
```json
{
  "financial_records": [
    {"year": 2021, "revenue": 100000000, "net_income": 15000000, "assets": 500000000, "liabilities": 200000000, "profit_margin": 15, "gross_margin": 40},
    {"year": 2022, "revenue": 120000000, "net_income": 12000000, "assets": 550000000, "liabilities": 250000000, "profit_margin": 10, "gross_margin": 38},
    {"year": 2023, "revenue": 130000000, "net_income": 14000000, ...}
  ]
}
```

**Output:**
- `growth_analysis`: CAGR, period, YoY growth
- `anomaly_flags`: Rule-based anomalies (rule_id, explanation, data)
- `trend_summary`: Explainable summary
- `year_over_year_change`: Detailed YoY deltas
- `visual_data`: Chart-ready labels, series, growth_series, risk_trend

**Anomaly rules:** REV_UP_PROFIT_DOWN, MARGIN_DECLINE, GROSS_MARGIN_COLLAPSE, LIABILITIES_OUTPACE_ASSETS, NEGATIVE_PROFIT, REVENUE_DECLINE.

## Knowledge Graph Engine

The `/api/v1/knowledge-graph/build` endpoint constructs a financial knowledge graph from LLM output.

**Nodes:** Company, Revenue, Risk, Regulation, Assets, Market  
**Edges:** has_revenue, exposed_to_risk, regulated_by, competes_with

**Input** (POST with JSON body):
```json
{
  "llm_output": {"executive_summary": "...", "risk_analysis": "...", "red_flags": [...]},
  "company_name": "Example Corp",
  "financial_data": {"revenue": 100000000, "assets": 500000000, "risks": ["Risk 1..."]}
}
```

**Output:** Graph JSON for frontend visualization (D3, vis.js, etc.):
```json
{
  "nodes": [{"id": "company:main", "type": "Company", "label": "Example Corp"}, ...],
  "edges": [{"source": "company:main", "target": "revenue:main", "type": "has_revenue"}, ...],
  "stats": {"node_count": 10, "edge_count": 12}
}
```

**Purpose:** Explain how insights were derived; show relationships between financial indicators.

## Vector Database (ChromaDB)

Semantic search and RAG across financial reports. Scalable for thousands of reports.

**Endpoints:**
- `POST /api/v1/vector/index` – Index report text (chunk, embed, store)
- `POST /api/v1/vector/search` – Natural language search across reports
- `POST /api/v1/vector/rag` – RAG query (retrieve context + prompt for LLM)
- `GET /api/v1/vector/stats` – Collection stats (total chunks)

**Index Request:**
```json
{
  "report_id": "report-2023-001",
  "raw_text": "Full report text...",
  "company_name": "Example Corp",
  "report_year": "2023",
  "metadata": {}
}
```

**Search Request:**
```json
{
  "query": "What were the main risk factors?",
  "top_k": 5,
  "company_name": "Example Corp",
  "report_year": "2023"
}
```

**RAG Response** includes `rag_prompt` – pass to LLM for contextual answers.

**Config** (`.env`): `CHROMA_PERSIST_DIR`, `EMBEDDING_MODEL`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `RAG_TOP_K`.

**Scalability:** Chunk-based indexing, batch add, metadata filtering (company/year), HNSW for fast search.

## Document Processing Pipeline

The `/api/v1/documents/process` endpoint runs a full extraction pipeline:

1. **Detect** if PDF is scanned (image-based) or digital (text-based)
2. **Extract text**: direct extraction for digital, Tesseract OCR for scanned
3. **Extract tables** via PyMuPDF `find_tables()`
4. **Clean text**: normalize whitespace, remove control chars
5. **Extract metadata**: company name, report year, report type (heuristics)

**Response:**
```json
{
  "company_name": "...",
  "report_year": "2023",
  "raw_text": "...",
  "extracted_tables": [[["col1","col2"], ["a","b"]]],
  "metadata": {"page_count": 10, "is_scanned": false, ...}
}
```

**Prerequisites:**
- Tesseract OCR for scanned PDFs (install from https://github.com/UB-Mannheim/tesseract/wiki)
- On Windows, set `TESSERACT_CMD` in `.env` if not in PATH

## Future Integration Points

- **LLM**: `raw_text` and `extracted_tables` ready for prompt construction
- **Queue**: Add Celery/Redis for async PDF processing pipelines
