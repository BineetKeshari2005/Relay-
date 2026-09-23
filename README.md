# Relay — Real-Time AI Decision-Support Copilot for Field Technicians

> **YC Fall 2026 x Moss: The Zero Latency Builder Sprint**  
> *Track: Real-Time Voice & Conversational AI (Primary) | Secondary Focus: Agent Reliability, Security & Evaluation*

---

## 1. What is Relay?

**Relay** is a real-time, voice-first decision-support copilot designed for field technicians servicing complex physical equipment (commercial HVAC, industrial refrigeration, power systems, and manufacturing machinery).

Instead of stopping work, taking off gloves, and manually searching 300-page PDF equipment manuals or fragmented service histories, a technician speaks naturally to Relay:

> **Technician**: *"I'm getting E17 again on unit 017. Pressure is around 195 PSI."*

Relay instantly parses the situation, retrieves verified technical manuals, historical repair logs, and safety standard operating procedures (SOPs) via **Moss**, deterministically validates physical safety constraints, and delivers concise, actionable diagnostic guidance.

---

## 2. The Problem Being Solved

Field service operations face severe structural inefficiencies and safety hazards:

1. **Context Fragmentation**: Technicians rarely have immediate access to past repair logs for the specific unit they are standing in front of.
2. **High Latency of Manual Knowledge Access**: Finding the correct wiring schematic or lockout/tagout procedure in a 400-page PDF manual while up on a rooftop takes 15–30 minutes, leading technicians to guess or rely on faulty memory.
3. **Safety Violations & Hallucinations**: Generic chatbots hallucinate technical specifications, pressure limits, or clearance thresholds. In physical trades, a hallucinated voltage threshold or missing lockout step can result in catastrophic equipment failure or physical injury.

---

## 3. Why Low-Latency Retrieval Matters & Why Moss

In real-time conversational and voice workflows, **latency is UX**. A technician waiting 3 to 5 seconds for a response from an audio copilot will abandon the interaction and revert to manual trial-and-error.

Relay's decision loop requires:
$$\text{Voice In (ASR)} \longrightarrow \mathbf{\text{Context Assembly}} \longrightarrow \mathbf{\text{Moss Retrieval}} \longrightarrow \text{Reasoning} \longrightarrow \mathbf{\text{Safety Validation}} \longrightarrow \text{TTS Out}$$

### Measured Latency Tiers (Sub-Second Decision Loop)

| Pipeline Component | Measured Latency | Implementation Details |
|---|---|---|
| **Moss In-Memory Retrieval** | **0.5 ms – 2.0 ms** (Sub-10ms) | Pre-warmed index in local process memory with zero network roundtrips |
| **Context Assembly Engine** | **1.0 ms – 4.0 ms** | Deterministic rule-based fact extraction & safety provenance checks |
| **Evidence-Grounded Reasoning** | **50 ms – 180 ms** | Dynamic hypothesis formulation, decision branching, and validation |
| **End-to-End Backend API** | **60 ms – 220 ms** | Total wall-clock turnaround for `POST /api/reasoning/analyze` |
| **Browser Voice I/O (ASR/TTS)** | **400 ms – 900 ms** | Native Web Speech API streaming transcription and synthesis |

> **Note on Latency Claims**: The **sub-10ms** benchmark specifically measures the **Moss in-memory retrieval layer**. Total conversational roundtrip including speech processing and LLM reasoning operates safely under 1 second.

---

## 4. Current Development Phase: Phase 8 (Final QA, Hardening & Demo Readiness)

> **CORE INVARIANTS**:
> 1. $\mathbf{THE\ BACKEND\ REASONING\ PIPELINE\ IS\ 100\%\ AUTHORITATIVE}$: All voice/text queries route through the evidence-grounded reasoning service.
> 2. $\mathbf{TECHNICIAN\ CONTRIBUTION \neq VERIFIED\ COMPANY\ KNOWLEDGE}$: Unreviewed field notes retain permanent provenance and non-authoritative status.
> 3. $\mathbf{SAFETY\ ALWAYS\ COMES\ FIRST}$: High-pressure hazards and mandatory Lockout/Tagout (LOTO) are announced before any diagnostic steps.

This repository implements **Phase 8: Final QA, Hardening, Integration Testing & Demo Readiness**:
- [x] **Full Voice Loop**: Technician speaks $\rightarrow$ Speech-to-Text $\rightarrow$ `POST /api/reasoning/analyze` $\rightarrow$ Moss retrieval + Context Assembly + Safety $\rightarrow$ Spoken Response Formatting $\rightarrow$ Text-to-Speech
- [x] **Actionable Voice Formatter**: `SpokenResponseFormatter` filters out metadata lines (e.g. `Model Scope`, `Document ID`, `NOTICE:`) and guarantees a genuine, actionable technician step is voiced
- [x] **Safe Validation Fallback**: Rejection of prohibited actions (`bypass lockout`) degrades cleanly without regurgitating error strings into audio
- [x] **Frontend Voice Copilot**:
  - `useVoiceCopilot` React hook with native Web Speech API (`webkitSpeechRecognition` & `SpeechSynthesis`)
  - Modular `LiveKitVoiceBoundary` interface defining room connection contracts for multi-user WebRTC rooms
  - Prominent push-to-talk mic button, pulsing `LISTENING` preview, and `RELAY SPEAKING` mute controls
  - One-click "Read Aloud" replay on diagnostic assessment cards
  - Real-time speech-to-intent latency telemetry in header badge
