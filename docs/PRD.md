# Product Requirements Document (PRD): RELAY

**Project**: Relay — Real-Time AI Decision-Support Copilot for Field Technicians  
**Competition**: YC Fall 2026 x Moss: The Zero Latency Builder Sprint  
**Track**: Real-Time Voice & Conversational AI (Primary) | Agent Reliability, Security & Evaluation (Secondary)  
**Phase**: Phase 1 (Foundation & Core Architecture)

---

## 1. Executive Summary

Field service technicians responsible for complex physical systems (commercial HVAC, industrial refrigeration, elevators, power distribution) routinely encounter high-stress, dangerous diagnostic situations. When a system trips with an error code, technicians must juggle live electrical probes, pressure gauges, and physical tools while attempting to search hundreds of pages of equipment manuals, wiring schematics, and fragmented past service tickets.

**Relay** is an ambient, voice-first decision-support copilot. A technician communicates hands-free in natural speech while working on equipment. Relay synthesizes live diagnostic measurements with verified technical manuals, historical repair records, and safety standard operating procedures (SOPs) retrieved with sub-100ms latency via **Moss**. Relay reasons over this grounded evidence, validates safety through strict deterministic policies, and delivers concise, step-by-step diagnostic actions.

---

## 2. Target Users & Personas

### Primary Persona: Dave Miller — Senior Commercial HVAC Field Technician
- **Context**: Dispatched to rooftop units and mechanical penthouses, wearing thick leather gloves, safety glasses, and ear protection. Carrying a tablet or smartphone in a holster and wireless Bluetooth earbud.
- **Pain Points**:
  - Stopping physical work to look up error codes on a small touch screen in direct sunlight is tedious and dangerous.
  - Prior repair history on specific rooftop units is locked in distant enterprise ERP/CRM systems.
  - Generic chatbots invent pinouts, torque values, or pressure thresholds that can blow a seal or trigger an arc flash.
- **Needs**:
  - Completely hands-free, low-latency audio interaction.
  - Accurate, equipment-specific answers grounded in the exact unit manual and service history.
  - Zero hallucination of safety-critical parameters.

### Secondary Persona: Facilities & Safety Director
- **Needs**: Guaranteed adherence to Lockout/Tagout (LOTO) protocols, auditability of diagnostic advice, reduced truck rolls, and protection against catastrophic equipment damage.

---

## 3. Core Product Principles

1. **Grounded Truth Over Generation**: Relay must **NEVER** invent technical specifications, safety limits, wiring diagrams, or diagnostic procedures. If verified evidence is missing, Relay must explicitly state its uncertainty and guide the technician to a safe measurement or escalation step.
2. **Deterministic Safety Authority**: The LLM is never the final authority on physical safety. Safety boundaries (e.g. pressure cutouts, high voltage verification, PPE requirements) are enforced by a separate deterministic safety validation layer.
3. **Retrieval in the Critical Path**: Moss is not an offline indexing utility; it is the core real-time retrieval engine operating under 100ms in the live conversational loop.
4. **Hands-Free Speed**: Latency must stay low enough to support conversational turn-taking without awkward pauses.

---

## 4. Core User Workflow

```
[Technician on site]
         │
         ▼
"I'm getting E17 again on unit 017. Pressure is around 195 PSI."
         │
         ▼
[LiveKit Audio Streaming & ASR]
         │
         ▼
[Relay Intent & Context Extractor]
- Asset: CoolCore ACX-420-017
- Error: E17 (High-Pressure Protection)
- Measurement: 195 PSI
         │
         ▼
[Moss Real-Time Retrieval (<100ms)]
- Filters: {asset_model: "ACX-420", error_code: "E17", asset_id: "ACX-420-017"}
- Retrieved Chunks: E17 SOP, Unit 017 Service History, Pressure Safety SOP
         │
         ▼
[Relay Reasoner]
- Correlates prior PT-1 sensor replacement with current elevated pressure
- Identifies airflow restriction / coil fouling as primary hypothesis
         │
         ▼
[Deterministic Safety Validator]
- Checks 195 PSI threshold (safe to inspect, but requires compressor shutdown)
- Verifies LOTO mandate
         │
         ▼
[Concise Audio & Visual Delivery]
"Issue: E17 high-pressure protection.
Likely Cause: Potential condenser airflow restriction.
Why: Unit 017 had sensor PT-1 replaced in August; coils foul quickly from the nearby vent.
Safety: Shut down the compressor before physical inspection.
Next Step: Verify shutdown, then check condenser coil face for dust blockage."
```

---

## 5. Feature Scope

### Phase 1: Foundation (Current)
- Modular backend architecture with FastAPI.
- Core data models: `Asset`, `ServiceRecord`, `KnowledgeDocument`, `TechnicianSession`, `ConversationTurn`.
- Unified `Context` and `ContextBuilder` abstraction.
- Decoupled `RetrievalProvider` with `MossRetrievalProvider` boundary and deterministic `MockRetrievalProvider`.
- Decoupled `LLMProvider` interface with local mock.
- Deterministic `SafetyValidator` with evidence-grounding and high-pressure checks.
- Realistic fictional HVAC dataset (CoolCore ACX-420, Unit 017).
- Health, version, and demo inspection endpoints.
- Full test suite with 100% deterministic coverage.

### Phase 2: Intelligence & Voice Integration (Next)
- Real-time voice agent pipeline using LiveKit Agents.
- Integration with live Moss API project index.
- Multi-step structured diagnostic reasoning engine.
- Session state persistence in SQLite.

### Phase 3: Technician Interface (Future)
- Mobile-optimized Next.js web application for field tablets/phones.
- Live audio visualizer and diagnostic summary cards.
- Interactive branching decision trees with one-tap confirmations.

---

## 6. Success Metrics & Hackathon Criteria

| Metric | Target | Rationale |
|---|---|---|
| **Retrieval Latency** | < 100ms via Moss | Enables seamless conversational turn-taking |
| **Safety Violation Rate** | 0.0% | Deterministic validator blocks unverified advice |
| **Evidence Grounding** | 100% of advice linked to retrieved doc | Eliminates technical hallucinations |
| **First-Time Fix Rate** | Measurable acceleration in demo flow | Demonstrates ROI for industrial field service |
