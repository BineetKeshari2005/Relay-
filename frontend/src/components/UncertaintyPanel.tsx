"use client";

import React from "react";
import { AlertCircle, HelpCircle, FileWarning, EyeOff } from "lucide-react";
import { UncertaintyModel, DetectedConflict } from "@/types/relay";

interface UncertaintyPanelProps {
  uncertainty?: UncertaintyModel;
  missingInformation?: string[];
  conflicts?: DetectedConflict[];
}

export const UncertaintyPanel: React.FC<UncertaintyPanelProps> = ({
  uncertainty,
  missingInformation = [],
  conflicts = [],
}) => {
  const hasUncertainty =
    missingInformation.length > 0 ||
    conflicts.length > 0 ||
    (uncertainty &&
      (uncertainty.missing_asset ||
        uncertainty.missing_error_code ||
        uncertainty.missing_measurement ||
        uncertainty.insufficient_evidence ||
        uncertainty.conflicting_evidence ||
        uncertainty.ambiguous_query ||
        uncertainty.unverified_safety_threshold));

  if (!hasUncertainty) {
    return null;
  }

  return (
    <div className="bg-zinc-900/90 border border-zinc-800 rounded-lg p-4 space-y-3">
      <div className="flex items-center gap-2">
        <EyeOff className="w-4 h-4 text-amber-400" />
        <h3 className="font-mono font-bold text-sm text-zinc-100 uppercase tracking-wide">
          Uncertainty &amp; Boundary Conditions
        </h3>
      </div>

      {/* Uncertainty Flag Badges */}
      {uncertainty && (
        <div className="flex flex-wrap gap-1.5 font-mono text-[10px]">
          {uncertainty.missing_asset && (
            <span className="bg-amber-950 text-amber-300 border border-amber-800 px-2 py-0.5 rounded">
              MISSING ASSET
            </span>
          )}
          {uncertainty.missing_error_code && (
            <span className="bg-zinc-800 text-zinc-300 border border-zinc-700 px-2 py-0.5 rounded">
              NO ERROR CODE
            </span>
          )}
          {uncertainty.missing_measurement && (
            <span className="bg-amber-950 text-amber-300 border border-amber-800 px-2 py-0.5 rounded">
              MISSING SENSOR TELEMETRY
            </span>
          )}
          {uncertainty.ambiguous_query && (
            <span className="bg-amber-950 text-amber-300 border border-amber-800 px-2 py-0.5 rounded">
              AMBIGUOUS QUERY
            </span>
          )}
          {uncertainty.insufficient_evidence && (
            <span className="bg-rose-950 text-rose-300 border border-rose-800 px-2 py-0.5 rounded">
              INSUFFICIENT MOSS COVERAGE
            </span>
          )}
          {uncertainty.conflicting_evidence && (
            <span className="bg-purple-950 text-purple-300 border border-purple-800 px-2 py-0.5 rounded">
              CONFLICTING EVIDENCE
            </span>
          )}
          {uncertainty.unverified_safety_threshold && (
            <span className="bg-rose-950 text-rose-300 border border-rose-800 px-2 py-0.5 rounded">
              UNVERIFIED SAFETY THRESHOLD
            </span>
          )}
        </div>
      )}

      {/* Missing Information Items */}
      {missingInformation.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-[10px] font-mono uppercase text-zinc-500 block">
            Missing Parameters (What We Don&apos;t Know):
          </span>
          <ul className="space-y-1 text-xs text-zinc-300 font-mono bg-black/30 p-2.5 rounded border border-zinc-800">
            {missingInformation.map((info, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-amber-400 font-bold shrink-0">?</span>
                <span>{info}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Detected Conflicts */}
      {conflicts.length > 0 && (
        <div className="space-y-2">
          <span className="text-[10px] font-mono uppercase text-rose-400 block font-bold">
            Detected Document Contradictions:
          </span>
          {conflicts.map((conflict, idx) => (
            <div
              key={idx}
              className="bg-purple-950/20 border border-purple-500/40 rounded p-2.5 text-xs text-purple-200 font-mono space-y-1"
            >
              <div className="flex items-center justify-between">
                <span className="font-bold uppercase text-[10px]">
                  {conflict.conflict_type}
                </span>
                <span className="text-[10px] text-zinc-400">
                  Sources: {conflict.sources.join(", ")}
                </span>
              </div>
              <p>{conflict.description}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
