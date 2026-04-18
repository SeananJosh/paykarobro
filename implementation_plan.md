# PaykaroBRO AI — Implementation Plan v1.0
> April 2026 | Confidential

---

## Goal

Build a multi-agent AI financial co-pilot for Indian SMEs that ingests financial data, predicts cash flow, ranks payment obligations, and autonomously executes approved payments — in a secure, auditable, and scalable manner.

---

## Tech Stack

### Frontend

| Layer | Technology | Why |
|---|---|---|
| Web App | **React 18** (Vite) | Component-based, large ecosystem, fast HMR |
| Mobile App | **React Native** (Expo) | Code sharing with web, native performance *(v1.2)* |
| State Management | **Zustand** | Lightweight, scalable, easy async patterns |
| Data Viz | **Recharts** + **D3.js** | Cash flow timelines, heatmaps, KPI cards |
| Styling | **Vanilla CSS** + CSS Variables | Full design control, no bloat |
| Voice UI | **Web Speech API** + **Whisper API** | Browser-native + fallback AI transcription *(v1.2)* |
| HTTP Client | **Axios** + **React Query** | Caching, background refetch, optimistic updates |

### Backend

| Layer | Technology | Why |
|---|---|---|
| AI Inference API | **FastAPI** (Python 3.11) | Async, high-throughput, native LangChain integration |
| API Gateway / Real-time | **Node.js** (Express + Socket.IO) | WebSocket support, event streaming to frontend |
| AI Orchestration | **LangChain** + **LangGraph** | Multi-agent coordination, tool use, state graphs |
| LLM | **GPT-4o** (reasoning) + **Claude 3.5 Sonnet** (generation) | Hybrid routing by cost vs sophistication |
| Authentication | **JWT** + **OAuth 2.0** | Stateless auth, Google/bank OAuth *(v1.1)* |
| 2FA | **TOTP** (Google Authenticator) + **SMS OTP** | Mandatory for payment execution |

### Data Layer

| Layer | Technology | Why |
|---|---|---|
| Primary DB | **PostgreSQL 16** (AWS RDS) | ACID compliance for financial transactions |
| Cache | **Redis 7** (AWS ElastiCache) | Sessions, rate limiting, agent result caching |
| File Storage | **AWS S3** | CSV imports, PDF reports, immutable audit logs |
| Message Queue | **AWS SQS** + **SNS** | Async agent task dispatch, webhook fanout |
| Search | **pg_trgm** (Postgres extension) | Full-text search on expenses/vendors |

### Infrastructure

| Layer | Technology | Why |
|---|---|---|
| Cloud | **AWS** (ap-south-1 — Mumbai) | Indian data residency, RBI compliance |
| Containers | **Docker** + **AWS ECS Fargate** | Serverless containers, horizontal scaling |
| Orchestration | **AWS EKS** *(v1.1 onwards)* | For 10K+ concurrent users |
| CI/CD | **GitHub Actions** | Automated test → build → deploy pipeline |
| Monitoring | **AWS CloudWatch** + **Sentry** | Infra metrics + frontend/backend error tracking |
| Secrets | **AWS Secrets Manager** | API keys, DB credentials, payment credentials |
| CDN | **AWS CloudFront** | Fast global delivery + DDoS protection |

### Payments

| Layer | Technology | Why |
|---|---|---|
| Payment Gateway | **Razorpay API** | PCI-DSS compliant, covers cards + UPI + NEFT |
| UPI Gateway | **NPCI UPI** | Direct UPI access, lower fees for SMEs |
| Webhook Handling | **SQS + Lambda** | Reliable async payment status updates |

---

## System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                        │
│      React Web App (Vite)     React Native App (v1.2)    │
│      Voice Interface (v1.2)   WhatsApp Bot (v1.2)        │
└──────────────────────┬───────────────────────────────────┘
                       │ HTTPS / WebSocket
┌──────────────────────▼───────────────────────────────────┐
│                 API GATEWAY (Node.js)                    │
│  Auth Middleware │ Rate Limiter │ WebSocket Manager      │
└──────┬───────────────────────────────────┬───────────────┘
       │ REST                              │ Events
