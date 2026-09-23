"use client";

import React, { useState } from "react";
import { ArrowRight, CheckSquare, Eye, ShieldAlert, ChevronDown, ChevronUp } from "lucide-react";
import { RecommendedNextStep } from "@/types/relay";

interface NextStepCardProps {
  steps: RecommendedNextStep[];
  onOpenFullStepsModal?: () => void;
}

export const NextStepCard: React.FC<NextStepCardProps> = ({
  steps,
  onOpenFullStepsModal,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (steps.length === 0) {
    return null;
  }

  const primaryStep = steps[0];

  return (
    <div className="bg-white border-2 border-blue-500 rounded-xl p-5 sm:p-6 shadow-sm space-y-4 transition-all">
      {/* Header: Title */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-blue-600 flex items-center justify-center text-white shrink-0">
            <CheckSquare className="w-3.5 h-3.5" />
          </div>
          <h2 className="text-xs sm:text-sm font-bold uppercase tracking-wider text-blue-700">
            Next action
          </h2>
        </div>

        {steps.length > 1 && (
          <span className="text-xs font-semibold text-slate-500">
            Step 1 of {steps.length}
          </span>
        )}
      </div>

      {/* Immediate Recommended Step */}
      <div className="space-y-2">
        <p className="text-base sm:text-lg font-semibold text-slate-900 leading-snug">
          {primaryStep.step}
        </p>

        {primaryStep.rationale && (
          <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
            <span className="font-medium text-slate-500 mr-1">Rationale:</span>
            {primaryStep.rationale}
          </p>
        )}

        {/* Expected observation if present */}
        {primaryStep.expected_observation && (
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 flex items-start gap-2 text-xs text-slate-700">
            <Eye className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-800 block">
                Expected Observation:
              </span>
              <span>{primaryStep.expected_observation}</span>
            </div>
          </div>
        )}

        {/* Safety constraints if present */}
        {primaryStep.safety_constraints && primaryStep.safety_constraints.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-2 text-xs text-amber-900">
            <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-amber-950 block">
                Required Precaution:
              </span>
              <ul className="list-disc list-inside space-y-0.5">
                {primaryStep.safety_constraints.map((sc, i) => (
                  <li key={i}>{sc}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Primary Action Button */}
      <div className="pt-2 flex items-center justify-between border-t border-slate-100">
        <button
          type="button"
          onClick={() => {
            if (onOpenFullStepsModal) {
              onOpenFullStepsModal();
            } else {
              setIsExpanded(!isExpanded);
            }
          }}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs sm:text-sm font-semibold shadow-xs transition-colors cursor-pointer"
        >
          <span>View full steps →</span>
        </button>

        {steps.length > 1 && !onOpenFullStepsModal && (
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-xs font-medium text-slate-500 hover:text-slate-800 flex items-center gap-1 cursor-pointer"
          >
            <span>{isExpanded ? "Collapse additional steps" : `+${steps.length - 1} more steps`}</span>
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        )}
      </div>

      {/* Inline Expanded Steps (fallback if modal not provided) */}
      {isExpanded && !onOpenFullStepsModal && steps.length > 1 && (
        <div className="pt-3 border-t border-slate-100 space-y-3">
          {steps.slice(1).map((s, idx) => (
            <div
              key={idx}
              className="bg-slate-50 border border-slate-200 rounded-lg p-3.5 space-y-1.5 text-xs text-slate-800"
            >
              <div className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-[10px]">
                  {idx + 2}
                </span>
                <span className="font-semibold text-slate-900">{s.step}</span>
              </div>
              {s.rationale && <p className="text-slate-600 pl-7">{s.rationale}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
