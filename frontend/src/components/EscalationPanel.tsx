"use client";

import React from "react";
import { AlertOctagon, PhoneCall, ShieldAlert } from "lucide-react";
import { EscalationAssessment } from "@/types/relay";

interface EscalationPanelProps {
  escalation: EscalationAssessment;
}

export const EscalationPanel: React.FC<EscalationPanelProps> = ({ escalation }) => {
  if (!escalation.should_escalate) {
    return null;
  }

  return (
    <div className="bg-rose-950/40 border border-rose-500 rounded-lg p-4 space-y-3 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-rose-300">
          <AlertOctagon className="w-5 h-5 text-rose-400" />
          <h3 className="font-mono font-bold text-sm uppercase tracking-wide">
            Supervisor Escalation Required
          </h3>
        </div>
        {escalation.recommended_escalation_target && (
          <span className="bg-rose-900/80 text-rose-200 border border-rose-600 px-2 py-0.5 rounded text-xs font-mono font-bold flex items-center gap-1.5">
            <PhoneCall className="w-3 h-3" />
            {escalation.recommended_escalation_target}
          </span>
        )}
      </div>

      {escalation.reason && (
        <p className="text-xs text-rose-100 font-medium">
          {escalation.reason}
        </p>
      )}

      {escalation.safety_reason && (
        <div className="bg-black/50 border border-rose-500/40 rounded p-2 text-xs text-rose-200 font-mono flex items-start gap-2">
          <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <span className="text-[10px] font-bold uppercase text-rose-400 block">
              Safety Trigger:
            </span>
            <span>{escalation.safety_reason}</span>
          </div>
        </div>
      )}

      {escalation.missing_information.length > 0 && (
        <div className="text-xs text-rose-200 font-mono">
          <span className="text-[10px] uppercase text-rose-400 font-bold block mb-1">
            Information Required Before Proceeding:
          </span>
          <ul className="list-disc list-inside space-y-0.5">
            {escalation.missing_information.map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
