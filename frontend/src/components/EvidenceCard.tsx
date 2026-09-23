"use client";

import React, { useState } from "react";
import { BookOpen, Check, FileCheck, Layers, ChevronDown, ChevronUp, Quote } from "lucide-react";
import { EvidenceClaim, ReasoningCitation, SupportLevel } from "@/types/relay";

interface EvidenceCardProps {
  claims: EvidenceClaim[];
  citations: ReasoningCitation[];
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ claims, citations }) => {
  const [activeTab, setActiveTab] = useState<"claims" | "citations">("claims");
  const [expandedCitation, setExpandedCitation] = useState<string | null>(null);

  const getSupportBadge = (level: SupportLevel) => {
    switch (level) {
      case "direct":
        return {
          label: "DIRECT SUPPORT",
          classes: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
        };
      case "inferred":
        return {
          label: "INFERRED",
          classes: "bg-amber-500/10 text-amber-400 border-amber-500/30",
        };
      case "insufficient":
        return {
          label: "INSUFFICIENT",
          classes: "bg-rose-500/10 text-rose-400 border-rose-500/30",
        };
      default:
        return {
          label: level,
          classes: "bg-zinc-800 text-zinc-400 border-zinc-700",
        };
    }
  };

  const toggleCitation = (id: string) => {
    setExpandedCitation(expandedCitation === id ? null : id);
  };

  return (
    <div className="bg-zinc-900/90 border border-zinc-800 rounded-lg p-4 space-y-4">
      {/* Header and Tab Selector */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-cyan-400" />
          <h3 className="font-mono font-bold text-sm text-zinc-100 uppercase tracking-wide">
            Grounding &amp; Technical Evidence
          </h3>
        </div>

        <div className="flex bg-zinc-950 p-0.5 rounded border border-zinc-800 text-xs font-mono">
          <button
            type="button"
            onClick={() => setActiveTab("claims")}
            className={`px-3 py-1 rounded transition-colors ${
              activeTab === "claims"
                ? "bg-zinc-800 text-zinc-100 font-semibold"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            Claims ({claims.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("citations")}
            className={`px-3 py-1 rounded transition-colors ${
              activeTab === "citations"
                ? "bg-zinc-800 text-zinc-100 font-semibold"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            Citations ({citations.length})
          </button>
        </div>
      </div>

      {/* Claims Tab Content */}
      {activeTab === "claims" && (
        <div className="space-y-2.5">
          {claims.length === 0 ? (
            <p className="text-xs text-zinc-500 font-mono py-2 text-center">
              No evidence claims registered for this turn.
            </p>
          ) : (
            claims.map((claim, idx) => {
              const badge = getSupportBadge(claim.support_level);
              return (
                <div
                  key={idx}
                  className="bg-black/30 border border-zinc-800/80 rounded-md p-3 space-y-1.5"
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-xs text-zinc-200 font-medium leading-relaxed">
                      {claim.claim}
                    </p>
                    <span
                      className={`text-[9px] font-mono px-2 py-0.5 rounded border shrink-0 font-bold tracking-wider ${badge.classes}`}
                    >
                      {badge.label}
                    </span>
                  </div>

                  {claim.explanation && (
                    <p className="text-[11px] text-zinc-400 font-mono">
                      <span className="text-zinc-600 uppercase mr-1">Rationale:</span>
                      {claim.explanation}
                    </p>
                  )}

                  {claim.evidence_ids.length > 0 && (
                    <div className="flex items-center gap-1.5 pt-1">
                      <span className="text-[10px] text-zinc-600 font-mono">Sources:</span>
                      {claim.evidence_ids.map((id) => (
                        <span
                          key={id}
                          className="bg-zinc-900 text-zinc-400 text-[10px] font-mono px-1.5 py-0.2 rounded border border-zinc-800"
                        >
                          {id}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Citations Tab Content */}
      {activeTab === "citations" && (
        <div className="space-y-2.5">
          {citations.length === 0 ? (
            <p className="text-xs text-zinc-500 font-mono py-2 text-center">
              No citations generated.
            </p>
          ) : (
            citations.map((cite, idx) => {
              const isExpanded = expandedCitation === cite.evidence_id;
              return (
                <div
                  key={idx}
                  className="bg-black/30 border border-zinc-800/80 rounded-md p-3 space-y-2"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs font-semibold text-zinc-200">
                          {cite.source}
                        </span>
                        <span className="text-[10px] font-mono bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded border border-zinc-700 uppercase">
                          {cite.document_type}
                        </span>

                        {/* Provenance Badge */}
                        {(cite.provenance_type === "TECHNICIAN_CONTRIBUTION" ||
                          cite.metadata?.provenance_type === "TECHNICIAN_CONTRIBUTION" ||
                          cite.document_type === "technician_contribution") && (
                          <span className="text-[9px] font-mono bg-amber-950/60 text-amber-300 border border-amber-500/40 px-1.5 py-0.5 rounded font-bold uppercase tracking-wider">
                            Technician Contribution
                          </span>
                        )}

                        {/* Verification Status Badge */}
                        {(cite.verification_status === "PENDING_REVIEW" ||
                          cite.metadata?.verification_status === "PENDING_REVIEW") && (
                          <span className="text-[9px] font-mono bg-amber-500/20 text-amber-400 border border-amber-500/50 px-1.5 py-0.5 rounded font-bold uppercase tracking-wider">
                            Pending Review
                          </span>
                        )}

                        {(cite.provenance_type === "VERIFIED_COMPANY_DOCUMENT" ||
                          cite.metadata?.provenance_type === "VERIFIED_COMPANY_DOCUMENT") && (
                          <span className="text-[9px] font-mono bg-emerald-950/60 text-emerald-300 border border-emerald-500/40 px-1.5 py-0.5 rounded uppercase">
                            Verified Company Doc
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] font-mono text-cyan-400/90 block mt-0.5">
                        ID: {cite.evidence_id}
                        {cite.score !== null && cite.score !== undefined && (
                          <span className="ml-2 text-zinc-500">
                            Relevance: {(cite.score * 100).toFixed(1)}%
                          </span>
                        )}
                      </span>
                    </div>

                    <button
                      type="button"
                      onClick={() => toggleCitation(cite.evidence_id)}
                      className="text-zinc-500 hover:text-zinc-300 p-1"
                      aria-label="Toggle Excerpt"
                    >
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </button>
                  </div>

                  {/* Excerpt Display */}
                  <div
                    className={`bg-zinc-950/80 rounded border ${
                      cite.provenance_type === "TECHNICIAN_CONTRIBUTION" ||
                      cite.metadata?.provenance_type === "TECHNICIAN_CONTRIBUTION" ||
                      cite.document_type === "technician_contribution"
                        ? "border-amber-500/40 bg-amber-950/10"
                        : "border-zinc-800/60"
                    } p-2.5 text-xs text-zinc-300 font-mono ${
                      !isExpanded ? "line-clamp-2" : ""
                    }`}
                  >
                    <div className="flex items-start gap-1.5">
                      <Quote className="w-3 h-3 text-zinc-600 shrink-0 mt-0.5" />
                      <span>{cite.relevant_excerpt}</span>
                    </div>
                  </div>

                  {(cite.provenance_type === "TECHNICIAN_CONTRIBUTION" ||
                    cite.metadata?.provenance_type === "TECHNICIAN_CONTRIBUTION" ||
                    cite.document_type === "technician_contribution") && (
                    <div className="text-[10px] font-mono text-amber-400/90 flex items-center gap-1.5 px-1">
                      <span>⚠️ Note: Field observation pending review. Non-authoritative contextual reference.</span>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
};