- [x] **100% Deterministic Test Suite**: **105 passing tests** (64 Core + 15 Contributions + 8 Voice + 4 Voice Hardening + 5 Integration Flows + 6 API Contracts + 3 Resilience)
- [x] **Zero Hardcoded Logic**: AST anti-hardcoding audit passes with 0 violations (`npm run audit`)
- [x] **Production Bundle**: Next.js 16 App Router builds cleanly with 0 TypeScript or lint errors (`npm run build`)

---

## 5. Repository Structure

```
Relay/
│
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI routers
│   │   │   ├── reasoning.py # POST /api/reasoning/analyze (includes spoken_response)
│   │   │   ├── context.py   # POST /api/context/assemble
│   │   │   ├── demo.py
│   │   │   ├── health.py
│   │   │   ├── knowledge.py # POST /api/knowledge/contributions
│   │   │   └── retrieval.py # POST /api/retrieval/search, GET /api/retrieval/health
│   │   ├── voice/           # Phase 7 Voice Formatter & Response Synthesis
│   │   │   ├── __init__.py
│   │   │   └── formatter.py # SpokenResponseFormatter (Safety-first concise audio output)
│   │   ├── config/          # Pydantic settings & environment configuration
│   │   ├── context/         # Phase 3 Context Assembly Engine
│   │   │   ├── assembled_context.py # Strongly-typed case file models
│   │   │   ├── assembler.py # ContextAssembler service
│   │   │   ├── quality_validator.py # ContextQualityValidator
│   │   │   ├── query_extractor.py # Deterministic QueryContextExtractor
│   │   │   └── context.py   # Base context models
│   │   ├── data/            # Demo fixtures and knowledge loaders
│   │   ├── llm/             # Abstract LLMProvider interface & mock
│   │   ├── models/          # Domain models (Asset, ServiceRecord, Knowledge, Session)
│   │   ├── reasoning/       # Phase 4 Evidence-Grounded Reasoning Engine
│   │   │   ├── base.py      # Abstract ReasoningProvider
│   │   │   ├── models.py    # Strongly-typed ReasoningResult, EvidenceClaim, Citation
│   │   │   ├── prompts.py   # System prompt and AssembledContext prompt builder
│   │   │   ├── provider.py  # MockReasoningProvider and LLMReasoningProvider
│   │   │   ├── validator.py # ReasoningQualityValidator (evidence & safety checks)
│   │   │   └── service.py   # ReasoningService orchestration
│   │   ├── retrieval/       # Real Moss engine & retrieval abstraction
│   │   │   ├── base.py      # Abstract RetrievalProvider, SearchResult, SearchResponse
│   │   │   ├── ingestion.py # Knowledge normalization & stable ID mapping
│   │   │   ├── index.py     # Explicit Moss index management CLI
│   │   │   ├── moss.py      # Production MossRetrievalProvider
│   │   │   ├── mock.py      # Preserved MockRetrievalProvider for offline CI
│   │   │   └── verify_moss.py # Standalone verification runner for 3 core queries
│   │   ├── safety/          # Deterministic SafetyValidator & policy checks
│   │   └── main.py          # FastAPI application factory & lifecycle
│   │
│   ├── tests/               # Pytest suite (models, retrieval, context, API, integration)
│   ├── requirements.txt     # Production dependencies including moss>=1.13.0
│   └── .env.example         # Environment configuration template
│
├── frontend/                # Next.js 16 + React 19 + Tailwind CSS v4
│   ├── src/
│   │   ├── app/             # App Router (page.tsx, layout.tsx, globals.css)
│   │   ├── components/      # Modular industrial dashboard UI components
│   │   ├── lib/api.ts       # Backend reasoning API client
│   │   └── types/relay.ts   # Strongly-typed domain models
│   └── scripts/             # Automated anti-hardcoding audit script
│
├── knowledge/               # Fictional demo HVAC technical dataset
│   ├── manuals/             # ACX-420 technical manual
│   ├── procedures/          # Troubleshooting guide & E17 SOP
│   ├── safety/              # Pressure safety SOP & LOTO guidelines
│   └── service_history/     # Unit 017 historical work order & maintenance log
│
├── docs/
│   ├── PRD.md               # Product Requirements Document
│   ├── ARCHITECTURE.md      # Detailed system architecture & dataflow
│   └── DEVELOPMENT.md       # Developer setup and testing guide
│
├── README.md                # Project landing overview
└── .gitignore
```

---

## 6. Getting Started

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- macOS / Linux / Windows WSL

### Quick Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your MOSS_PROJECT_ID and MOSS_PROJECT_KEY
   ```

5. **Run the test suite**:
   ```bash
   pytest -v
   ```

6. **Start the backend server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **Test Context Assembly**:
   ```bash
   curl -s -X POST http://localhost:8000/api/context/assemble \
     -H "Content-Type: application/json" \
     -d '{
       "query": "I am getting E17 again on unit 017. Pressure is around 195 PSI.",
       "session_id": "sess-017",
       "top_k": 3
     }' | jq
   ```

---

## 7. License

Internal Hackathon Project — Built for YC Fall 2026 x Moss Sprint.
