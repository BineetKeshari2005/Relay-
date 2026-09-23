"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  Cpu,
  History,
  Activity,
  BookOpen,
  Calendar,
  Layers,
  Wrench,
  Loader2,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { ProvenanceBadge } from "@/components/ProvenanceBadge";
import { getDemoAsset, getDemoSession } from "@/lib/api";
import { EquipmentAsset, SessionDetailResponse } from "@/types/relay";

export default function AssetDetailPage() {
  const params = useParams();
  const assetId = (params?.id as string) || "ACX-420-017";

  const [activeTab, setActiveTab] = useState<
    "overview" | "history" | "measurements" | "knowledge" | "sessions"
  >("overview");
  const [asset, setAsset] = useState<EquipmentAsset | null>(null);
  const [sessionDetail, setSessionDetail] = useState<SessionDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      getDemoAsset(assetId),
      getDemoSession("sess-017").catch(() => null),
    ])
      .then(([assetData, sessData]) => {
        setAsset(assetData);
        setSessionDetail(sessData);
      })
      .catch((err) => {
        setError(err.message || "Failed to load asset details.");
      })
      .finally(() => setLoading(false));
  }, [assetId]);

  if (loading) {
    return (
      <div className="p-16 flex flex-col items-center justify-center text-slate-400 space-y-3">
        <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
        <span className="text-xs">Loading equipment specifications...</span>
      </div>
    );
  }

  if (error || !asset) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center space-y-3 max-w-lg mx-auto">
        <AlertCircle className="w-8 h-8 text-red-600 mx-auto" />
        <h3 className="font-bold text-slate-900 text-sm">Failed to Load Asset</h3>
        <p className="text-xs text-red-700">{error || "Asset not found."}</p>
        <Link
          href="/assets"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 text-white rounded-lg text-xs font-medium"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Assets</span>
        </Link>
      </div>
    );
  }

  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "history", label: "Service History" },
    { id: "measurements", label: "Measurements" },
    { id: "knowledge", label: "Knowledge" },
    { id: "sessions", label: "Sessions" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Link
              href="/assets"
              className="text-slate-400 hover:text-slate-700 text-xs flex items-center gap-1 transition-colors mr-1"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Assets</span>
            </Link>
            <span className="text-slate-300">/</span>
            <h2 className="text-lg font-bold text-slate-900 font-mono">
              {asset.asset_id}
            </h2>
            <StatusBadge status={asset.status || "Attention"} size="sm" />
          </div>
          <p className="text-xs sm:text-sm text-slate-500 font-medium">
            {asset.model} • {asset.location || "Mechanical Rooftop Deck"}
          </p>
        </div>

        <Link
          href="/workspace"
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors self-start sm:self-auto cursor-pointer"
        >
          <Wrench className="w-3.5 h-3.5" />
          <span>Diagnose in Workspace</span>
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

      {/* Tab 1: Overview */}
      {activeTab === "overview" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Current Status Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4 shadow-2xs">
            <h3 className="font-bold text-sm text-slate-900 border-b border-slate-100 pb-2">
              Operational Status
            </h3>
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Current Health:</span>
                <StatusBadge status={asset.status || "Attention"} size="sm" />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Serial Number:</span>
                <span className="font-mono text-slate-900">{asset.serial_number || "CC-2024-8891-B"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Installation Date:</span>
                <span className="text-slate-900">{asset.installation_date || "March 15, 2024"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Last Serviced:</span>
                <span className="font-semibold text-slate-900">{asset.last_service_date || "Aug 14, 2026"}</span>
              </div>
            </div>
          </div>

          {/* Current Observations Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4 shadow-2xs">
            <h3 className="font-bold text-sm text-slate-900 border-b border-slate-100 pb-2">
              Active Observations &amp; Telemetry
            </h3>
            <div className="space-y-2 text-xs text-slate-700">
              <p className="flex items-start gap-2">
                <span className="text-amber-500 font-bold">•</span>
                <span>Active high head pressure fault (E17) observed during high ambient demand.</span>
              </p>
              <p className="flex items-start gap-2">
                <span className="text-blue-500 font-bold">•</span>
                <span>Discharge pressure operating at 195.0 PSI (cutoff safety threshold: 190.0 PSI).</span>
              </p>
              <p className="flex items-start gap-2">
                <span className="text-emerald-500 font-bold">•</span>
                <span>Condenser fan motor operating normally; coil surface requires debris clearing.</span>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Service History */}
      {activeTab === "history" && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4 shadow-2xs">
          <h3 className="font-bold text-sm text-slate-900 border-b border-slate-100 pb-2">
            Chronological Service Records
          </h3>
          {sessionDetail?.service_history && sessionDetail.service_history.length > 0 ? (
            <div className="space-y-3">
              {sessionDetail.service_history.map((rec) => (
                <div
                  key={rec.record_id}
                  className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-1.5 text-xs text-slate-800"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 font-mono">{rec.record_id}</span>
                    <span className="text-slate-500 font-mono">{rec.date}</span>
                  </div>
                  <p className="font-medium text-slate-700">{rec.description}</p>
                  <p className="text-slate-500">
                    <strong className="text-slate-600">Action:</strong> {rec.action_taken}
                  </p>
                  {rec.parts_replaced && rec.parts_replaced.length > 0 && (
                    <div className="flex items-center gap-1.5 pt-1 text-[11px] text-slate-500">
                      <span>Parts replaced:</span>
                      {rec.parts_replaced.map((p, i) => (
                        <span key={i} className="bg-white border border-slate-200 px-1.5 py-0.5 rounded font-mono">
                          {p}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 py-4 text-center">No previous service records registered.</p>
          )}
        </div>
      )}

      {/* Tab 3: Measurements */}
      {activeTab === "measurements" && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4 shadow-2xs">
          <h3 className="font-bold text-sm text-slate-900 border-b border-slate-100 pb-2">
            Current Operating Measurements
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs space-y-1">
              <span className="text-slate-500 block">Discharge Pressure:</span>
              <span className="text-base font-bold font-mono text-red-600">195.0 PSI</span>
              <span className="text-[10px] text-slate-400 font-mono block">Max Threshold: 190.0 PSI</span>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs space-y-1">
              <span className="text-slate-500 block">Ambient Temperature:</span>
              <span className="text-base font-bold font-mono text-slate-800">88.0 °F</span>
              <span className="text-[10px] text-slate-400 font-mono block">Sensor Telemetry</span>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs space-y-1">
              <span className="text-slate-500 block">Suction Pressure:</span>
              <span className="text-base font-bold font-mono text-emerald-600">68.5 PSI</span>
              <span className="text-[10px] text-slate-400 font-mono block">Within nominal range</span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Knowledge */}
      {activeTab === "knowledge" && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4 shadow-2xs">
          <h3 className="font-bold text-sm text-slate-900 border-b border-slate-100 pb-2">
            Applicable Technical Documentation
          </h3>
          <div className="space-y-3">
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-center justify-between">
              <div>
                <h4 className="font-bold text-xs sm:text-sm text-slate-900">
                  SOP-E17: High Head Pressure Cutoff Diagnostics
                </h4>
                <p className="text-xs text-slate-500">CoolCore ACX-420 Manufacturer Technical Manual</p>
              </div>
              <ProvenanceBadge type="VERIFIED_COMPANY_DOCUMENT" />
            </div>

            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-center justify-between">
              <div>
                <h4 className="font-bold text-xs sm:text-sm text-slate-900">
                  CoolCore ACX-420 Electrical Disconnect &amp; LOTO Guide
                </h4>
                <p className="text-xs text-slate-500">Corporate Safety Compliance Document</p>
              </div>
              <ProvenanceBadge type="VERIFIED_COMPANY_DOCUMENT" />
            </div>
          </div>
        </div>
      )}

      {/* Tab 5: Sessions */}
      {activeTab === "sessions" && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4 shadow-2xs">
          <h3 className="font-bold text-sm text-slate-900 border-b border-slate-100 pb-2">
            Previous Diagnostic Sessions for {asset.asset_id}
          </h3>
          <div className="space-y-3">
            <Link
              href="/sessions/sess-017"
              className="bg-slate-50 hover:bg-blue-50/50 border border-slate-200 rounded-xl p-4 flex items-center justify-between transition-colors block"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-xs text-slate-900">sess-017</span>
                  <StatusBadge status="Active" size="sm" />
                </div>
                <p className="text-xs text-slate-600 mt-1">High head pressure cutoff (E17) — 195 PSI</p>
              </div>
              <span className="text-xs text-blue-600 font-semibold">View Session →</span>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
