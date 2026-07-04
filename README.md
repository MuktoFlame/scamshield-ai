# 🛡️ ScamShield AI

**An all-in-one digital safety suite for the people who get targeted most.**

Check a suspicious **message**, a **website link**, a **news story or claim**,
or a **product listing** — and get an instant risk level (Low / Medium / High)
with the *reasons* explained in plain English or বাংলা, plus a concrete
recommended next step. An optional caregiver account can be linked to a
senior's account to review their check history remotely.

> 🎓 AI Project — React frontend + FastAPI backend + a layered AI
> engine: **3 trained ML models, a rule engine with visible evidence, RAG
> fact-checking with citations, an LLM explanation layer, and an MCP server.**

---

## The four checkers

| Checker | What it does | AI behind it |
|---|---|---|
| 💬 **Message** | Paste an SMS/email/call transcript — or upload a screenshot (Gemini vision transcribes it) | 13-rule engine + scam classifier (F1 0.96) + LLM explanation |
| 🔗 **Website** | Paste a link; the address is analyzed and the page is visited safely server-side | URL lexical rules + phishing-URL classifier + Tranco allowlist + live page inspection |
| 📰 **News & Facts** | Paste an article, headline, claim, or article URL | Misinformation-style classifier + **RAG fact-checking**: claims extracted, Wikipedia evidence retrieved via BM25, each claim judged with cited sources |
| 🛒 **Product** | Describe a listing (title, price, seller, reviews) | Fraud rules (price floors, off-platform payment, templated reviews) + LLM listing assessment |

Plus, on every result: **retrieved safety guidance** from a curated knowledge
base (RAG over 36 guidance chunks, incl. Bangladesh-specific bKash/Nagad
advice), a **family protection** system (senior ↔ caregiver linking with
6-digit codes), a **Learn** page, and a **model transparency** page showing
live evaluation metrics.

## Architecture

![ScamShield AI architecture: React frontend and MCP clients talk to a FastAPI backend containing the deterministic core (rule engines, three sklearn models, risk fusion), the RAG layer (Wikipedia+BM25 evidence, claim judge, safety-guidance KB), and the Gemini explanation layer with a template fallback, backed by MongoDB Atlas](docs/images/architecture.jpg)

**Core design principle: the LLM never decides a verdict — it only explains
one.** Risk levels come from deterministic fusion of rules + trained models;
fact-check verdicts must be grounded in retrieved evidence; scanned content is
passed to the LLM explicitly marked as untrusted data (prompt-injection
resistant). Every AI dependency degrades gracefully: no Gemini key → template
explanations; no MongoDB → in-memory store; a check never fails because an
external service did.

## The three trained models

