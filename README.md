<div align="center">

# 📊 GenAI-Driven Intelligent System for Automated Financial Report Analysis
**Transforming Unstructured Financial Data into Actionable, Explainable AI Insights. 🚀**

<p align="center">
  <img src="https://img.shields.io/badge/Status-Active%20%26%20Production%20Ready-success?style=for-the-badge" alt="Status" />
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/Llama_3-70B-purple?style=for-the-badge&logo=meta" alt="Llama 3" />
  <br/>
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" alt="License" />
  <img src="https://img.shields.io/badge/Contributions-Welcome-orange.svg?style=flat-square" alt="Contributions Welcome" />
</p>

</div>

---

## 🚀 Overview

Financial reports (10-K, Annual Reports) are dense, unstructured, and notoriously difficult to extract meaningful data from manually. **This system automates the entire analytical pipeline**. 

By simply uploading a PDF, the platform automatically extracts text and tables (even from scanned documents), calculates critical financial ratios, and unleashes the power of **Large Language Models (Llama-3 via Groq)** to generate deep qualitative insights. 

**Why is it unique?** 
Unlike standard AI wrapper tools, this system features a **Hallucination Guard** that cross-validates the AI's numerical claims against deterministic mathematical extraction, ensuring enterprise-grade factual accuracy. Furthermore, it dynamically builds a **Knowledge Graph** to explain the relationships between companies, risks, and financial metrics.

---

## ✨ Features

- **📄 Robust PDF Processing:** Supports both digital PDFs (via PyMuPDF) and scanned documents (via Tesseract OCR fallback).
- **💰 Financial Data Structuring:** Pulls precise monetary values, multi-year data, and tables out of raw text using NLP and Regex.
- **🧠 LLM-Based Insights:** Generates executive summaries, investment recommendations, and risk analysis using advanced Prompt Engineering.
- **🛡️ Hallucination Guard:** Automatically flags and penalizes the AI if it fabricates or miscalculates numbers.
- **📈 Trend & Anomaly Analysis:** Computes YoY growth, CAGR, and automatically alerts on severe margin collapses or revenue drops.
- **🕸️ Dynamic Knowledge Graph:** Maps entities and risks visually for complete explainability.
- **📊 Premium Interactive Dashboard:** Sleek, glass-morphism Next.js UI containing KPI cards, heatmaps, and Recharts-based trends.
- **📥 One-Click PPT Generation:** Exports the full analysis into an investor-ready presentation format.

---

## 🧠 How It Works (Workflow)

The system is fully decoupled. The backend handles heavy lifting, processing, and AI validation, while the frontend handles rendering and user interactions.

### Step-by-Step Flow:
> **User** ➔ **Upload PDF** ➔ **Backend** ➔ **Processing** ➔ **AI** ➔ **Validation** ➔ **Dashboard** ➔ **Output**

### Visual Processing Pipeline:
```text
[PDF Upload] 
     ↓
[Document Processing]  (PyMuPDF / OCR) 
     ↓
[Data Structuring]     (Regex, spaCy NER, Table Parsing)
     ↓
[Mathematical Engine]  (Calculates Ratios, Margins, Debt)
     ↓
[LLM Intelligence]     (Groq Llama-3 Generates Analysis)
     ↓
[Validation Layer]     (Hallucination Guard checks AI Math)
     ↓
[Visualization]        (Next.js Dashboard, Knowledge Graph)
```

---

## 🏗️ Architecture

The backend implements a scalable, layer-driven architecture ensuring separation of concerns:

```text
=================== FASTAPI BACKEND ===================
1. Routers Layer        (API Endpoints)
2. Services Layer       (Business Logic / Engines)
   ├─ Document Processor
   ├─ Financial Parser
   ├─ LLM Engine
   ├─ Trend Engine
   └─ Knowledge Graph Builder
3. Validation Layer     (Hallucination Guard)
4. Domain Models        (Pydantic Data Contracts)
=========================================================
                          ⇅ REST API (JSON)
=================== NEXT.JS FRONTEND ====================
1. Pages                (Main Dashboard UI)
2. Components           (KPIs, Charts, Upload Zone)
3. State Management     (Parallel API convergence)
=========================================================
```

---

## 📂 Project Structure

