"use client";

import React from "react";
import { HelpCircle, ChevronRight, MessageSquare } from "lucide-react";

interface ClarifyingQuestionsPanelProps {
  questions: string[];
  onSelectQuestion?: (question: string) => void;
}

export const ClarifyingQuestionsPanel: React.FC<ClarifyingQuestionsPanelProps> = ({
  questions,
  onSelectQuestion,
}) => {
  if (questions.length === 0) {
    return null;
  }

  return (
    <div className="bg-amber-50/80 border border-amber-200 rounded-xl p-4 sm:p-5 space-y-3 shadow-2xs">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-amber-600" />
          <h3 className="font-bold text-sm sm:text-base text-amber-950">
            Relay needs more information
          </h3>
        </div>
        <span className="text-[11px] font-semibold bg-amber-100 text-amber-800 border border-amber-200 px-2 py-0.5 rounded-full uppercase tracking-wider">
          Needs Clarification
        </span>
      </div>

      <p className="text-xs text-amber-900/80 leading-relaxed">
        To narrow down the root cause and provide unambiguous procedure steps, click or answer one of the following:
      </p>

      <div className="space-y-2">
        {questions.map((q, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => onSelectQuestion?.(q)}
            className="w-full text-left bg-white hover:bg-amber-100/50 border border-amber-200 hover:border-amber-300 rounded-lg p-3 transition-colors flex items-center justify-between gap-3 group cursor-pointer shadow-2xs"
          >
            <div className="flex items-center gap-2 text-xs sm:text-sm text-slate-800 font-medium">
              <span className="w-5 h-5 rounded-md bg-amber-100 text-amber-800 font-bold text-xs flex items-center justify-center shrink-0">
                {idx + 1}
              </span>
              <span>{q}</span>
            </div>

            <div className="flex items-center gap-1 text-xs font-semibold text-amber-700 opacity-70 group-hover:opacity-100 transition-opacity shrink-0">
              <span>Send</span>
              <ChevronRight className="w-4 h-4" />
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
