"use client";

import React from "react";
import { AlertTriangle, Lock, ShieldAlert } from "lucide-react";
import { SafetyContext } from "@/types/relay";

interface SafetyPanelProps {
  safety: SafetyContext;
  safetyConsiderations?: string[];
}

export const SafetyPanel: React.FC<SafetyPanelProps> = ({
  safety,
  safetyConsiderations = [],
}) => {
  const hasWarningItems = (safety.warning_items && safety.warning_items.length > 0);
  const hasSafetyWarnings = (safety.safety_warnings && safety.safety_warnings.length > 0);
  const isHighAlert =
    safety.safety_level === "high_pressure" ||
    safety.safety_level === "critical" ||
    safety.mandatory_loto ||
    safety.high_pressure_hazard;

  // IMPORTANT INVARIANT: If there is no safety warning, do not show an empty red card!
  if (!isHighAlert && !hasWarningItems && !hasSafetyWarnings && safetyConsiderations.length === 0) {
    return null;
  }

  return (
    <section
      aria-label="Safety Constraints"
      className="bg-red-50 border border-red-200 rounded-xl p-4 sm:p-5 text-red-950 space-y-3 shadow-xs"
    >
      {/* Header: Warning Icon + Safety Title + Critical Badge */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 text-red-600 shrink-0" />
          <h2 className="font-bold text-sm sm:text-base text-red-900 tracking-tight">
            Safety
          </h2>
        </div>

        <div className="flex items-center gap-1.5 sm:gap-2">
          {safety.mandatory_loto && (
            <span className="inline-flex items-center gap-1 bg-red-100 text-red-800 border border-red-300 text-[10px] font-bold uppercase px-2 py-0.5 rounded-md">
              <Lock className="w-3 h-3" />
              Mandatory LOTO
            </span>
          )}
          <span className="bg-red-600 text-white text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full shadow-2xs">
            Critical
          </span>
        </div>
      </div>

      {/* Actual Dynamic Backend Safety Warnings */}
      {hasWarningItems && (
        <div className="space-y-2">
          {safety.warning_items.map((item, idx) => (
            <div
              key={idx}
              className="bg-white/80 border border-red-200 rounded-lg p-3 text-xs sm:text-sm text-red-900"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="font-semibold leading-relaxed">{item.warning}</span>
                {item.provenance_type && (
                  <span className="text-[10px] font-mono text-red-700 bg-red-100 px-1.5 py-0.5 rounded shrink-0 uppercase">
                    {item.provenance_type === "VERIFIED_FROM_KNOWLEDGE" ? "Verified SOP" : "Heuristic"}
                  </span>
                )}
              </div>
              {(item.source_reference || item.threshold_applied) && (
                <div className="mt-1 flex flex-wrap gap-x-3 text-[11px] text-red-700/80 font-mono">
                  {item.source_reference && <span>Source: {item.source_reference}</span>}
                  {item.threshold_applied && <span>Threshold: {item.threshold_applied}</span>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Fallback to text warnings if warning_items is empty */}
      {!hasWarningItems && hasSafetyWarnings && (
        <div className="space-y-1.5">
          {safety.safety_warnings.map((warn, idx) => (
            <p key={idx} className="text-xs sm:text-sm text-red-900 font-medium leading-relaxed">
              {warn}
            </p>
          ))}
        </div>
      )}

      {/* Additional Reasoning Considerations if available */}
      {safetyConsiderations.length > 0 && !hasWarningItems && !hasSafetyWarnings && (
        <ul className="list-disc list-inside space-y-1 text-xs text-red-900/90 font-medium">
          {safetyConsiderations.map((sc, i) => (
            <li key={i}>{sc}</li>
          ))}
        </ul>
      )}
    </section>
  );
};
