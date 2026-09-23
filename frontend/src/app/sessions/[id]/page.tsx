"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  User,
  Bot,
  ShieldAlert,
  CheckSquare,
  Activity,
  Database,
  FileText,
  Clock,
  Layers,
  ChevronRight,
  Download,
  PlusCircle,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { ProvenanceBadge } from "@/components/ProvenanceBadge";
import { getDemoSession } from "@/lib/api";
import { SessionDetailResponse } from "@/types/relay";

export default function SessionDetailPage() {
  const params = useParams();
  const sessionId = (params?.id as string) || "sess-017";

  const [sessionData, setSessionData] = useState<SessionDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDemoSession(sessionId)
      .then((data) => {
        setSessionData(data);
      })
      .catch((err) => {
        setError(err.message || "Failed to load session details.");
      })
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) {
    return (
      <div className="p-16 flex flex-col items-center justify-center text-slate-400 space-y-3">
        <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        <span className="text-xs">Loading session telemetry...</span>
      </div>
    );
  }

  if (error || !sessionData) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center space-y-3 max-w-lg mx-auto">
        <AlertCircle className="w-8 h-8 text-red-600 mx-auto" />
        <h3 className="font-bold text-slate-900 text-sm">Failed to Load Session</h3>
        <p className="text-xs text-red-700">{error || "Session not found."}</p>
        <Link
          href="/sessions"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 text-white rounded-lg text-xs font-medium"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Sessions</span>
        </Link>
      </div>
    );
  }

  const { session, asset, service_history, recent_turns } = sessionData;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Link
              href="/sessions"
              className="text-slate-400 hover:text-slate-700 text-xs flex items-center gap-1 transition-colors mr-1"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Sessions</span>
            </Link>
            <span className="text-slate-300">/</span>
            <h2 className="text-lg font-bold text-slate-900 font-mono">
              Session {session.asset_id}
            </h2>
            <StatusBadge status={session.status} size="sm" />
          </div>
          <p className="text-xs sm:text-sm text-slate-500 font-medium">
            {session.current_issue || "High discharge pressure diagnostic run"}
          </p>
        </div>

        {/* Quick Action Buttons */}
        <div className="flex items-center gap-2">
          <Link
            href="/evidence"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors shadow-2xs"
          >
            <Database className="w-3.5 h-3.5 text-blue-600" />
            <span>View Evidence</span>
          </Link>
          <button
            type="button"
            onClick={() => alert("Note saved to session log.")}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors shadow-2xs cursor-pointer"
          >
            <PlusCircle className="w-3.5 h-3.5 text-slate-500" />
            <span>Add Note</span>
          </button>
          <button
            type="button"
            onClick={() => alert("Diagnostic session exported as PDF/JSON summary.")}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 transition-colors shadow-2xs cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Conversation Timeline */}
        <div className="lg:col-span-8 space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h3 className="font-bold text-sm text-slate-900">
              Diagnostic Event Timeline
            </h3>
            <span className="text-xs text-slate-400 font-mono">
              Chronological Stream
            </span>
          </div>

          <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
            {/* Step 1: Initial Query */}
            <div className="relative space-y-2">
              <span className="absolute -left-6 top-1 w-4 h-4 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-bold">
                1
              </span>
              <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-1 shadow-2xs">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span className="font-semibold text-slate-800 flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-slate-500" />
                    Technician Utterance
                  </span>
                  <span className="font-mono text-[11px]">{session.start_time || "10:31 AM"}</span>
                </div>
                <p className="text-xs sm:text-sm text-slate-800 font-medium">
                  &ldquo;I am getting E17 again on unit 017. Pressure is around 195 PSI.&rdquo;
                </p>
              </div>
            </div>

            {/* Step 2: Evidence Retrieved Event */}
            <div className="relative space-y-2">
              <span className="absolute -left-6 top-1 w-4 h-4 rounded-full bg-indigo-600 text-white flex items-center justify-center text-[10px] font-bold">
                2
              </span>
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-indigo-900 flex items-center gap-1.5">
                    <Database className="w-3.5 h-3.5 text-indigo-600" />
                    Moss Zero-Latency Evidence Retrieval
                  </span>
                  <ProvenanceBadge type="VERIFIED_COMPANY_DOCUMENT" />
                </div>
                <p className="text-xs text-slate-600 font-mono bg-white p-2.5 rounded-lg border border-slate-200/80">
                  Matched SOP-E17-002: &ldquo;High head pressure cutoff triggered when discharge pressure exceeds 190.0 PSI...&rdquo;
                </p>
              </div>
            </div>

            {/* Step 3: Safety Constraint Event */}
            <div className="relative space-y-2">
              <span className="absolute -left-6 top-1 w-4 h-4 rounded-full bg-red-600 text-white flex items-center justify-center text-[10px] font-bold">
                3
              </span>
              <div className="bg-red-50 border border-red-200 rounded-xl p-4 space-y-1.5 text-red-950">
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="flex items-center gap-1.5 text-red-800">
                    <ShieldAlert className="w-4 h-4 text-red-600" />
                    Authoritative Safety Alert Triggered
                  </span>
                  <span className="bg-red-600 text-white text-[10px] px-2 py-0.5 rounded-full font-bold uppercase">
                    Critical
                  </span>
                </div>
                <p className="text-xs text-red-900 leading-relaxed">
                  High pressure exceeds safety threshold (195.0 PSI &gt; 190.0 PSI). Do not bypass the high-pressure switch under operational power. Mandatory Lockout/Tagout required before electrical cabinet service.
                </p>
              </div>
            </div>

            {/* Step 4: Recommended Action */}
            <div className="relative space-y-2">
              <span className="absolute -left-6 top-1 w-4 h-4 rounded-full bg-emerald-600 text-white flex items-center justify-center text-[10px] font-bold">
                4
              </span>
              <div className="bg-white border-2 border-blue-500 rounded-xl p-4 space-y-2 shadow-2xs">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold uppercase tracking-wider text-blue-600 flex items-center gap-1.5">
                    <CheckSquare className="w-4 h-4" />
                    Recommended Actionable Step
                  </span>
                </div>
                <p className="text-xs sm:text-sm font-semibold text-slate-900">
                  Disconnect electrical power and perform LOTO before inspecting condenser coil face for particulate blockage.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Extracted Information Sidebar */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4 shadow-2xs">
            <h3 className="font-bold text-xs uppercase tracking-wider text-slate-500 border-b border-slate-100 pb-2">
              Extracted Information
            </h3>

            {/* Asset */}
            <div className="space-y-1">
              <span className="text-xs text-slate-400 font-medium block">Asset</span>
              <div className="flex items-center justify-between font-mono text-xs">
                <span className="font-bold text-slate-900">{asset.asset_id}</span>
                <span className="text-slate-500">{asset.model}</span>
              </div>
            </div>

            {/* Error Code */}
            {session.active_error_code && (
              <div className="space-y-1">
                <span className="text-xs text-slate-400 font-medium block">Active Fault Code</span>
                <span className="inline-block bg-amber-50 text-amber-800 border border-amber-200 font-mono font-bold text-xs px-2.5 py-0.5 rounded-md">
                  {session.active_error_code}
                </span>
              </div>
            )}

            {/* Measurements */}
            <div className="space-y-2">
              <span className="text-xs text-slate-400 font-medium block">Recorded Measurements</span>
              {session.measurements && Object.keys(session.measurements).length > 0 ? (
                <div className="space-y-1.5 font-mono text-xs">
                  {Object.entries(session.measurements).map(([key, val]) => (
                    <div
                      key={key}
                      className="bg-slate-50 border border-slate-200/80 rounded-lg p-2.5 flex items-center justify-between"
                    >
                      <span className="text-slate-600 capitalize">
                        {key.replace("_", " ")}
                      </span>
                      <span className="font-bold text-blue-700">
                        {String(val)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400 italic">No measurements recorded.</p>
              )}
            </div>

            {/* Relevant Observations */}
            <div className="space-y-2">
              <span className="text-xs text-slate-400 font-medium block">Technician Observations</span>
              <div className="bg-slate-50 border border-slate-200/80 rounded-lg p-3 text-xs text-slate-700 space-y-1 leading-relaxed">
                <p>• Elevated head pressure trip during warm ambient cycle</p>
                <p>• Fan motor running, condenser face requires airflow test</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
