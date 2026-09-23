"use client";

import React, { useState, useEffect, KeyboardEvent } from "react";
import {
  Send,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Loader2,
  AlertCircle,
  Sparkles,
} from "lucide-react";
import { VoiceState } from "@/lib/voice/types";

interface InputComposerProps {
  onSubmitQuery: (query: string, sessionId?: string, assetId?: string, isVoice?: boolean) => Promise<void>;
  isLoading: boolean;
  defaultSessionId?: string;
  defaultAssetId?: string;
  voiceState?: VoiceState;
  interimTranscript?: string;
  finalTranscript?: string;
  isVoiceSpeaking?: boolean;
  onStartListening?: () => void;
  onStopListening?: () => void;
  onStopSpeaking?: () => void;
  voiceError?: string | null;
}

export const InputComposer: React.FC<InputComposerProps> = ({
  onSubmitQuery,
  isLoading,
  defaultSessionId = "sess-017",
  defaultAssetId = "ACX-420-017",
  voiceState = "idle",
  interimTranscript = "",
  finalTranscript = "",
  isVoiceSpeaking = false,
  onStartListening,
  onStopListening,
  onStopSpeaking,
  voiceError,
}) => {
  const [query, setQuery] = useState("");

  // Update query when voice transcription yields speech
  useEffect(() => {
    if (interimTranscript) {
      setQuery(interimTranscript);
    } else if (finalTranscript) {
      setQuery(finalTranscript);
    }
  }, [interimTranscript, finalTranscript]);

  const exampleChips = [
    "Unit showing E17",
    "Pressure is 195 PSI",
    "Compressor is vibrating",
    "What should I check?",
  ];

  const handleSubmit = async (e?: React.FormEvent, customQuery?: string) => {
    if (e) e.preventDefault();
    const queryToSend = (customQuery ?? query).trim();
    if (!queryToSend || isLoading) return;
    setQuery("");
    await onSubmitQuery(queryToSend, defaultSessionId, defaultAssetId, false);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleMicClick = () => {
    if (voiceState === "listening") {
      onStopListening?.();
    } else {
      onStartListening?.();
    }
  };

  const isListening = voiceState === "listening";

  return (
    <div className="w-full space-y-3">
      {/* Voice Active Listening Bar */}
      {isListening && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-3.5 flex items-center justify-between gap-3 text-blue-900 transition-all animate-in fade-in duration-150">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-600"></span>
            </span>
            <span className="text-xs font-semibold">
              Listening... Speak your observation or question
            </span>
          </div>
          <button
            type="button"
            onClick={onStopListening}
            className="text-xs font-medium text-blue-700 hover:text-blue-900 underline cursor-pointer"
          >
            Done speaking
          </button>
        </div>
      )}

      {/* Voice Speaking Bar */}
      {isVoiceSpeaking && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 flex items-center justify-between text-emerald-900">
          <div className="flex items-center gap-2">
            <Volume2 className="w-4 h-4 text-emerald-600 animate-pulse" />
            <span className="text-xs font-medium">Relay is speaking...</span>
          </div>
          <button
            type="button"
            onClick={onStopSpeaking}
            className="text-xs font-medium text-emerald-700 hover:text-emerald-900 flex items-center gap-1 cursor-pointer"
          >
            <VolumeX className="w-3.5 h-3.5" />
            <span>Mute</span>
          </button>
        </div>
      )}

      {/* Voice Error Notification */}
      {voiceError && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-center gap-2 text-xs text-amber-800">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
          <span>Voice unavailable — you can continue with text.</span>
        </div>
      )}

      {/* Main Elegant Input Box */}
      <form
        onSubmit={handleSubmit}
        className="bg-white border border-slate-200 rounded-2xl p-2 sm:p-2.5 shadow-sm hover:border-slate-300 focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-100 transition-all"
      >
        <div className="flex items-center gap-2">
          {/* Large Microphone Button */}
          <button
            type="button"
            onClick={handleMicClick}
            disabled={isLoading}
            className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 transition-all cursor-pointer ${
              isListening
                ? "bg-red-500 text-white shadow-sm animate-pulse"
                : "bg-slate-100 hover:bg-blue-50 text-slate-600 hover:text-blue-600 border border-slate-200"
            }`}
            title={isListening ? "Stop listening" : "Click to speak with Relay"}
            aria-label="Microphone"
          >
            {isListening ? (
              <MicOff className="w-5 h-5 text-white" />
            ) : (
              <Mic className="w-5 h-5" />
            )}
          </button>

          {/* Textarea Input */}
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={isLoading}
            placeholder={
              isListening
                ? "Listening..."
                : isLoading
                ? "Analyzing..."
                : "Speak to Relay or type your question..."
            }
            className="flex-1 bg-transparent border-0 resize-none text-sm text-slate-800 placeholder-slate-400 focus:outline-hidden py-2.5 px-2 leading-relaxed"
          />

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="w-10 h-10 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:bg-slate-100 disabled:text-slate-300 text-white flex items-center justify-center shrink-0 transition-colors cursor-pointer shadow-xs disabled:cursor-not-allowed"
            aria-label="Send Query"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin text-slate-500" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </form>

      {/* Example Query Chips */}
      <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 pt-0.5">
        <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wide mr-1 hidden sm:inline">
          Examples:
        </span>
        {exampleChips.map((chip) => (
          <button
            key={chip}
            type="button"
            onClick={() => handleSubmit(undefined, chip)}
            disabled={isLoading}
            className="text-xs font-medium text-slate-600 hover:text-blue-600 bg-white hover:bg-blue-50 border border-slate-200 hover:border-blue-200 px-3 py-1.5 rounded-full transition-colors cursor-pointer shadow-2xs disabled:opacity-50"
          >
            {chip}
          </button>
        ))}
      </div>
    </div>
  );
};
