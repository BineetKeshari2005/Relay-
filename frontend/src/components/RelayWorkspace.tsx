"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Sparkles,
  AlertCircle,
  HelpCircle,
  BookOpen,
  ArrowRight,
  RotateCcw,
  CheckCircle2,
  Layers,
  Wrench,
  Clock,
  Mic,
} from "lucide-react";
import { AnalyzeResponse, ConversationTurnUI, TechnicianContribution } from "@/types/relay";
import { analyzeQuery } from "@/lib/api";
import { useVoiceCopilot } from "@/lib/voice/useVoiceCopilot";
import { InputComposer } from "./InputComposer";
import { SafetyPanel } from "./SafetyPanel";
import { AssessmentCard } from "./AssessmentCard";
import { NextStepCard } from "./NextStepCard";
import { ClarifyingQuestionsPanel } from "./ClarifyingQuestionsPanel";
import { TeachRelayModal } from "./TeachRelayModal";
import { FullStepsModal } from "./FullStepsModal";
import { WhyThisAnswerModal } from "./WhyThisAnswerModal";
import { EmptyState } from "./EmptyState";

export const RelayWorkspace: React.FC = () => {
  const [turns, setTurns] = useState<ConversationTurnUI[]>([]);
  const [activeTurnIndex, setActiveTurnIndex] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [globalError, setGlobalError] = useState<string | null>(null);

  // Modals
  const [isTeachRelayOpen, setIsTeachRelayOpen] = useState<boolean>(false);
  const [isFullStepsOpen, setIsFullStepsOpen] = useState<boolean>(false);
  const [isWhyAnswerOpen, setIsWhyAnswerOpen] = useState<boolean>(false);
  const [contributionNotice, setContributionNotice] = useState<string | null>(null);

  const sessionId = "sess-017";
  const assetId = "ACX-420-017";

  const handleVoiceTranscriptSubmit = useCallback(
    (transcript: string) => {
      handleQuerySubmit(transcript, sessionId, assetId, true);
    },
    [sessionId, assetId]
  );

  const {
    voiceState,
    interimTranscript,
    finalTranscript,
    errorMessage: voiceError,
    telemetry: voiceTelemetry,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
  } = useVoiceCopilot({
    onTranscriptReady: handleVoiceTranscriptSubmit,
  });

  const handleQuerySubmit = async (
    query: string,
    overrideSessionId?: string,
    overrideAssetId?: string,
    isVoiceTrigger: boolean = false
  ) => {
    setIsLoading(true);
    setGlobalError(null);

    try {
      const response: AnalyzeResponse = await analyzeQuery({
        query,
        session_id: overrideSessionId || sessionId,
        asset_id: overrideAssetId || assetId,
      });

      const voiceLatency = isVoiceTrigger
        ? voiceTelemetry.recording_duration_ms + voiceTelemetry.transcription_latency_ms
        : undefined;

      const newTurn: ConversationTurnUI = {
        id: `turn-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        query,
        response,
        client_latency_ms: response.client_latency_ms || 0,
        is_voice: isVoiceTrigger,
        voice_latency_ms: voiceLatency,
      };

      setTurns((prev) => {
        const nextTurns = [...prev, newTurn];
        setActiveTurnIndex(nextTurns.length - 1);
        return nextTurns;
      });

      // Automatically speak spoken response if triggered via speech
      if (isVoiceTrigger && response.reasoning.spoken_response) {
        speak(response.reasoning.spoken_response);
      }
    } catch (err: any) {
      setGlobalError(err.message || "Failed to analyze diagnostic query.");
    } finally {
      setIsLoading(false);
    }
  };

  const activeTurn = turns[activeTurnIndex] || null;
  const activeReasoning = activeTurn?.response.reasoning || null;
  const activeContext = activeTurn?.response.context || null;

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Voice & Text Input Section */}
      <section className="space-y-3">
        <InputComposer
          onSubmitQuery={handleQuerySubmit}
          isLoading={isLoading}
          defaultSessionId={sessionId}
          defaultAssetId={assetId}
          voiceState={voiceState}
          interimTranscript={interimTranscript}
          finalTranscript={finalTranscript}
          isVoiceSpeaking={voiceState === "speaking"}
          onStartListening={startListening}
          onStopListening={stopListening}
          onStopSpeaking={stopSpeaking}
          voiceError={voiceError}
        />
      </section>

      {/* Global Error Banner */}
      {globalError && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-xs sm:text-sm text-red-700 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block text-red-900">Communication Error</span>
            <span>{globalError}</span>
          </div>
        </div>
      )}

      {/* Knowledge Ingestion Notice */}
      {contributionNotice && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3.5 flex items-center justify-between text-xs text-emerald-800">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{contributionNotice}</span>
          </div>
          <button
            type="button"
            onClick={() => setContributionNotice(null)}
            className="text-emerald-700 hover:text-emerald-900 font-bold ml-2 cursor-pointer"
          >
            ✕
          </button>
        </div>
      )}

      {/* Turn History Pills if > 1 turn */}
      {turns.length > 1 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
          <span className="text-slate-400 font-medium shrink-0">Recent Turns:</span>
          {turns.map((turn, idx) => (
            <button
              key={turn.id}
              type="button"
              onClick={() => setActiveTurnIndex(idx)}
              className={`px-3 py-1 rounded-full border text-xs font-medium transition-colors shrink-0 flex items-center gap-1.5 cursor-pointer ${
                idx === activeTurnIndex
                  ? "bg-blue-50 text-blue-600 border-blue-200 font-semibold"
                  : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50"
              }`}
            >
              {turn.is_voice && <Mic className="w-3 h-3 text-blue-600" />}
              <span>Turn #{idx + 1} ({turn.timestamp})</span>
            </button>
          ))}
        </div>
      )}

      {/* Response Area: Focused strictly on "What should I do right now?" */}
      {activeTurn && activeReasoning && activeContext ? (
        <div className="space-y-4">
          {/* 1. SAFETY SECTION (Displayed FIRST, ONLY if safety warnings exist) */}
          <SafetyPanel
            safety={activeContext.safety_context}
            safetyConsiderations={activeReasoning.safety_considerations}
          />

          {/* 2. NEXT ACTION (Strongest visual element after safety) */}
          <NextStepCard
            steps={activeReasoning.recommended_next_steps}
            onOpenFullStepsModal={() => setIsFullStepsOpen(true)}
          />

          {/* 3. ASSESSMENT (Short, readable, with Read Aloud) */}
          <AssessmentCard
            status={activeReasoning.status}
            issueSummary={activeReasoning.issue_summary}
            whatWeKnow={activeReasoning.what_we_know}
            assessment={activeReasoning.assessment}
            certaintyLevel={activeReasoning.certainty_level}
            spokenResponse={activeReasoning.spoken_response}
            onSpeakResponse={(text) => speak(text)}
            isSpeaking={voiceState === "speaking"}
          />

          {/* 4. CLARIFYING QUESTIONS (if needs_information) */}
          {activeReasoning.clarifying_questions && activeReasoning.clarifying_questions.length > 0 && (
            <ClarifyingQuestionsPanel
              questions={activeReasoning.clarifying_questions}
              onSelectQuestion={(q) => handleQuerySubmit(q, sessionId, assetId, false)}
            />
          )}

          {/* 5. SECONDARY ACTIONS ROW */}
          <div className="bg-slate-100/70 border border-slate-200 rounded-xl p-3 flex flex-wrap items-center justify-between gap-2.5">
            <div className="flex flex-wrap items-center gap-2">
              {/* "Why this answer?" Button */}
              <button
                type="button"
                onClick={() => setIsWhyAnswerOpen(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-200 hover:border-slate-300 text-xs font-semibold text-slate-700 hover:text-slate-900 shadow-2xs transition-colors cursor-pointer"
              >
                <BookOpen className="w-3.5 h-3.5 text-blue-600" />
                <span>Why this answer? ({activeReasoning.citations.length} sources)</span>
              </button>

              {/* "Follow-up questions" trigger if not already showing */}
              {activeReasoning.clarifying_questions && activeReasoning.clarifying_questions.length > 0 && (
                <span className="text-xs text-amber-700 font-medium px-2 py-1 bg-amber-50 rounded-md border border-amber-200">
                  {activeReasoning.clarifying_questions.length} clarifying questions pending
                </span>
              )}
            </div>

            {/* "Teach Relay / Save to Session" Button */}
            <button
              type="button"
              onClick={() => setIsTeachRelayOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border border-slate-200 hover:border-slate-300 text-xs font-semibold text-slate-700 hover:text-slate-900 shadow-2xs transition-colors cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span>Teach Relay</span>
            </button>
          </div>
        </div>
      ) : (
        /* Empty State */
        <EmptyState
          icon={Wrench}
          title="Relay Field Copilot Ready"
          description="Speak or type a field symptom, error code, or telemetry reading to begin zero-latency evidence-grounded diagnosis."
        />
      )}

      {/* Full Steps Modal */}
      <FullStepsModal
        isOpen={isFullStepsOpen}
        onClose={() => setIsFullStepsOpen(false)}
        steps={activeReasoning?.recommended_next_steps || []}
      />

      {/* Why This Answer Modal */}
      <WhyThisAnswerModal
        isOpen={isWhyAnswerOpen}
        onClose={() => setIsWhyAnswerOpen(false)}
        claims={activeReasoning?.evidence_claims || []}
        citations={activeReasoning?.citations || []}
        issueSummary={activeReasoning?.issue_summary}
      />

      {/* Teach Relay Modal */}
      <TeachRelayModal
        isOpen={isTeachRelayOpen}
        onClose={() => setIsTeachRelayOpen(false)}
        onSuccess={(contrib) => {
          setContributionNotice(
            `Saved field finding "${contrib.title}" as technician-contributed knowledge (Pending Review).`
          );
          setTimeout(() => setContributionNotice(null), 8000);
        }}
        initialAssetId={activeContext?.asset_id || assetId}
        initialSessionId={activeContext?.session_id || sessionId}
        initialErrorCode={activeContext?.error_code || undefined}
      />
    </div>
  );
};
