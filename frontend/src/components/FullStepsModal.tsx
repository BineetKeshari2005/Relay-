"use client";

import React from "react";
import { X, CheckSquare, Eye, ShieldAlert, FileText } from "lucide-react";
import { RecommendedNextStep } from "@/types/relay";

interface FullStepsModalProps {
  isOpen: boolean;
  onClose: () => void;
  steps: RecommendedNextStep[];
}

export const FullStepsModal: React.FC<FullStepsModalProps> = ({
  isOpen,
  onClose,
  steps,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <CheckSquare className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-base text-slate-900">
                Recommended Procedural Steps
              </h3>
              <p className="text-xs text-slate-500">
                Actionable sequential instructions generated from technical knowledge
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

        {/* Steps List */}
        <div className="p-6 overflow-y-auto space-y-4">
          {steps.map((step, idx) => (
            <div
              key={idx}
              className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2.5"
            >
              <div className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-blue-600 text-white font-bold text-xs flex items-center justify-center shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                <div className="space-y-1">
                  <h4 className="font-semibold text-sm sm:text-base text-slate-900 leading-snug">
                    {step.step}
                  </h4>
                  {step.rationale && (
                    <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                      <span className="font-medium text-slate-500 mr-1">Rationale:</span>
                      {step.rationale}
                    </p>
                  )}
                </div>
              </div>

              {/* Expected observation */}
              {step.expected_observation && (
                <div className="ml-9 bg-white border border-slate-200 rounded-lg p-3 flex items-start gap-2 text-xs text-slate-700">
                  <Eye className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-slate-900 block">
                      Expected Observation:
                    </span>
                    <span>{step.expected_observation}</span>
                  </div>
                </div>
              )}

              {/* Safety constraints */}
              {step.safety_constraints && step.safety_constraints.length > 0 && (
                <div className="ml-9 bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2 text-xs text-red-900">
                  <ShieldAlert className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-red-950 block">
                      Safety Constraint:
                    </span>
                    <ul className="list-disc list-inside space-y-0.5">
                      {step.safety_constraints.map((sc, i) => (
                        <li key={i}>{sc}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          ))}
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