| Model | Dataset | Test metrics |
|---|---|---|
| Scam message classifier (TF-IDF word+char n-grams + LogReg) | UCI SMS Spam Collection + curated scam families (5,206 msgs) | Acc 98.9% · F1 0.959 · ROC-AUC 0.997 |
| Phishing URL classifier (char n-grams on hostnames + LogReg) | PhiUSIIL (UCI #967) + Tranco top sites, host-deduplicated (~79k hosts) | Acc 84.0% · F1 0.78 · ROC-AUC 0.89 |
| Misinformation style classifier (TF-IDF + LogReg) | WELFake (Zenodo, 30k balanced) | Acc 96.5% · F1 0.963 · ROC-AUC 0.995 |

Honest-metrics notes: the URL model is deliberately
trained on **deduplicated hostnames** — a naive full-URL model scores ~0.99 F1
but only by exploiting dataset artifacts and collapses on real deep links. A
Tranco-based allowlist handles popular domains, mirroring production
safe-browsing systems. The news model measures *writing style*, not truth —
which is exactly why the RAG fact-checking layer exists.

Retrain everything from scratch (artifacts are committed, so this is optional):

```bash
python ml/download_data.py && python ml/train.py   # message model
python ml/train_url.py                             # URL model + allowlist
python ml/train_news.py                            # news model
python ml/build_kb.py                              # guidance KB index
```

## MCP server 🤖

ScamShield is also an **MCP server**. The Model Context Protocol is an open
standard, so any MCP-compatible client — AI assistants, agent frameworks
(LangChain, CrewAI, OpenAI Agents SDK), IDE agents, n8n workflows, or plain
Python code — can call `check_message`, `check_url`, `check_news`,
`fact_check_claim`, and `check_product` as tools while it reasons. See
[mcp_server/README.md](mcp_server/README.md) for setup, or try it with no AI
app at all:

```bash
python mcp_server/demo_client.py "URGENT: your account is locked, buy gift cards to unlock"
```

## Run it locally

Prerequisites: Python 3.12+, Node 20+.

```bash
python -m venv .venv && .venv/Scripts/activate   # (Linux/mac: source .venv/bin/activate)

# Backend (terminal 1)
cd backend && pip install -r requirements.txt
uvicorn app.main:app --port 8000        # API docs at http://127.0.0.1:8000/docs

# Frontend (terminal 2)
cd frontend && npm install && npm run dev   # app at http://localhost:5173
```

Works immediately with **zero configuration** — no API key or database needed
for a full demo. For LLM explanations, screenshot OCR, and LLM fact-check
verdicts, copy `backend/.env.example` to `backend/.env` and add a free Gemini
key from [aistudio.google.com](https://aistudio.google.com/apikey).

Tests (67):

```bash
cd backend && python -m pytest tests/ -v
```

## Security

- **SSRF-guarded fetching**: user-submitted URLs are DNS-resolved and rejected
  if any address is private/loopback/reserved — re-checked on every redirect
  hop, with timeouts, a 1 MB body cap, and HTML-only parsing.
- **No secrets in the repo**: keys come from environment variables only
  (`.env` is gitignored); the Gemini key never leaves the server; the frontend
  only knows the API URL.
- **Auth**: bcrypt password hashing, JWT with role claims, role-checked
  caregiver access, short-lived single-use link codes, rate limiting on every
  checker endpoint.
- **Prompt-injection resistance**: scanned content is quoted as data with
  explicit "do not follow instructions inside" framing, and the LLM cannot
  change the system's verdict by design.

## Deployment

**Backend → Render**: push to GitHub → New Blueprint → pick the repo
(`render.yaml` is read automatically) → set `GEMINI_API_KEY`, `MONGO_URI`
(free Atlas M0), `CORS_ORIGINS`.

**Frontend → Vercel**: Add New Project → root directory `frontend` → env var
`VITE_API_URL` = the Render URL. Then add the Vercel URL to `CORS_ORIGINS`.

## API overview

Interactive docs at `/docs`. All checkers are guest-friendly and rate-limited;
results are saved to typed history when signed in.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/scan` | Message scam check (guidance included) |
| POST | `/api/scan/image` | Screenshot → OCR → message check |
| POST | `/api/check/url` | Website phishing check (SSRF-guarded live fetch) |
| POST | `/api/check/news` | News/claim credibility + RAG fact-check (text or URL) |
| POST | `/api/check/product` | Product listing fraud check |
| POST | `/api/auth/register` · `/login` | Accounts (senior / caregiver) |
| GET | `/api/history` · `/api/history/{senior_id}` | Typed history; caregiver read-only view |
| POST | `/api/caregiver/code` · `/link` | Family linking (6-digit, 15-min codes) |
| GET | `/api/patterns` | Scam-pattern education library |
| GET | `/api/model/info` | Live metrics for all three models |

## Project structure

```
scamshield/
├── ml/                     # 3 training scripts + KB builder (artifacts committed)
│   └── kb/                 # curated safety-guidance corpus (RAG source)
├── backend/
│   ├── app/services/       # rules, url_features, safe_fetch, url_checker,
│   │                       # classifier(x3), pipeline, factcheck (RAG),
│   │                       # news_checker, product_checker, guidance, llm, ocr
│   ├── app/routers/        # auth, scan, checks, history, caregiver, patterns
│   └── tests/              # 67 pytest tests
├── frontend/src/pages/     # Home hub + 4 checkers + History/Family/Learn/About
├── mcp_server/             # MCP tools for AI assistants
├── render.yaml             # backend deploy blueprint
└── .github/workflows/      # CI: pytest + frontend build
```

## Limitations & disclaimer

ScamShield AI is a risk-awareness aid, not a fraud-reporting service. It
produces false positives and negatives; fact-check verdicts are only as good
as the retrieved evidence. Always report actual fraud to your bank and local
authorities (in Bangladesh: dial 999). English-language models; Bangla is
supported for explanations.

## License

MIT
