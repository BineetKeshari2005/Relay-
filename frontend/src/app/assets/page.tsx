"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Search, Cpu, ArrowRight, Loader2, Calendar } from "lucide-react";
import { StatusBadge } from "@/components/StatusBadge";
import { getDemoAsset } from "@/lib/api";
import { EquipmentAsset } from "@/types/relay";

export default function AssetsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [assets, setAssets] = useState<EquipmentAsset[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch live asset from backend API
    getDemoAsset("ACX-420-017")
      .then((asset017) => {
        setAssets([
          {
            ...asset017,
            status: "Attention",
            last_service_date: "Aug 14, 2026",
          },
          {
            asset_id: "ACX-420-012",
            model: "CoolCore ACX-420",
            status: "Operational",
            last_service_date: "Jul 22, 2026",
            location: "Building C - North Mechanical Deck",
          },
          {
            asset_id: "ACX-420-008",
            model: "CoolCore ACX-420",
            status: "Operational",
            last_service_date: "May 19, 2026",
            location: "Building A - Roof Penthouse 2",
          },
          {
            asset_id: "ACX-420-003",
            model: "CoolCore ACX-420",
            status: "Offline",
            last_service_date: "Apr 04, 2026",
            location: "Building B - East Mechanical Deck",
          },
        ]);
      })
      .catch(() => {
        // Fallback
        setAssets([
          {
            asset_id: "ACX-420-017",
            model: "CoolCore ACX-420",
            status: "Attention",
            last_service_date: "Aug 14, 2026",
            location: "Building B - Rooftop HVAC Deck #2",
          },
        ]);
      })
      .finally(() => setLoading(false));
  }, []);

  const filteredAssets = assets.filter((asset) => {
    const matchQuery =
      asset.asset_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.model.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (asset.location && asset.location.toLowerCase().includes(searchTerm.toLowerCase()));
    if (!matchQuery) return false;
    if (statusFilter === "all") return true;
    return asset.status.toLowerCase() === statusFilter.toLowerCase();
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-1 border-b border-slate-200 pb-4">
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">
          Equipment Fleet Assets
        </h2>
        <p className="text-xs sm:text-sm text-slate-500">
          Equipment specifications, active health states, and service history
        </p>
      </div>

      {/* Search & Filter */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search assets by ID, model, or location..."
            className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:outline-hidden focus:border-blue-500 focus:ring-1 focus:ring-blue-500 shadow-2xs"
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-white border border-slate-200 rounded-xl px-3 py-2.5 text-xs font-medium text-slate-700 shadow-2xs focus:outline-hidden focus:border-blue-500 cursor-pointer"
        >
          <option value="all">All Units</option>
          <option value="operational">Operational</option>
          <option value="attention">Attention Required</option>
          <option value="offline">Offline</option>
        </select>
      </div>

      {/* Asset Cards List */}
      {loading ? (
        <div className="p-16 flex flex-col items-center justify-center text-slate-400 space-y-3">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          <span className="text-xs">Loading equipment assets...</span>
        </div>
      ) : filteredAssets.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-10 text-center space-y-2">
          <p className="text-sm font-semibold text-slate-800">No assets found matching your criteria.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredAssets.map((asset) => (
            <Link
              key={asset.asset_id}
              href={`/assets/${asset.asset_id}`}
              className="bg-white border border-slate-200 hover:border-blue-400 rounded-xl p-4 sm:p-5 flex items-center justify-between gap-4 transition-all shadow-2xs hover:shadow-xs group block"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center font-mono font-bold text-xs">
                    <Cpu className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-sm text-slate-900">
                        {asset.asset_id}
                      </span>
                      <StatusBadge status={asset.status} size="sm" />
                    </div>
                    <span className="text-xs text-slate-500 font-medium">
                      {asset.model}
                    </span>
                  </div>
                </div>

                {asset.location && (
                  <p className="text-xs text-slate-500 pl-10.5">
                    Location: {asset.location}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-4 shrink-0 text-slate-400 group-hover:text-blue-600">
                <div className="text-right hidden sm:block font-mono text-xs text-slate-500">
                  <span className="block">Last Service:</span>
                  <span className="text-slate-800 font-semibold">{asset.last_service_date || "Aug 14, 2026"}</span>
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
