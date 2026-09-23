"use client";

import React from "react";
import { Volume2, VolumeX, CheckCircle, HelpCircle, AlertCircle, ShieldQuestion } from "lucide-react";
import { CertaintyLevel, ReasoningStatus } from "@/types/relay";
import { StatusBadge } from "./StatusBadge";

interface AssessmentCardProps {
  status: ReasoningStatus;
  issueSummary: string;
  whatWeKnow?: string[];
  assessment: string;
  certaintyLevel?: CertaintyLevel;
  spokenResponse?: string | null;
  onSpeakResponse?: (text: string) => void;
  isSpeaking?: boolean;
}

export const AssessmentCard: React.FC<AssessmentCardProps> = ({
  status,
  issueSummary,
  whatWeKnow = [],
  assessment,
  certaintyLevel,
  spokenResponse,
  onSpeakResponse,
  isSpeaking = false,
}) => {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 sm:p-6 shadow-sm space-y-4">
      {/* Header: Title + Status + Read Aloud */}
      <div className="flex items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <h2 className="text-sm sm:text-base font-bold text-slate-900 tracking-tight">
            Assessment
          </h2>
          <StatusBadge status={status} size="sm" />
        </div>

        {/* Read Aloud Button */}
        {onSpeakResponse && (
          <button
            type="button"
            onClick={() => onSpeakResponse(spokenResponse || assessment)}
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
              isSpeaking
                ? "bg-blue-50 border-blue-200 text-blue-700 animate-pulse"
                : "bg-slate-50 hover:bg-slate-100 border-slate-200 text-slate-700"
            }`}
            title="Read diagnostic assessment aloud"
          >
            <Volume2 className="w-3.5 h-3.5 text-blue-600" />
            <span>{isSpeaking ? "Speaking..." : "Read Aloud"}</span>
          </button>
        )}
      </div>

      {/* Short Backend-Generated Assessment */}
      <div className="space-y-3">
        <p className="text-slate-800 text-sm sm:text-base leading-relaxed font-normal">
          {assessment}
        </p>

        {/* Key Grounded Facts (if available) */}
        {whatWeKnow.length > 0 && (
          <div className="bg-slate-50 border border-slate-200/80 rounded-lg p-3 space-y-1.5">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">
              Observed &amp; Grounded Facts:
            </span>
            <ul className="space-y-1 text-xs text-slate-700">
              {whatWeKnow.map((fact, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold shrink-0">✓</span>
                  <span>{fact}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};