```text
genai-finance-platform/
│
├── backend/                   # Python FastAPI Server
│   ├── app/
│   │   ├── main.py            # API Gateway
│   │   ├── config.py          # Envs & settings
│   │   ├── routers/           # HTTP endpoints
│   │   ├── services/          # Core extraction/AI engines
│   │   └── models/            # Pydantic Schemas
│   ├── requirements.txt
│   └── .env                   # Environment variables
│
├── frontend/                  # Next.js React App
│   ├── src/
│   │   ├── app/               # Next.js App Router (page.tsx)
│   │   ├── components/        # Isolated UI visual components
│   │   └── lib/               # API connection logic
│   ├── package.json
│   └── tailwind.config.ts     # UI Styling tokens
```

---

## ⚙️ Installation & Setup

Follow these steps to get the project running on your local machine.

### 1. Clone Repo
```bash
git clone https://github.com/your-username/genai-finance-platform.git
cd genai-finance-platform
```

### 2. Backend Setup
Requires **Python 3.10+** and Tesseract installed on your OS system path.

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Environment Variables (Backend)
Create a `.env` file in the `backend/` directory:
```text
GROQ_API_KEY=gsk_your_groq_api_key_here
```
*(Get a free extremely fast AI API key from [console.groq.com](https://console.groq.com))*

### 4. Frontend Setup
Requires **Node.js 18+**.

```bash
cd ../frontend
npm install
```

---

## ▶️ How to Run

You must run both servers simultaneously in separate terminals.

### Run Backend
```bash
cd backend
python -m uvicorn app.main:app --reload
```
API Documentation available at: `http://localhost:8000/docs`

### Run Frontend
```bash
cd frontend
npm run dev
```
Dashboard available at: `http://localhost:3000`

---

## 📊 Example Output

The backend structures the chaotic PDF text into pure, validated JSON data for the frontend:

```json
{
  "financials": {
    "revenue": 1000000000,
    "net_income": 200000000,
    "profit_margin": 20.0,
    "risk_score": 35
  },
  "llm_insights": {
    "executive_summary": "The company demonstrated strong YoY growth...",
    "confidence_score": 0.95,
    "red_flags": ["Excessive regulatory exposure"]
  }
}
```

---

## 📈 Dashboard Preview

The frontend is a premium, glassmorphism-styled dashboard containing:
- **KPI Cards:** Instant view of Revenue, Assets, and Margins with positive/negative color coding.
- **Area & Composed Charts:** Tracks Revenue trends vs. Operating Expenses across multiple years.
- **Knowledge Graph:** A physics-based, interactive mapping of financial entities (Company → Risks, Regulations).
- **Radar Chart:** Visualizes financial health bounds (Liquidity, R&D Intensity, Debt Ratio).

---

## 🔥 Key Innovations

1. **Hallucination Guard:** The LLM's number generation is strictly monitored. If the AI states revenue is "$5B", but the deterministic parser calculated "$4B", the guard flags the hallucination and lowers the system confidence score immediately.
2. **Knowledge Graph (NetworkX):** Automatically converts unreadable financial walls-of-text into an interactive structural map. 
3. **End-to-End Automation:** Consolidates 4 separate tools (Extraction, Analysis, Visualization, and PPT Reporting) into a single 10-second workflow.

---

## 🧪 Testing

1. Launch both servers as listed in the "How to Run" section.
2. Open `localhost:3000`.
3. Locate an Apple 10-K, Tesla Annual Report, or any dummy financial PDF.
4. Drag and drop into the upload zone.
5. **Expected Results:** The UI should transition from uploading, to analyzing, to displaying the entire comprehensive dashboard automatically.

---

## ⚠️ Common Errors & Fixes

- **`401 Unauthorized` / Groq API Error:**
  - *Fix:* Ensure your `GROQ_API_KEY` is present in the `backend/.env` file and is a valid key.
- **`Failed to fetch` on Frontend:**
  - *Fix:* The backend server is not running, or it's running on the wrong port. It must be accessible at `http://localhost:8000`.
- **OCR Not Extracting Text Expectedly:**
  - *Fix:* Ensure Tesseract-OCR is installed correctly on your actual operating system (e.g., via `apt-get install tesseract-ocr` or the Windows installer).

---

## 🚀 Future Improvements

- **Real-Time Market APIs:** Connect to Bloomberg or Alpha Vantage to benchmark analyzed reports against live stock ticks.
- **Predictive ML Models:** Integrate Deep Learning models (like Meta's Prophet) to forecast future revenue based on historical Extractions.
- **Multi-Language Support:** Expand OCR and NLP parsing to German, Japanese, and Mandarin financial disclosures.

---

## 🤝 Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 👨‍💻 Team

Developed by:
- **Pranav Dhote**
- **Purva Bhambere**
- **Omkar Avasare**


---

## ⭐ Show Support

**If you found this project helpful, creative, or useful for your own learning, please hit the ⭐ button at the top right of this repository!**
