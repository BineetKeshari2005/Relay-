"""Context Assembler service coordinating retrieval, structured assets, and evidence classification."""

from typing import Any, Dict, List, Optional

from app.context.assembled_context import (
    AssembledContext,
    DetectedConflict,
    EvidenceClassification,
    EvidenceItem,
    ExtractedQueryFacts,
    RetrievalMetadata,
    SafetyContext,
    SafetyWarningItem,
    UncertaintyModel,
)
from app.context.query_extractor import QueryContextExtractor
from app.data.demo_fixtures import (
    get_demo_asset,
    get_demo_service_records,
    get_demo_session,
    get_demo_turns,
)
from app.models.asset import Asset
from app.models.service_record import ServiceRecord
from app.models.session import ConversationTurn
from app.retrieval.base import RetrievalProvider, SearchResponse


class ContextAssembler:
    """
    Coordinates gathering and normalizing all context elements into an AssembledContext.

    Separation of Concerns:
    - Uses RetrievalProvider abstraction (never calls Moss SDK directly).
    - Produces a structured 'case file' with facts, evidence, and uncertainty.
    - NEVER performs diagnosis, root cause reasoning, or solution recommendations.
    """

    def __init__(
        self,
        retrieval_provider: RetrievalProvider,
        query_extractor: Optional[QueryContextExtractor] = None,
    ):
        self.retrieval_provider = retrieval_provider
        self.query_extractor = query_extractor or QueryContextExtractor()

    def classify_evidence(self, doc_type: str, safety_level: Optional[str]) -> EvidenceClassification:
        """Deterministically map document metadata to an EvidenceClassification."""
        dt = (doc_type or "").lower().strip()
        sl = (safety_level or "").lower().strip()

        if "contribution" in dt or "technician" in dt:
            return "technician_contribution"
        elif "service_record" in dt:
            return "service_history"
        elif "maintenance" in dt:
            return "maintenance_history"
        elif "safety" in dt or sl == "critical":
            return "safety_procedure"
        elif "procedure" in dt or "troubleshoot" in dt:
            return "troubleshooting"
        elif "manual" in dt or "spec" in dt:
            return "technical_manual"
        else:
            return "general_reference"

    def resolve_asset(
        self,
        explicit_asset_id: Optional[str],
        extracted_facts: ExtractedQueryFacts,
    ) -> tuple[Optional[Asset], Optional[str], bool]:
        """
        Resolve equipment asset using explicit IDs or extracted query facts.
        Returns: (Asset instance or None, resolved asset_id or None, is_resolved boolean)
        """
        candidate_id = explicit_asset_id

        # If not explicitly passed, try exact match from extracted query
        if not candidate_id and extracted_facts.asset_reference:
            ref = extracted_facts.asset_reference.lower()
            if "017" in ref:
                candidate_id = "ACX-420-017"

        if candidate_id:
            asset = get_demo_asset(candidate_id)
            if asset:
                return asset, candidate_id, True

        return None, None, False

    def detect_conflicts(self, evidence: List[EvidenceItem]) -> List[DetectedConflict]:
        """Detect version disparities or contradictory specifications across evidence."""
        conflicts: List[DetectedConflict] = []
        import re

        # Group documents by base document identifier/source (stripping version suffixes like _v1, -v2, etc.)
        docs_by_base: Dict[str, Dict[str, List[str]]] = {}
        for item in evidence:
            doc_id = item.document_id
            ver = item.version
            if ver:
                src = (item.source or item.document_id).lower().replace(".md", "")
                base_name = re.sub(r"[-_]v\d+.*$", "", src)
                docs_by_base.setdefault(base_name, {}).setdefault(ver, []).append(doc_id)

        for base_name, version_map in docs_by_base.items():
            if len(version_map) > 1:
                sources_summary = [f"{v}: {', '.join(docs)}" for v, docs in version_map.items()]
                all_sources = [doc for docs in version_map.values() for doc in docs]
                conflicts.append(
                    DetectedConflict(
                        conflict_type="version_mismatch",
                        sources=all_sources,
                        description=f"Multiple conflicting versions retrieved for {base_name} ({'; '.join(sources_summary)}).",
                    )
                )

        return conflicts

    async def assemble(
        self,
        query: str,
        asset_id: Optional[str] = None,
        session_id: Optional[str] = None,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> AssembledContext:
        """
        Build the unified AssembledContext case file for a technician interaction.
        """
        # 1. Deterministic Query Fact Extraction
        facts = self.query_extractor.extract(query)

        # 2. Asset Resolution
        asset, resolved_asset_id, asset_is_resolved = self.resolve_asset(asset_id, facts)
        resolved_model = asset.model if asset else facts.asset_model

        # 3. Resolve Active Error Code and Measurements
        error_code = facts.error_code
        measurements: Dict[str, Any] = dict(facts.measurements)
        measurement_provenance: Dict[str, str] = {
            k: "technician_query" for k in facts.measurements.keys()
        }

        # 4. Load Conversation Context & Session History if available
        recent_turns: List[ConversationTurn] = []
        structured_service_history: List[ServiceRecord] = []

        if session_id:
            session = get_demo_session(session_id)
            if session:
                # Merge session measurements
                if session.current_measurements:
                    for k, v in session.current_measurements.items():
                        if k not in measurements:
                            measurements[k] = v
                            measurement_provenance[k] = f"session_telemetry:{session_id}"
                if not error_code and session.current_error_code:
                    error_code = session.current_error_code
                if not resolved_asset_id and session.asset_id:
                    asset, resolved_asset_id, asset_is_resolved = self.resolve_asset(session.asset_id, facts)
            recent_turns = get_demo_turns(session_id)

        # Load structured asset service history if asset is known
        if resolved_asset_id:
            structured_service_history = get_demo_service_records(resolved_asset_id)

        # 5. Execute Knowledge Retrieval via Decoupled Provider
        search_filters: Dict[str, Any] = dict(filters or {})
        if resolved_model and "asset_model" not in search_filters:
            search_filters["asset_model"] = resolved_model
        if error_code and "error_code" not in search_filters:
            search_filters["error_code"] = error_code

        # If filters are too restrictive and yield no docs, provider handles it
        search_resp: SearchResponse = await self.retrieval_provider.search(
            query=query,
            filters=search_filters if search_filters else None,
            limit=top_k,
        )

        # Fallback to broader search if filtered search returned 0 results
        if search_resp.total_count == 0 and search_filters:
            search_resp = await self.retrieval_provider.search(
                query=query,
                filters=None,
                limit=top_k,
            )

        # 6. Transform and Classify Evidence Items
        evidence_items: List[EvidenceItem] = []
        safety_docs: List[str] = []
        safety_evidence_ids: List[str] = []
        highest_safety = "standard"

        for res in search_resp.results:
            doc_type = res.metadata.get("document_type", res.source)
            safety_level = res.metadata.get("safety_level", "standard")
            classification = self.classify_evidence(doc_type, safety_level)

            # Check safety severity
            if safety_level == "critical":
                highest_safety = "critical"
            elif safety_level in ["high_pressure", "warning"] and highest_safety != "critical":
                highest_safety = "warning"

            if classification == "safety_procedure" or safety_level in ["critical", "high_pressure"]:
                safety_docs.append(res.chunk_id)
                safety_evidence_ids.append(res.chunk_id)

            applicability = {
                "matches_error_code": res.metadata.get("error_code") == error_code if error_code else False,
                "matches_model": res.metadata.get("asset_model") == resolved_model if resolved_model else False,
                "matches_asset": res.metadata.get("asset_id") == resolved_asset_id if resolved_asset_id else False,
            }

            provenance_type = getattr(res, "provenance_type", None) or res.metadata.get("provenance_type", "VERIFIED_COMPANY_DOCUMENT")
            verification_status = getattr(res, "verification_status", None) or res.metadata.get("verification_status", "VERIFIED")
            is_tech_contrib = (
                provenance_type == "TECHNICIAN_CONTRIBUTION"
                or classification == "technician_contribution"
                or "contrib" in res.chunk_id.lower()
            )

            evidence_items.append(
                EvidenceItem(
                    document_id=res.chunk_id,
                    source=res.metadata.get("source", res.title),
                    document_type=doc_type,
                    classification=classification,
                    text=res.content,
                    score=res.score,
                    metadata=res.metadata,
                    safety_level=safety_level,
                    version=res.metadata.get("version"),
                    date=res.metadata.get("date"),
                    applicability=applicability,
                    provenance_type=provenance_type,
                    verification_status=verification_status,
                    is_technician_contribution=is_tech_contrib,
                )
            )

        # 7. Assemble Safety Context with Grounded Threshold Provenance
        safety_warnings: List[str] = []
        warning_items: List[SafetyWarningItem] = []
        threshold_sources: Dict[str, str] = {}
        has_pressure_hazard = False
        mandatory_loto = False
        unverified_safety_threshold = False

        # Identify relevant retrieved safety/procedure documents for grounding
        e17_sop = next(
            (e for e in evidence_items if e.document_id == "e17-troubleshooting" or "e17" in e.document_id.lower()),
            None,
        )
        pressure_sop = next(
            (e for e in evidence_items if e.document_id == "pressure-safety-sop" or "pressure" in e.document_id.lower()),
            None,
        )

        if "pressure_psi" in measurements:
            try:
                pval = float(measurements["pressure_psi"])
                # Emergency pressure threshold (> 250 PSI from pressure-safety-sop)
                if pval > 250.0:
                    has_pressure_hazard = True
                    mandatory_loto = True
                    msg = (
                        f"Emergency discharge pressure detected ({pval} PSI > 250 PSI threshold). "
                        "Immediate shutdown, system isolation, and depressurization required before any technician contact."
                    )
                    safety_warnings.append(msg)
                    warning_items.append(
                        SafetyWarningItem(
                            warning=msg,
                            provenance_type="VERIFIED_FROM_KNOWLEDGE" if pressure_sop else "DEMO_RULE",
                            source_document_id="pressure-safety-sop" if pressure_sop else None,
                            source_reference="SOP-SAFE-PRESS-01 Section 3" if pressure_sop else None,
                            threshold_applied=f"emergency_pressure > 250.0 PSI (measured: {pval} PSI)",
                        )
                    )
                    threshold_sources["pressure_psi"] = "pressure-safety-sop (SOP-SAFE-PRESS-01 Section 3: >250 PSI)"

                elif pval > 190.0:
                    # Elevated discharge pressure (> 190 PSI)
                    has_pressure_hazard = True
                    mandatory_loto = True
                    msg = (
                        f"Elevated discharge pressure detected ({pval} PSI). "
                        "Mandatory Lockout/Tagout (LOTO) and compressor de-energization required before physical coil inspection."
                    )
                    safety_warnings.append(msg)
                    if e17_sop or error_code == "E17":
                        warning_items.append(
                            SafetyWarningItem(
                                warning=msg,
                                provenance_type="VERIFIED_FROM_KNOWLEDGE",
                                source_document_id="e17-troubleshooting",
                                source_reference="SOP-ACX420-E17 Rev 3.0 Step 3",
                                threshold_applied=f"discharge_pressure > 190.0 PSI (measured: {pval} PSI)",
                            )
                        )
                        threshold_sources["pressure_psi"] = "e17-troubleshooting (SOP-ACX420-E17 Rev 3.0 Step 3: >190 PSI)"
                    else:
                        # Evaluated without a verified knowledge threshold for this equipment/issue
                        warning_items.append(
                            SafetyWarningItem(
                                warning=msg,
                                provenance_type="DEMO_RULE",
                                source_document_id=None,
                                source_reference=None,
                                threshold_applied=f"generic_heuristic > 190.0 PSI (measured: {pval} PSI)",
                            )
                        )
                        unverified_safety_threshold = True

                else:
                    # Pressure is <= 190 PSI (within normal operating band 160-185 PSI or slightly above)
                    # If pressure is present on an asset where no document provides a threshold
                    if not e17_sop and error_code != "E17" and not any(e.classification == "technical_manual" for e in evidence_items):
                        unverified_safety_threshold = True
                        warning_items.append(
                            SafetyWarningItem(
                                warning=f"Pressure reading present ({pval} PSI); no verified threshold available in current knowledge base.",
                                provenance_type="DEMO_RULE",
                                source_document_id=None,
                                source_reference=None,
                                threshold_applied="none",
                            )
                        )
            except (ValueError, TypeError):
                pass

        for item in evidence_items:
            if item.classification == "safety_procedure":
                mandatory_loto = True
                if not any(w.source_document_id == item.document_id for w in warning_items):
                    warning_items.append(
                        SafetyWarningItem(
                            warning=f"Safety procedure identified: {item.document_id}. Adhere to safety precautions.",
                            provenance_type="VERIFIED_FROM_KNOWLEDGE",
                            source_document_id=item.document_id,
                            source_reference=item.source,
                            threshold_applied=None,
                        )
                    )

        safety_ctx = SafetyContext(
            safety_level=highest_safety,
            safety_documents=list(set(safety_docs)),
            safety_warnings=safety_warnings,
            warning_items=warning_items,
            threshold_sources=threshold_sources,
            safety_evidence_ids=list(set(safety_evidence_ids)),
            mandatory_loto=mandatory_loto,
            high_pressure_hazard=has_pressure_hazard,
        )

        # 8. Missing Information Detection
        missing_info: List[str] = []
        if not asset_is_resolved:
            missing_info.append("exact equipment asset identifier (e.g. ACX-420-017)")
        if not error_code:
            missing_info.append("specific diagnostic trouble code (e.g. E17)")
        if error_code == "E17" and "pressure_psi" not in measurements:
            missing_info.append("current physical discharge pressure reading (PSI)")

        # 9. Uncertainty Evaluation
        uncertainty = UncertaintyModel(
            missing_asset=not asset_is_resolved,
            missing_error_code=not bool(error_code),
            missing_measurement="pressure_psi" not in measurements if error_code == "E17" else False,
            insufficient_evidence=len(evidence_items) == 0,
            conflicting_evidence=False,
            ambiguous_query=len(query.strip()) < 10 or (not error_code and not measurements),
            stale_history=False,
            unresolved_asset_reference=facts.asset_reference if not asset_is_resolved else None,
            unverified_safety_threshold=unverified_safety_threshold,
        )

        # 10. Conflict Detection
        conflicts = self.detect_conflicts(evidence_items)
        if conflicts:
            uncertainty.conflicting_evidence = True

        # 11. Assemble Retrieval Metadata
        retrieval_meta = RetrievalMetadata(
            provider=search_resp.provider,
            status="ready",
            latency_ms=search_resp.latency_ms if search_resp.latency_ms is not None else 0.0,
            result_count=len(evidence_items),
            query=query,
        )

        return AssembledContext(
            session_id=session_id,
            technician_query=query,
            query_facts=facts,
            asset=asset,
            asset_id=resolved_asset_id,
            asset_model=resolved_model,
            error_code=error_code,
            measurements=measurements,
            measurement_provenance=measurement_provenance,
            observations=facts.observations,
            relevant_service_history=structured_service_history,
            conversation_context=recent_turns,
            evidence=evidence_items,
            safety_context=safety_ctx,
            uncertainty=uncertainty,
            missing_information=missing_info,
            conflicts=conflicts,
            retrieval_metadata=retrieval_meta,
        )
