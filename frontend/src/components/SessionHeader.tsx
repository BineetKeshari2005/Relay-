"use client";

import React from "react";
import { Activity, BookOpen, Cpu, Database, Mic, ShieldAlert, Wifi, WifiOff } from "lucide-react";
import { ReasoningMetadata } from "@/types/relay";
import { VoiceState } from "@/lib/voice/types";

interface SessionHeaderProps {
  isBackendOnline: boolean;
  sessionId: string;
  assetId: string;
  lastReasoningMeta?: ReasoningMetadata | null;
  lastClientLatencyMs?: number | null;
  voiceState?: VoiceState;
  lastVoiceLatencyMs?: number | null;
  onOpenTeachRelay?: () => void;
}

export const SessionHeader: React.FC<SessionHeaderProps> = ({
  isBackendOnline,
  sessionId,
  assetId,
  lastReasoningMeta,
  lastClientLatencyMs,
  voiceState = "idle",
  lastVoiceLatencyMs,
  onOpenTeachRelay,
}) => {
  return (
    <header className="border-b border-zinc-800 bg-zinc-950/90 backdrop-blur px-4 py-3 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
        {/* Brand & System Title */}
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-500 font-black text-xl tracking-tighter">
            ⚡
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono font-bold tracking-wider text-base text-zinc-100">
                RELAY
              </span>
              <span className="text-[10px] uppercase font-mono font-semibold px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">
                Field Copilot
              </span>
            </div>
            <p className="text-[11px] text-zinc-400 font-mono flex items-center gap-1.5">
              <span>Zero-Latency Decision Support</span>
              <span className="text-zinc-600">•</span>
              <span className="text-amber-500/90 font-medium">
                Fictional HVAC Sandbox
              </span>
            </p>
          </div>
        </div>

        {/* Operational Indicators */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
          {/* Active Asset Badge */}
          <div className="bg-zinc-900 border border-zinc-800 rounded px-2.5 py-1 flex items-center gap-1.5 text-zinc-300">
            <span className="text-zinc-500 text-[10px]">ASSET:</span>
            <span className="font-semibold text-zinc-100">{assetId}</span>
          </div>

          {/* Session ID Badge */}
          <div className="bg-zinc-900 border border-zinc-800 rounded px-2.5 py-1 flex items-center gap-1.5 text-zinc-300">
            <span className="text-zinc-500 text-[10px]">SESSION:</span>
            <span className="text-zinc-200">{sessionId}</span>
          </div>

          {/* Backend Connectivity Badge */}
          <div
            className={`border rounded px-2.5 py-1 flex items-center gap-1.5 ${
              isBackendOnline
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                : "bg-rose-500/10 border-rose-500/30 text-rose-400 animate-pulse"
            }`}
          >
            {isBackendOnline ? (
              <>
                <Wifi className="w-3.5 h-3.5" />
                <span>ONLINE</span>
              </>
            ) : (
              <>
                <WifiOff className="w-3.5 h-3.5" />
                <span>OFFLINE (Port 8000)</span>
              </>
            )}
          </div>

          {/* Voice Engine Status Badge */}
          <div
            className={`border rounded px-2.5 py-1 flex items-center gap-1.5 font-mono ${
              voiceState === "listening"
                ? "bg-red-500/10 border-red-500/40 text-red-400 animate-pulse font-bold"
                : voiceState === "speaking"
                ? "bg-cyan-500/10 border-cyan-500/40 text-cyan-300 animate-pulse font-bold"
                : "bg-zinc-900 border-zinc-800 text-zinc-400"
            }`}
          >
            <Mic className="w-3.5 h-3.5" />
            <span className="uppercase text-[11px]">
              {voiceState === "listening"
                ? "Listening"
                : voiceState === "speaking"
                ? "Speaking"
                : "Voice Ready"}
            </span>
          </div>

          {/* Teach Relay Button */}
          {onOpenTeachRelay && (
            <button
              type="button"
              onClick={onOpenTeachRelay}
              className="bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 hover:text-amber-200 border border-amber-500/40 hover:border-amber-400 rounded px-2.5 py-1 flex items-center gap-1.5 transition-colors font-mono font-semibold"
              title="Contribute field observation or resolution to Relay"
            >
              <BookOpen className="w-3.5 h-3.5 text-amber-400" />
              <span>Teach Relay</span>
            </button>
          )}
        </div>

        {/* Realtime Latency Telemetry */}
        {lastReasoningMeta && (
          <div className="flex items-center gap-3 text-[11px] font-mono bg-zinc-900/90 border border-zinc-800/80 rounded-lg px-3 py-1 text-zinc-400">
            {lastVoiceLatencyMs !== null && lastVoiceLatencyMs !== undefined && lastVoiceLatencyMs > 0 && (
              <>
                <div className="flex items-center gap-1">
                  <Mic className="w-3 h-3 text-red-400" />
                  <span>Speech:</span>
                  <span className="text-red-300 font-bold">{lastVoiceLatencyMs}ms</span>
                </div>
                <span className="text-zinc-700">|</span>
              </>
            )}
            <div className="flex items-center gap-1">
              <Database className="w-3 h-3 text-cyan-400" />
              <span>Moss:</span>
              <span className="text-cyan-300 font-bold">
                {lastReasoningMeta.retrieval_latency_ms.toFixed(1)}ms
              </span>
            </div>
            <span className="text-zinc-700">|</span>
            <div className="flex items-center gap-1">
              <Cpu className="w-3 h-3 text-amber-400" />
              <span>Reasoner:</span>
              <span className="text-amber-300 font-bold">
                {lastReasoningMeta.latency_ms.toFixed(1)}ms
              </span>
            </div>
            {lastClientLatencyMs !== null && lastClientLatencyMs !== undefined && (
              <>
                <span className="text-zinc-700">|</span>
                <div className="flex items-center gap-1">
                  <Activity className="w-3 h-3 text-emerald-400" />
                  <span>E2E:</span>
                  <span className="text-emerald-300 font-bold">
                    {lastClientLatencyMs}ms
                  </span>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </header>
  );
};
