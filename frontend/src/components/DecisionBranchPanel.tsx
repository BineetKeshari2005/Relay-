"use client";

import React from "react";
import { GitBranch, CornerDownRight, HelpCircle } from "lucide-react";
import { DecisionBranch } from "@/types/relay";

interface DecisionBranchPanelProps {
  branches: DecisionBranch[];
}

export const DecisionBranchPanel: React.FC<DecisionBranchPanelProps> = ({
  branches,
}) => {
  if (branches.length === 0) {
    return null;
  }

  return (
    <div className="bg-zinc-900/90 border border-zinc-800 rounded-lg p-4 space-y-3">
      <div className="flex items-center gap-2">
        <GitBranch className="w-4 h-4 text-purple-400" />
        <h3 className="font-mono font-bold text-sm text-zinc-100 uppercase tracking-wide">
          SOP Decision Branches (Condition Tree)
        </h3>
      </div>

      <div className="space-y-3">
        {branches.map((b, idx) => (
          <div
            key={idx}
            className="bg-black/40 border border-zinc-800 rounded-md p-3 space-y-2 text-xs font-mono"
          >
            {/* Condition */}
            <div className="flex items-center gap-2 text-amber-300 font-semibold bg-zinc-950 px-2.5 py-1.5 rounded border border-zinc-800">
              <span className="text-zinc-500 uppercase text-[10px]">IF:</span>
              <span>{b.condition}</span>
            </div>

            {/* True Branch */}
            <div className="pl-3 border-l-2 border-emerald-500/60 ml-2 space-y-1">
              <div className="flex items-start gap-1.5 text-emerald-300">
                <CornerDownRight className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                <div>
                  <span className="text-[10px] uppercase font-bold text-emerald-400 block">
                    THEN (TRUE):
                  </span>
                  <span className="text-zinc-200">{b.if_true_branch}</span>
                </div>
              </div>
            </div>

            {/* False Branch */}
            {b.if_false_branch && (
              <div className="pl-3 border-l-2 border-zinc-700 ml-2 space-y-1">
                <div className="flex items-start gap-1.5 text-zinc-400">
                  <CornerDownRight className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  <div>
                    <span className="text-[10px] uppercase font-bold text-zinc-500 block">
                      ELSE (FALSE):
                    </span>
                    <span className="text-zinc-300">{b.if_false_branch}</span>
                  </div>
                </div>
              </div>
            )}

            {/* Rationale & Source Doc IDs */}
            {(b.rationale || b.evidence_ids.length > 0) && (
              <div className="pt-1.5 flex flex-wrap items-center justify-between gap-2 text-[10px] text-zinc-500 border-t border-zinc-800/80">
                {b.rationale && <span>Rationale: {b.rationale}</span>}
                {b.evidence_ids.length > 0 && (
                  <div className="flex items-center gap-1">
                    <span>SOP:</span>
                    {b.evidence_ids.map((id) => (
                      <span
                        key={id}
                        className="bg-zinc-800 text-zinc-400 px-1 py-0.2 rounded"
                      >
                        {id}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
