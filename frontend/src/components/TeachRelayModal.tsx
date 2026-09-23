"use client";

import React, { useState, useEffect } from "react";
import { X, BookOpen, AlertCircle, CheckCircle2, Clock, Loader2, Sparkles } from "lucide-react";
import { createContribution } from "@/lib/api";
import { TechnicianContribution, ContributionCreateRequest } from "@/types/relay";
import { ProvenanceBadge } from "./ProvenanceBadge";

interface TeachRelayModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (contribution: TechnicianContribution) => void;
  initialAssetId?: string;
  initialSessionId?: string;
  initialErrorCode?: string;
}

export const TeachRelayModal: React.FC<TeachRelayModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  initialAssetId = "",
  initialSessionId = "",
  initialErrorCode = "",
}) => {
  const [whatYouLearned, setWhatYouLearned] = useState("");
  const [actionTaken, setActionTaken] = useState("");
  const [contextEquipment, setContextEquipment] = useState(initialAssetId || "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submittedContribution, setSubmittedContribution] = useState<TechnicianContribution | null>(null);

  useEffect(() => {
    if (isOpen) {
      if (initialAssetId && !contextEquipment) {
        setContextEquipment(initialAssetId);
      }
      setError(null);
      setSubmittedContribution(null);
    }
  }, [isOpen, initialAssetId]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!whatYouLearned.trim()) {
      setError("Please describe what you observed or learned in the field.");
      return;
    }

    setLoading(true);
    setError(null);

    // Derive concise title from first sentence or words
    const trimmedLearned = whatYouLearned.trim();
    const firstLine = trimmedLearned.split("\n")[0].slice(0, 60);
    const title = firstLine.length < trimmedLearned.length ? `${firstLine}...` : firstLine;
    const action = actionTaken.trim() || trimmedLearned;

    const payload: ContributionCreateRequest = {
      title: title.length >= 3 ? title : "Field Observation Note",
      observation: trimmedLearned,
      symptom: trimmedLearned,
      action_taken: action.length >= 3 ? action : "Inspected and verified in field",
      outcome: "Resolved in field",
      asset_id: contextEquipment.trim() || undefined,
      session_id: initialSessionId || undefined,
      technician_id: "Tech 104",
      contributor_name: "Technician Keshari",
    };

    try {
      const result = await createContribution(payload);
      setSubmittedContribution(result);
      onSuccess?.(result);
    } catch (err: any) {
      setError(err.message || "Failed to submit field observation.");
    } finally {
      setLoading(false);
    }
  };

  const handleResetAndClose = () => {
    setWhatYouLearned("");
    setActionTaken("");
    setError(null);
    setSubmittedContribution(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-lg shadow-xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <BookOpen className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-base text-slate-900">
                Teach Relay
              </h3>
              <p className="text-xs text-slate-500">
                Share a field observation that could help the next technician.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleResetAndClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Success Confirmation State */}
        {submittedContribution ? (
          <div className="p-6 space-y-4">
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 space-y-3">
              <div className="flex items-center gap-2 text-emerald-800 font-semibold text-sm">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                <span>Saved as technician-contributed knowledge</span>
              </div>
              <p className="text-xs text-emerald-700 leading-relaxed">
                Your field finding has been indexed into Relay&apos;s retrieval engine for peer technicians.
              </p>

              <div className="flex items-center gap-2 pt-1 border-t border-emerald-200">
                <span className="text-[11px] font-medium text-emerald-800">Status:</span>
                <ProvenanceBadge
                  type="TECHNICIAN_CONTRIBUTION"
                  status="PENDING_REVIEW"
                />
              </div>
            </div>

            <p className="text-xs text-slate-500 italic">
              Note: Technician contributions retain &quot;Pending Review&quot; status and are not treated as verified company SOPs until approved by engineering.
            </p>

            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={handleResetAndClose}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors cursor-pointer"
              >
                Done
              </button>
            </div>
          </div>
        ) : (
          /* Form State */
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-xs text-red-700 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {/* Field: What did you learn? */}
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-800">
                What did you learn? <span className="text-red-500">*</span>
              </label>
              <textarea
                value={whatYouLearned}
                onChange={(e) => setWhatYouLearned(e.target.value)}
                placeholder="e.g. When experiencing intermittent blower vibration, check for loose mounting bolts on the bracket before replacing the motor..."
                rows={4}
                required
                className="w-full text-xs text-slate-900 border border-slate-200 rounded-lg p-3 placeholder-slate-400 focus:outline-hidden focus:border-blue-500 focus:ring-1 focus:ring-blue-500 leading-relaxed resize-none"
              />
            </div>

            {/* Field: Action taken */}
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-800">
                Action or recommendation taken
              </label>
              <input
                type="text"
                value={actionTaken}
                onChange={(e) => setActionTaken(e.target.value)}
                placeholder="e.g. Torqued mounting bracket to 24 Nm"
                className="w-full text-xs text-slate-900 border border-slate-200 rounded-lg px-3 py-2 placeholder-slate-400 focus:outline-hidden focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>

            {/* Field: Context / equipment */}
            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-800">
                Context / equipment <span className="text-slate-400 font-normal">(optional)</span>
              </label>
              <input
                type="text"
                value={contextEquipment}
                onChange={(e) => setContextEquipment(e.target.value)}
                placeholder="e.g. ACX-420-017 or CoolCore ACX-420 series"
                className="w-full text-xs text-slate-900 border border-slate-200 rounded-lg px-3 py-2 placeholder-slate-400 focus:outline-hidden focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              />
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-[11px] text-slate-600 flex items-start gap-2">
              <Clock className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
              <span>
                Contributions are saved immediately as <strong>Technician Contribution</strong> and marked <strong>Pending Review</strong>.
              </span>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={handleResetAndClose}
                className="px-4 py-2 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || !whatYouLearned.trim()}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors flex items-center gap-1.5 cursor-pointer disabled:cursor-not-allowed"
              >
                {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>Save to Relay</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