┌──────▼─────────────────────┐  ┌─────────▼───────────────┐
│    FastAPI AI Service       │  │    AWS SQS / SNS        │
│  ┌─────────────────────┐   │  │  Agent Task Queue       │
│  │  Intent Router      │   │  │  Payment Webhooks       │
│  │  Cash Flow Agent    │   │  └─────────────────────────┘
│  │  Priority Agent     │◄──┼── LangGraph State Machine
│  │  Negotiation Agent  │   │
│  │  Payment Agent      │   │
│  │  Insight Agent      │   │
│  └─────────────────────┘   │
└──────┬─────────────────────┘
       │
┌──────▼───────────────────────────────────────┐
│                 DATA LAYER                   │
│  PostgreSQL 16 ── Redis 7 ── AWS S3         │
└──────┬───────────────────────────────────────┘
       │
┌──────▼───────────────────────────────────────┐
│               PAYMENT LAYER                  │
│  Razorpay API ── NPCI UPI Gateway           │
└──────────────────────────────────────────────┘
```

---

## Agent Design

### Intent Router
- Input: raw user query (text or voice transcript)
- Output: target agent name + structured parameters
- Model: GPT-4o with function calling
- Tools: `classify_intent(query) → {agent, params}`

### Cash Flow Prediction Agent
- Input: bank statements, invoices, historical transaction data
- Output: 30/60/90-day forecast with confidence intervals
- Pipeline: LangGraph stateful → statistical baseline + LLM commentary
- Tools: `fetch_transactions()`, `run_forecast()`, `generate_heatmap()`

### Priority Decision Agent
- Input: list of all outstanding obligations
- Output: ranked payment queue with rule-based + LLM reasoning
- Scoring weights: due date urgency (40%) + penalty risk (30%) + vendor importance (20%) + cash availability (10%)
- Model: Claude 3.5 Sonnet (reasoning transparency, cost-effective)

### Negotiation Agent
- Input: vendor record + outstanding obligation
- Output: pre-drafted deferral email / WhatsApp message
- Model: GPT-4o (strong natural language generation)
- Tools: `fetch_vendor_history()`, `draft_message()`, `send_via_channel()`

### Payment Execution Agent
- Input: approved payment instruction + user 2FA token
- Output: payment receipt or rollback confirmation
- Authorization: Double-verify user approval + 2FA before any execution
- Tools: `validate_2fa()`, `execute_payment_razorpay()`, `create_audit_log()`

### Insight & Explanation Agent
- Input: all agent outputs + financial context summary
- Output: plain-language daily digest, anomaly flags
- Model: Claude 3.5 Sonnet
- Tools: `summarize_decisions()`, `flag_anomalies()`, `generate_digest()`

---

## Database Schema (Key Tables)

```sql
-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT,
  totp_secret TEXT,
  role TEXT DEFAULT 'owner',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Businesses (multi-business support in v2.0)
CREATE TABLE businesses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  gstin TEXT,
  owner_id UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Obligations / Expenses
CREATE TABLE obligations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id UUID REFERENCES businesses(id),
  vendor_name TEXT NOT NULL,
  amount NUMERIC(15,2) NOT NULL,
  currency TEXT DEFAULT 'INR',
  due_date DATE NOT NULL,
  category TEXT,
  priority_score NUMERIC(5,2),
  status TEXT DEFAULT 'pending', -- pending | approved | paid | deferred
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Cash Flow Forecasts
CREATE TABLE forecasts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id UUID REFERENCES businesses(id),
  forecast_date DATE NOT NULL,
  predicted_balance NUMERIC(15,2),
  confidence_lower NUMERIC(15,2),
  confidence_upper NUMERIC(15,2),
  generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent Decision Audit Log
CREATE TABLE agent_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_id UUID REFERENCES businesses(id),
  agent_name TEXT NOT NULL,
  input_summary TEXT,
  output_summary TEXT,
  reasoning TEXT,
  user_action TEXT, -- approved | overridden | dismissed
  executed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Payments
CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  obligation_id UUID REFERENCES obligations(id),
  business_id UUID REFERENCES businesses(id),
  amount NUMERIC(15,2) NOT NULL,
  payment_method TEXT,  -- UPI | NEFT | card
  gateway_ref TEXT,
  status TEXT DEFAULT 'initiated', -- initiated | success | failed | rolled_back
  executed_at TIMESTAMPTZ,
  rolled_back_at TIMESTAMPTZ
);
```

---

## API Contract (Key Endpoints)

### FastAPI — AI Service

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/agents/intent` | Route natural language query to agent |
| POST | `/api/v1/agents/cashflow/forecast` | Generate 30-day cash flow forecast |
| GET | `/api/v1/agents/cashflow/forecast/{business_id}` | Fetch latest saved forecast |
| POST | `/api/v1/agents/priority/rank` | Rank all outstanding obligations |
| POST | `/api/v1/agents/negotiation/draft` | Draft vendor negotiation message |
| POST | `/api/v1/agents/payment/execute` | Execute approved payment (requires 2FA token) |
| GET | `/api/v1/agents/insight/digest/{business_id}` | Fetch today's AI digest |

### Node.js Gateway

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/login` | JWT login |
| POST | `/auth/2fa/verify` | Verify TOTP/OTP before payment |
| GET | `/ws/events/{business_id}` | WebSocket for real-time alerts |
| POST | `/expenses/import` | Bulk CSV import |
| GET | `/obligations/{business_id}` | List all obligations with AI scores |
| PATCH | `/obligations/{id}/status` | Update obligation status (approve/defer) |

---

## Folder Structure

```
paykarobro/
├── frontend/                    # React 18 + Vite web app
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Dashboard, Obligations, Forecast, Settings
│   │   ├── stores/              # Zustand state stores
│   │   ├── services/            # Axios API clients
│   │   ├── hooks/               # Custom React hooks
│   │   └── styles/              # Global CSS & design tokens
│   └── index.html
│
├── backend/
│   ├── ai-service/              # FastAPI + LangGraph agents (Python)
│   │   ├── agents/
│   │   │   ├── cashflow_agent.py
│   │   │   ├── priority_agent.py
│   │   │   ├── negotiation_agent.py
│   │   │   ├── payment_agent.py
│   │   │   ├── insight_agent.py
│   │   │   └── intent_router.py
│   │   ├── routers/             # FastAPI route handlers
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── services/            # DB, Redis, S3, Razorpay clients
│   │   ├── tests/               # Unit + integration tests
│   │   └── main.py
│   │
│   └── gateway/                 # Node.js API Gateway (TypeScript)
│       ├── src/
│       │   ├── routes/
│       │   ├── middleware/      # Auth, rate-limit, 2FA
│       │   ├── websocket/
│       │   └── app.ts
│       └── package.json
│
├── infra/                       # AWS CDK IaC
│   ├── ecs/
│   ├── rds/
│   └── sqs/
│
├── docs/
│   ├── PRD.md
│   └── implementation_plan.md
│
└── docker-compose.yml           # Local dev environment
```

---

## Hackathon Implementation Roadmap

> **Strategy:** Build a fully working, demo-able prototype in 48 hours using mocked-where-necessary data.
> Post-hackathon modules are clearly labelled for future development sprints.

---

### 🏁 Hackathon Prototype — 48 Hours (Working MVP)

**Goal:** A live, click-through demo that shows the full AI loop:
expense input → AI priority ranking → 30-day cash flow forecast → dashboard KPIs → approve/override action

#### What's REAL (built during hackathon)
| # | Feature | Status |
|---|---|---|
| 1 | React dashboard UI — KPI cards, cash flow chart, obligation board | ✅ Built |
| 2 | Manual expense input form + CSV upload | ✅ Built |
| 3 | Priority Decision Agent — LLM ranks obligations with reasoning | ✅ Built |
| 4 | Cash Flow Prediction — rule-based forecast with chart | ✅ Built |
| 5 | Insight Agent — plain-language AI daily digest | ✅ Built |
| 6 | Approve / Override / Dismiss actions on each obligation | ✅ Built |
| 7 | Agent decision audit log (in-session) | ✅ Built |
| 8 | FastAPI backend with SQLite (local, no infra needed) | ✅ Built |
| 9 | JWT auth (simple, no 2FA for prototype) | ✅ Built |

#### What's SIMULATED (mocked for demo, replaced post-hackathon)
| # | Feature | Mock Strategy |
|---|---|---|
| 1 | Bank statement ingestion | Pre-loaded sample JSON dataset |
| 2 | Payment execution | Simulated confirmation screen (no real API call) |
| 3 | WhatsApp alerts | UI notification banner instead |
| 4 | Real-time WebSocket | Polling every 5s on prototype |
| 5 | Razorpay / UPI integration | Mock payment receipt shown |

#### Hackathon Tech Choices (simplified for speed)
| Layer | Hackathon Choice | Production Swap |
|---|---|---|
| DB | **SQLite** (zero setup) | PostgreSQL 16 on AWS RDS |
| Cache | In-memory dict | Redis 7 |
| Auth | Simple JWT, no 2FA | JWT + TOTP 2FA |
| Infra | **localhost** / Vercel + Railway | AWS ECS Fargate |
| Queue | Synchronous calls | AWS SQS + SNS |
| LLM | **GPT-4o** (single provider) | GPT-4o + Claude 3.5 Sonnet hybrid |

#### Hour-by-Hour Hackathon Sprint Plan

```
HOUR 00–04  ── Setup
  │  Scaffold repo, Vite + React frontend, FastAPI backend
  │  SQLite schema: users, businesses, obligations, forecasts, audit_log
  │  Basic JWT auth (login + session)
  │
