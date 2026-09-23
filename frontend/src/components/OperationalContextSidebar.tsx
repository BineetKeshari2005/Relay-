"use client";

import React, { useState } from "react";
import {
  Activity,
  Layers,
  FileText,
  Clock,
  ChevronDown,
  ChevronUp,
  Cpu,
  History,
  Tag,
  AlertCircle,
} from "lucide-react";
import { AssembledContext, EvidenceItem } from "@/types/relay";

interface OperationalContextSidebarProps {
  context?: AssembledContext | null;
}

export const OperationalContextSidebar: React.FC<OperationalContextSidebarProps> = ({
  context,
}) => {
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);

  if (!context) {
    return (
      <aside className="bg-zinc-950/80 border border-zinc-800 rounded-xl p-4 text-xs font-mono text-zinc-500 h-full flex flex-col items-center justify-center text-center space-y-2">
        <Activity className="w-8 h-8 text-zinc-700" />
        <p className="text-zinc-400 font-medium">Awaiting Operational Context</p>
        <p className="text-[11px] text-zinc-600 max-w-xs">
          Transmit a technician query to inspect live sensor readings, Moss retrieval chunks, and asset telemetry.
        </p>
      </aside>
    );
  }

  const toggleDoc = (id: string) => {
    setExpandedDoc(expandedDoc === id ? null : id);
  };

  return (
    <aside className="bg-zinc-950/90 border border-zinc-800 rounded-xl p-4 space-y-5 overflow-y-auto max-h-[calc(100vh-140px)]">
      {/* Sidebar Header */}
      <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-amber-400" />
          <h3 className="font-mono font-bold text-xs uppercase tracking-wider text-zinc-200">
            Operational Context
          </h3>
        </div>
        <span className="text-[10px] font-mono text-zinc-500 bg-zinc-900 px-2 py-0.5 rounded border border-zinc-800">
          MOSS CHUNKS: {context.evidence.length}
        </span>
      </div>

      {/* Asset Specifications */}
      <div className="space-y-2">
        <span className="text-[10px] font-mono uppercase text-zinc-500 tracking-wider block">
          Asset Specification
        </span>
        <div className="bg-zinc-900/80 border border-zinc-800 rounded-lg p-3 text-xs font-mono space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-zinc-500">Asset ID:</span>
            <span className="text-zinc-200 font-semibold">{context.asset_id || "Unresolved"}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-zinc-500">Model:</span>
            <span className="text-zinc-200">{context.asset_model || "Unknown"}</span>
          </div>
          {context.asset?.location && (
            <div className="flex items-center justify-between">
              <span className="text-zinc-500">Location:</span>
              <span className="text-zinc-300">{context.asset.location}</span>
            </div>
          )}
          {context.error_code && (
            <div className="flex items-center justify-between pt-1 border-t border-zinc-800">
              <span className="text-amber-400 font-bold">Active DTC:</span>
              <span className="bg-amber-500/20 text-amber-300 border border-amber-500/30 px-1.5 py-0.2 rounded font-bold">
                {context.error_code}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Live Measurements & Provenance Tracking */}
      <div className="space-y-2">
        <span className="text-[10px] font-mono uppercase text-zinc-500 tracking-wider block">
          Telemetry &amp; Provenance
        </span>
        {Object.keys(context.measurements).length === 0 ? (
          <p className="text-[11px] font-mono text-zinc-600 bg-zinc-900/50 p-2.5 rounded border border-zinc-800">
            No numerical measurements recorded for this turn.
          </p>
        ) : (
          <div className="space-y-1.5">
            {Object.entries(context.measurements).map(([key, val]) => {
              const origin = context.measurement_provenance[key] || "untracked";
              const isQuery = origin === "technician_query";
              return (
                <div
                  key={key}
                  className="bg-black/40 border border-zinc-800/80 rounded p-2 text-xs font-mono space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-400 capitalize">
                      {key.replace("_", " ")}:
                    </span>
                    <span className="text-emerald-400 font-bold">
                      {typeof val === "number" ? val.toFixed(1) : String(val)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-zinc-500 pt-0.5">
                    <span>Provenance:</span>
                    <span
                      className={`px-1 rounded border text-[9px] uppercase ${
                        isQuery
                          ? "bg-blue-950 text-blue-300 border-blue-800"
                          : "bg-zinc-800 text-zinc-300 border-zinc-700"
                      }`}
                    >
                      {isQuery ? "technician query" : origin}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Historical Work Orders */}
      {context.relevant_service_history.length > 0 && (
        <div className="space-y-2">
          <span className="text-[10px] font-mono uppercase text-zinc-500 tracking-wider block flex items-center gap-1">
            <History className="w-3 h-3" />
            Service History ({context.relevant_service_history.length})
          </span>
          <div className="space-y-1.5">
            {context.relevant_service_history.map((rec, i) => (
              <div
                key={i}
                className="bg-zinc-900/70 border border-zinc-800 rounded p-2 text-xs font-mono space-y-1"
              >
                <div className="flex items-center justify-between text-zinc-400">
                  <span className="font-semibold text-zinc-200">{rec.record_id}</span>
                  <span className="text-[10px]">{rec.date}</span>
                </div>
                <p className="text-[11px] text-zinc-300 line-clamp-2">
                  {rec.description || rec.summary}
                </p>
                {rec.error_code && (
                  <span className="text-[9px] bg-zinc-800 text-zinc-400 px-1 rounded inline-block">
                    DTC: {rec.error_code}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Retrieved Moss Knowledge Chunks */}
      <div className="space-y-2">
        <span className="text-[10px] font-mono uppercase text-cyan-400/90 tracking-wider block flex items-center gap-1">
          <Cpu className="w-3 h-3 text-cyan-400" />
          Retrieved Moss Chunks ({context.evidence.length})
        </span>
        <div className="space-y-2">
          {context.evidence.map((item, idx) => {
            const isExp = expandedDoc === item.document_id;
            return (
              <div
                key={idx}
                className="bg-zinc-900/90 border border-zinc-800 rounded-lg p-2.5 space-y-1.5 text-xs font-mono"
              >
                <div className="flex items-start justify-between gap-1">
                  <div className="space-y-0.5">
                    <span className="font-bold text-zinc-200 block text-[11px]">
                      {item.document_id}
                    </span>
                    <span className="text-[10px] text-zinc-500 block">
                      {item.source}
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={() => toggleDoc(item.document_id)}
                    className="text-zinc-500 hover:text-zinc-300 p-0.5"
                    aria-label="Expand chunk"
                  >
                    {isExp ? (
                      <ChevronUp className="w-3.5 h-3.5" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>

                <div className="flex flex-wrap gap-1 text-[9px]">
                  {/* Provenance Badge */}
                  {(item.is_technician_contribution ||
                    item.provenance_type === "TECHNICIAN_CONTRIBUTION" ||
                    item.classification === "technician_contribution") && (
                    <span className="bg-amber-950/80 text-amber-300 border border-amber-500/40 px-1 py-0.2 rounded font-bold uppercase tracking-wider">
                      Tech Contribution
                    </span>
                  )}
                  {(item.verification_status === "PENDING_REVIEW" ||
                    item.metadata?.verification_status === "PENDING_REVIEW") && (
                    <span className="bg-amber-500/20 text-amber-400 border border-amber-500/40 px-1 py-0.2 rounded font-bold uppercase tracking-wider">
                      Pending Review
                    </span>
                  )}
                  {(item.provenance_type === "VERIFIED_COMPANY_DOCUMENT" ||
                    item.metadata?.provenance_type === "VERIFIED_COMPANY_DOCUMENT") && (
                    <span className="bg-emerald-950 text-emerald-300 border border-emerald-800 px-1 py-0.2 rounded uppercase">
                      Verified SOP
                    </span>
                  )}
                  <span className="bg-zinc-800 text-zinc-400 px-1 py-0.2 rounded uppercase">
                    {item.classification}
                  </span>
                  {item.safety_level && (
                    <span
                      className={`px-1 py-0.2 rounded uppercase font-semibold ${
                        item.safety_level === "standard"
                          ? "bg-zinc-800 text-zinc-400"
                          : "bg-amber-950 text-amber-300 border border-amber-800"
                      }`}
                    >
                      {item.safety_level}
                    </span>
                  )}
                  {item.score !== null && item.score !== undefined && (
                    <span className="bg-cyan-950 text-cyan-300 px-1 py-0.2 rounded border border-cyan-800">
                      Score: {(item.score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>

                <div
                  className={`bg-black/50 p-2 rounded text-[11px] text-zinc-300 leading-relaxed border border-zinc-800/80 ${
                    !isExp ? "line-clamp-3" : ""
                  }`}
                >
                  {item.text}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
};
