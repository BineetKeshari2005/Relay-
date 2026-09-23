"use client";

import React, { useState } from "react";
import { X, BookOpen, Quote, ShieldCheck, HelpCircle } from "lucide-react";
import { EvidenceClaim, ReasoningCitation } from "@/types/relay";
import { ProvenanceBadge } from "./ProvenanceBadge";

interface WhyThisAnswerModalProps {
  isOpen: boolean;
  onClose: () => void;
  claims: EvidenceClaim[];
  citations: ReasoningCitation[];
  issueSummary?: string;
}

export const WhyThisAnswerModal: React.FC<WhyThisAnswerModalProps> = ({
  isOpen,
  onClose,
  claims,
  citations,
  issueSummary,
}) => {
  const [activeTab, setActiveTab] = useState<"citations" | "claims">("citations");

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <BookOpen className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-base text-slate-900">
                Why this answer?
              </h3>
              <p className="text-xs text-slate-500">
                Grounding evidence and retrieved citations powering Relay&apos;s recommendations
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="px-6 pt-3 border-b border-slate-200 flex gap-4 text-xs font-medium">
          <button
            type="button"
            onClick={() => setActiveTab("citations")}
            className={`pb-2.5 border-b-2 transition-colors cursor-pointer ${
              activeTab === "citations"
                ? "border-blue-600 text-blue-600 font-semibold"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            Retrieved Sources ({citations.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("claims")}
            className={`pb-2.5 border-b-2 transition-colors cursor-pointer ${
              activeTab === "claims"
                ? "border-blue-600 text-blue-600 font-semibold"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            Fact Claims ({claims.length})
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-3.5">
          {activeTab === "citations" && (
            <div className="space-y-3">
              {citations.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-6">
                  No citations available for this response.
                </p>
              ) : (
                citations.map((cite, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-slate-900">
                          {cite.source}
                        </span>
                        <span className="text-[11px] font-mono text-slate-500 uppercase bg-slate-200/70 px-1.5 py-0.5 rounded">
                          {cite.document_type}
                        </span>
                      </div>
                      <ProvenanceBadge
                        type={cite.provenance_type || (cite.metadata as any)?.provenance_type}
                        status={cite.verification_status || (cite.metadata as any)?.verification_status}
                      />
                    </div>

                    {/* Excerpt */}
                    <div className="bg-white border border-slate-200/90 rounded-lg p-3 text-xs text-slate-700 leading-relaxed font-mono flex items-start gap-2">
                      <Quote className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                      <span>{cite.relevant_excerpt}</span>
                    </div>

                    <div className="text-[10px] text-slate-500 font-mono flex items-center justify-between">
                      <span>Doc ID: {cite.evidence_id}</span>
                      {cite.score !== null && cite.score !== undefined && (
                        <span>Relevance: {(cite.score * 100).toFixed(0)}%</span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === "claims" && (
            <div className="space-y-3">
              {claims.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-6">
                  No individual claims recorded.
                </p>
              ) : (
                claims.map((claim, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-1.5"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs sm:text-sm font-medium text-slate-800">
                        {claim.claim}
                      </p>
                      <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200 shrink-0">
                        {claim.support_level}
                      </span>
                    </div>
                    {claim.explanation && (
                      <p className="text-xs text-slate-500">{claim.explanation}</p>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-slate-200 bg-slate-50/50 flex justify-end rounded-b-2xl">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