HOUR 04–10  ── Core Agents
  │  Priority Decision Agent (LangChain + GPT-4o)
  │    → Score obligations: urgency, penalty risk, vendor importance, cash
  │  Cash Flow Prediction (rule-based + LLM commentary)
  │    → 30-day forecast from sample bank data
  │  Insight Agent → daily digest in plain English
  │
HOUR 10–18  ── Dashboard UI
  │  KPI Cards: Days Cash on Hand, Burn Rate, Payables Aging
  │  Cash Flow Timeline chart (Recharts, 30-day view)
  │  Obligation Board: ranked list + approve/override/dismiss buttons
  │  AI Reasoning panel: show agent justifications inline
  │  Agent Audit Log table
  │
HOUR 18–24  ── Integration + Polish
  │  Connect FastAPI agents to React frontend (Axios)
  │  CSV expense import (Papa Parse)
  │  Simulated payment confirmation modal
  │  Loading states, error handling, toasts
  │
HOUR 24–36  ── Demo Prep + Testing
  │  Seed realistic SME demo data (Ravi's cloud kitchen scenario)
  │  End-to-end flow walkthrough: input → rank → forecast → approve
  │  Fix critical bugs
  │  Deploy: frontend → Vercel, backend → Railway (free tier)
  │
HOUR 36–48  ── Buffer + Presentation
     Polish UI, record demo video, build pitch slides
```

#### Hackathon Deliverable Checklist
- [ ] User can log in and see their business dashboard
- [ ] User can add expenses manually or via CSV upload
- [ ] Priority Decision Agent ranks all obligations with LLM reasoning visible
- [ ] Cash flow chart shows 30-day forecast with current balance
- [ ] KPI cards render: Days Cash on Hand, Burn Rate, Payables Aging
- [ ] User can approve, override, or dismiss each AI recommendation
- [ ] Insight Agent shows a plain-English digest of the financial situation
- [ ] Agent audit log shows all decisions made
- [ ] Simulated payment confirmation flow works end-to-end
- [ ] App is live and accessible via public URL (Vercel + Railway)

---

## Post-Hackathon Module Roadmap

After the hackathon, the prototype evolves into production through 4 focused modules. Each module is independently shippable.

---

### Module 1 — Production Infrastructure (2 Weeks)
**Goal:** Replace all hackathon shortcuts with production-grade systems

| Task | Detail |
|---|---|
| Migrate SQLite → PostgreSQL | AWS RDS, full schema migration |
| Add Redis cache | Session management, agent result caching |
| Containerize with Docker | docker-compose.yml for local dev |
| Deploy to AWS ECS Fargate | ap-south-1 (Mumbai), RBI data residency |
| GitHub Actions CI/CD | Auto test → build → deploy on push to main |
| JWT → JWT + TOTP 2FA | Mandatory for payment-related actions |
| Environment secrets | AWS Secrets Manager for all credentials |

**Output:** Identical functionality as hackathon prototype, but running on production infra

---

### Module 2 — Payment & Bank Execution (3 Weeks)
**Goal:** Close the AI-to-action loop with real payment execution

| Task | Detail |
|---|---|
| Razorpay API integration | Cards, NEFT, IMPS payment execution |
| NPCI UPI Gateway | Direct UPI payments for SMEs |
| Payment audit trail | Immutable write-once S3 log |
| 60-second rollback | Reverse any payment within 1 minute |
| Bank statement ingestion | Account Aggregator API (Setu/Finvu) |
| WhatsApp bot (360dialog) | Alerts + approve/deny via WhatsApp |
| Load testing | 1,000 concurrent users, p95 < 3s |

**Output:** Users can approve and execute real payments with full audit trail

---

### Module 3 — Voice & Mobile (3 Weeks)
**Goal:** Mobile-first + voice interface for on-the-go SME owners

| Task | Detail |
|---|---|
| React Native app (Expo) | iOS + Android, shared business logic |
| Whisper ASR integration | Voice-to-text for expense input & commands |
| Intent router (voice) | Parse voice commands → dispatch to agent |
| Push notifications | Firebase FCM for payment reminders |
| Offline mode | Queue actions locally, sync on reconnect |
| Negotiation Agent | Draft vendor deferral emails, sendable via app |

**Output:** Full MVP usable on mobile with voice commands and push alerts

---

### Module 4 — Scale & Intelligence (4 Weeks)
**Goal:** Enterprise-ready, multilingual, deeply integrated platform

| Task | Detail |
|---|---|
| Multi-business portfolio | One login, manage multiple SME accounts |
| Hindi + Tamil language | UI copy + voice recognition |
| Tally / Zoho Books sync | Bidirectional data sync via their APIs |
| Advanced ML forecasting | Replace rule-based with Prophet/LSTM model |
| SOC 2 Type II audit prep | Evidence collection, controls documentation |
| Pen testing + bug bounty | Third-party security audit |
| 10K concurrent user test | AWS EKS migration if needed |

**Output:** Enterprise-grade platform ready for Series A SME customer acquisition

---

## Security Implementation Checklist

- [ ] AES-256 encryption at rest (RDS + S3)
- [ ] TLS 1.3 enforced on all endpoints
- [ ] 2FA mandatory before any payment execution
- [ ] Stateless agents — PII masked before entering LLM context
- [ ] Zero-trust VPC: services only reachable internally
- [ ] Payment audit log stored in write-once S3 bucket (Object Lock)
- [ ] Rollback window: 60 seconds post-payment execution
- [ ] Rate limiting: 100 req/min per business on payment endpoints
- [ ] Quarterly pen testing + bug bounty program

---

## Open Questions

> **LLM Provider** — Use GPT-4o + Claude hybrid from day 1, or start single provider and expand later?

> **Account Aggregator** — Which AA partner: Finvu, Perfios, or Setu? (affects bank statement ingestion scope and licensing)

> **Payment Authorization** — Is user 2FA sufficient, or add a secondary approver for payments above a threshold (e.g., ₹1L+)?

> **WhatsApp Channel** — Twilio, 360dialog, or direct Meta API? SLAs differ significantly.

> **SOC 2 Timeline** — Target Type II by v1.1 launch or defer to v2.0?

---

## Verification Plan

### Automated Tests
```bash
# Python unit tests
pytest backend/ai-service/tests/ --cov=agents --cov-report=term

# API integration tests
pytest backend/ai-service/tests/integration/

# Frontend unit tests
cd frontend && npm run test

# E2E browser tests
cd frontend && npx playwright test
```

### Performance Benchmarks
- AI agent response time: < 3 seconds (p95)
- Dashboard loads: < 1.5 seconds (Lighthouse score > 90)
- Payment execution: < 5 seconds end-to-end

### Security Validation
- OWASP ZAP scan on all public endpoints
- Verify 2FA challenge fires on every payment attempt
- Confirm audit log is append-only and tamper-evident

### Manual QA (Persona-Based)
- **Ravi**: Enter 10 expenses → verify ranked queue + 30-day forecast
- **Priya**: Trigger burn-rate alert → confirm real-time WebSocket notification
- **Arjun**: Use Negotiation Agent → verify deferral email draft quality

---

*PaykaroBRO AI | Implementation Plan v1.0 | April 2026 | Confidential*
