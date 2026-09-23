"use client";

import React from "react";
import { CheckCircle2, AlertTriangle, XCircle, ShieldCheck } from "lucide-react";
import { ReasoningValidationReport } from "@/types/relay";

interface ValidationBadgeProps {
  report: ReasoningValidationReport;
}

export const ValidationBadge: React.FC<ValidationBadgeProps> = ({ report }) => {
  if (report.is_valid && report.warnings.length === 0) {
    return (
      <div className="bg-emerald-950/40 border border-emerald-500/30 rounded px-2.5 py-1 flex items-center gap-1.5 text-[11px] font-mono text-emerald-400">
        <ShieldCheck className="w-3.5 h-3.5" />
        <span>Grounded Reasoning Validated (Zero Hallucinations)</span>
      </div>
    );
  }

  return (
    <div
      className={`border rounded p-2 text-xs font-mono space-y-1 ${
        report.is_valid
          ? "bg-amber-950/30 border-amber-500/40 text-amber-300"
          : "bg-rose-950/40 border-rose-500 text-rose-300"
      }`}
    >
      <div className="flex items-center gap-1.5 font-bold">
        {report.is_valid ? (
          <>
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            <span>Validation Advisory Warnings ({report.warnings.length})</span>
          </>
        ) : (
          <>
            <XCircle className="w-3.5 h-3.5 text-rose-400" />
            <span>Reasoning Validation Failed ({report.errors.length} errors)</span>
          </>
        )}
      </div>

      {report.errors.length > 0 && (
        <ul className="list-disc list-inside space-y-0.5 text-[11px] text-rose-200">
          {report.errors.map((err, i) => (
            <li key={i}>{err}</li>
          ))}
        </ul>
      )}

      {report.warnings.length > 0 && (
        <ul className="list-disc list-inside space-y-0.5 text-[11px] text-amber-200">
          {report.warnings.map((warn, i) => (
            <li key={i}>{warn}</li>
          ))}
        </ul>
      )}
    </div>
  );
};
