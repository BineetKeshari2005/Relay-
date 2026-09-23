# Development Guide: RELAY

**Sprint**: YC Fall 2026 x Moss: The Zero Latency Builder Sprint  
**Target Environment**: macOS / Linux / WSL  
**Phase**: Phase 8 — Final QA, Hardening, Integration Testing & Demo Readiness

---

## 1. Local Environment Setup

### 1.1 Python Backend
Relay uses Python 3.10+ (tested on Python 3.14).

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies including moss
pip install --upgrade pip
pip install -r requirements.txt
```

### 1.2 Configuration
Set your credentials in `backend/.env`:
```ini
ENVIRONMENT=development
LOG_LEVEL=INFO

MOSS_PROJECT_ID=69884154-f51c-4c50-8f8d-49bcb1d7d9ef
MOSS_PROJECT_KEY=<your_moss_project_key>
MOSS_INDEX_NAME=relay-hvac
MOSS_HYBRID_ALPHA=0.8

LLM_PROVIDER=mock
```

### 1.3 Node.js Frontend Setup
Relay uses Next.js 16+ (App Router) with React 19 and Tailwind CSS v4.

```bash
cd frontend

# Install dependencies
npm install

# Verify configuration in frontend/.env.local:
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 2. Running Relay Locally

### 2.1 Start Backend (FastAPI)
```bash
cd backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation is accessible at `http://localhost:8000/docs`.

### 2.2 Start Frontend (Next.js)
```bash
cd frontend
npm run dev -- -p 3000
```
Open `http://localhost:3000` in Chrome/Edge or any Web Speech API-compatible browser to experience voice interaction.

---

## 3. Real-Time Voice Copilot Operations

### 3.1 Voice Query & Audio Playback
1. In the web workspace (`http://localhost:3000`), click the amber **Mic** button in the input composer.
2. Allow browser microphone access when prompted.
3. Speak an equipment issue (e.g. *"High discharge pressure on unit 017"*).
4. The live interim transcript appears in real-time. Upon finishing speech, Relay automatically dispatches the query through the backend reasoning engine (`POST /api/reasoning/analyze`).
5. When the response arrives, the synthesized spoken response begins audio playback automatically. Critical safety warnings are voiced first.
6. The turn badge displays a microphone icon and recording/transcription latency telemetry.
7. Click the **Read Aloud** button on any diagnostic card to replay the spoken response.

### 3.2 Spoken Response API Verification
```bash
curl -s -X POST http://localhost:8000/api/reasoning/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I am getting E17 again on unit 017. Pressure is around 195 PSI.",
    "session_id": "sess-017",
    "asset_id": "ACX-420-017"
  }' | jq '.reasoning.spoken_response'
```

---

## 4. Knowledge Contribution & Ingestion Operations ("Teach Relay")

### 4.1 Submit a Field Contribution via REST API
```bash
curl -s -X POST http://localhost:8000/api/knowledge/contributions \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Condensate P-trap biological blockage causing suction freeze",
    "observation": "Low suction pressure 195 PSI with intermittent coil icing",
    "symptom": "Low suction pressure and freeze-up",
    "suspected_cause": "Algae and sediment accumulation clogging P-trap outlet",
    "action_taken": "Flushed drain line with nitrogen blast and installed cleanout plug",
    "outcome": "Suction pressure stabilized at 215 PSI, drainage verified free",
    "asset_id": "ACX-420-017",
    "session_id": "sess-017"
  }' | jq
```

Response assigns explicit non-authoritative provenance:
```json
{
  "id": "contrib-3a2c986f",
  "title": "Condensate P-trap biological blockage causing suction freeze",
  "provenance_type": "TECHNICIAN_CONTRIBUTION",
  "verification_status": "PENDING_REVIEW"
}
```

### 4.2 List All Ingested Contributions
```bash
curl -s http://localhost:8000/api/knowledge/contributions | jq
```

---

## 5. Frontend Audits and Quality Checks

### 5.1 Anti-Hardcoding Audit
Verifies that no query matching logic or hardcoded Q&A tables exist in the frontend UI:
```bash
cd frontend
npm run audit
```

### 5.2 Production Build
```bash
cd frontend
npm run build
```

---

## 6. Running Automated Backend Tests

Run the full pytest suite (all 105 unit, integration, contract, resilience, contribution, and voice tests):
```bash
cd backend
.venv/bin/pytest -v
```

Run Integration Flow tests (E17, vibration, vague, no-evidence, contributions):
```bash
cd backend
.venv/bin/pytest tests/test_integration_flows.py -v
```

Run API Contract tests:
```bash
cd backend
.venv/bin/pytest tests/test_api_contracts.py -v
```

Run Failure Simulation & Resilience tests:
```bash
cd backend
.venv/bin/pytest tests/test_resilience_and_failures.py -v
```

Run Voice Hardening & Regression tests:
```bash
cd backend
.venv/bin/pytest tests/test_voice_hardening.py -v
```

Run Knowledge Contribution & Ingestion tests:
```bash
cd backend
.venv/bin/pytest tests/test_contributions.py -v
```

Run Reasoning Engine tests:
```bash
cd backend
.venv/bin/pytest tests/test_reasoning.py -v
```

