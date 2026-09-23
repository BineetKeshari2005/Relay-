"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Plus, History, Clock, ArrowRight, Loader2, Cpu } from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { getDemoSession } from "@/lib/api";

interface SessionListItem {
  id: string;
  assetId: string;
  model: string;
  issue: string;
  time: string;
  status: string;
}

export default function SessionsPage() {
  const [activeTab, setActiveTab] = useState<"recent" | "today" | "week" | "all">("recent");
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch live session from demo API
    getDemoSession("sess-017")
      .then((detail) => {
        setSessions([
          {
            id: detail.session.session_id,
            assetId: detail.session.asset_id,
            model: detail.asset.model,
            issue: detail.session.current_issue || "High discharge pressure (E17)",
            time: "10:31 AM",
            status: detail.session.status || "active",
          },
          {
            id: "sess-012",
            assetId: "ACX-420-012",
            model: "CoolCore ACX-420",
            issue: "Compressor abnormal vibration & alignment",
            time: "09:14 AM",
            status: "completed",
          },
          {
            id: "sess-008",
            assetId: "ACX-420-008",
            model: "CoolCore ACX-420",
            issue: "Routine pre-season coil inspection",
            time: "Yesterday",
            status: "completed",
          },
        ]);
      })
      .catch(() => {
        // Fallback demo data if backend unavailable
        setSessions([
          {
            id: "sess-017",
            assetId: "ACX-420-017",
            model: "CoolCore ACX-420",
            issue: "High discharge pressure (E17)",
            time: "10:31 AM",
            status: "active",
          },
        ]);
      })
      .finally(() => setLoading(false));
  }, []);

  const tabs = [
    { id: "recent", label: "Recent" },
    { id: "today", label: "Today" },
    { id: "week", label: "This Week" },
    { id: "all", label: "All Sessions" },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Diagnostic Sessions
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Your recent equipment diagnostic history and technician interventions
          </p>
        </div>

        <Link
          href="/workspace"
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs sm:text-sm font-semibold shadow-xs transition-colors self-start sm:self-auto cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>New Session</span>
        </Link>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2 overflow-x-auto text-xs font-medium">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
              activeTab === tab.id
                ? "bg-blue-50 text-blue-600 font-semibold"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Sessions List */}
      {loading ? (
        <div className="p-12 flex justify-center text-slate-400">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        </div>
      ) : (
        <div className="space-y-3">
          {sessions.map((sess) => (
            <Link
              key={sess.id}
              href={`/sessions/${sess.id}`}
              className="bg-white border border-slate-200 hover:border-blue-400 rounded-xl p-4 sm:p-5 flex items-center justify-between gap-4 transition-all shadow-2xs hover:shadow-xs group block"
            >
              <div className="space-y-1 sm:space-y-1.5">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono font-bold text-xs sm:text-sm text-slate-900">
                    {sess.assetId}
                  </span>
                  <span className="text-[11px] text-slate-500 font-mono hidden sm:inline">
                    {sess.model}
                  </span>
                  <StatusBadge status={sess.status} size="sm" />
                </div>
                <p className="text-xs sm:text-sm font-medium text-slate-700">
                  {sess.issue}
                </p>
              </div>

              <div className="flex items-center gap-4 shrink-0 text-slate-400 group-hover:text-blue-600">
                <div className="text-right hidden sm:block">
                  <span className="text-xs text-slate-500 font-mono block">
                    {sess.time}
                  </span>
                  <span className="text-[10px] text-slate-400 uppercase font-mono">
                    Session ID: {sess.id}
                  </span>
                </div>
                <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
