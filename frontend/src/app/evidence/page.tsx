"use client";

import React, { useState, useEffect } from "react";
import {
  Search,
  Database,
  Cpu,
  Zap,
  Loader2,
  X,
  FileText,
  Clock,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";
import { ProvenanceBadge } from "@/components/ProvenanceBadge";
import { searchRetrieval, getRetrievalHealth } from "@/lib/api";
import {
  SearchResultItemModel,
  RetrievalHealthResponseModel,
} from "@/types/relay";

export default function EvidencePage() {
  const [query, setQuery] = useState("E17 high pressure troubleshooting");
  const [filterSource, setFilterSource] = useState<string>("all");
  const [results, setResults] = useState<SearchResultItemModel[]>([]);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [providerName, setProviderName] = useState<string>("moss");
  const [loading, setLoading] = useState<boolean>(true);
  const [health, setHealth] = useState<RetrievalHealthResponseModel | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<SearchResultItemModel | null>(null);

  const executeSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    setLoading(true);
    try {
      const data = await searchRetrieval({
        query: searchQuery.trim(),
        top_k: 8,
      });
      setResults(data.results);
      setLatencyMs(data.latency_ms);
      setProviderName(data.provider);
    } catch (err) {
      console.error("Retrieval search error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getRetrievalHealth()
      .then((h) => setHealth(h))
      .catch(() => {});
    executeSearch("E17 high pressure troubleshooting");
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeSearch(query);
  };

  // Filter results if filter is set
  const filteredResults = results.filter((item) => {
    if (filterSource === "all") return true;
    const docType = (item.metadata?.document_type || "").toLowerCase();
    const prov = (item.metadata?.provenance_type || "").toLowerCase();
    if (filterSource === "verified") {
      return (
        prov === "verified_company_document" ||
        docType === "sop" ||
        docType === "manual"
      );
    }
    if (filterSource === "technician") {
      return (
        prov === "technician_contribution" ||
        docType === "technician_contribution"
      );
    }
    if (filterSource === "service") {
      return prov === "historical_service_record" || docType === "service_record";
    }
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header & Mission Banner */}
      <div className="space-y-1 border-b border-slate-200 pb-4">
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">
          Evidence
        </h2>
        <p className="text-xs sm:text-sm text-slate-500">
          Sources that power Relay&apos;s answers — Relay doesn&apos;t simply generate an answer, it retrieves evidence first.
        </p>
      </div>

      {/* Zero Latency Architecture Indicator Banner */}
      <div className="bg-slate-900 text-white rounded-xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-blue-600/30 border border-blue-500/40 flex items-center justify-center text-blue-400 shrink-0">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-white">
                Moss Low-Latency Knowledge Index
              </span>
              <span className="text-[10px] font-mono bg-blue-500/20 text-blue-300 border border-blue-400/30 px-2 py-0.5 rounded-full">
                Active Provider: {providerName}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Zero-latency hybrid vector index loaded in memory for immediate field technician retrieval.
            </p>
          </div>
        </div>

        {latencyMs !== null && (
          <div className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 flex items-center gap-2 self-start sm:self-auto font-mono text-xs">
            <Clock className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-slate-300">Measured Latency:</span>
            <span className="font-bold text-emerald-400">{latencyMs.toFixed(1)} ms</span>
          </div>
        )}
      </div>

      {/* Search Bar & Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <form onSubmit={handleSearchSubmit} className="flex-1 relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search evidence manuals, SOPs, error codes..."
            className="w-full pl-10 pr-24 py-2.5 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:outline-hidden focus:border-blue-500 focus:ring-1 focus:ring-blue-500 shadow-2xs"
          />
          <button
            type="submit"
            disabled={loading}
            className="absolute right-1.5 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-2xs transition-colors cursor-pointer"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Search"}
          </button>
        </form>

        {/* Source Filter Tabs */}
        <select
          value={filterSource}
          onChange={(e) => setFilterSource(e.target.value)}
          className="bg-white border border-slate-200 rounded-xl px-3 py-2.5 text-xs font-medium text-slate-700 shadow-2xs focus:outline-hidden focus:border-blue-500 cursor-pointer"
        >
          <option value="all">All Sources</option>
          <option value="verified">Verified Knowledge</option>
          <option value="technician">Technician Contributions</option>
          <option value="service">Historical Service</option>
        </select>
      </div>

      {/* Results Count & Latency Header */}
      <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
        <span>
          {filteredResults.length} relevant {filteredResults.length === 1 ? "source" : "sources"} found
        </span>
        {latencyMs !== null && (
          <span className="font-mono text-[11px] text-slate-400">
            Retrieved in {latencyMs.toFixed(1)} ms
          </span>
        )}
      </div>

      {/* Results Document Cards */}
      {loading ? (
        <div className="p-16 flex flex-col items-center justify-center text-slate-400 space-y-3">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          <span className="text-xs">Querying Moss retrieval engine...</span>
        </div>
      ) : filteredResults.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-10 text-center space-y-2">
          <p className="text-sm font-semibold text-slate-800">
            No evidence found for this query.
          </p>
          <p className="text-xs text-slate-500">
            Try searching for error codes like &quot;E17&quot;, &quot;vibration&quot;, or &quot;pressure switch&quot;.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredResults.map((item) => {
            const title =
              item.metadata?.title ||
              item.metadata?.document_title ||
              item.id;
            const provType =
              item.metadata?.provenance_type ||
              (item.id.startsWith("contrib") ? "TECHNICIAN_CONTRIBUTION" : "VERIFIED_COMPANY_DOCUMENT");
            const verStatus =
              item.metadata?.verification_status ||
              (item.id.startsWith("contrib") ? "PENDING_REVIEW" : "VERIFIED");

            return (
              <div
                key={item.id}
                onClick={() => setSelectedDoc(item)}
                className="bg-white border border-slate-200 hover:border-blue-400 rounded-xl p-5 space-y-3 shadow-2xs hover:shadow-xs transition-all cursor-pointer group flex flex-col justify-between"
              >
                <div className="space-y-2">
                  {/* Card Title & Provenance Badge */}
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-bold text-sm sm:text-base text-slate-900 group-hover:text-blue-600 transition-colors leading-snug">
                      {title}
                    </h3>
                    <ProvenanceBadge type={provType} status={verStatus} />
                  </div>

                  {/* Excerpt */}
                  <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed font-normal">
                    &ldquo;{item.text}&rdquo;
                  </p>
                </div>

                {/* Card Footer: Metadata & Latency */}
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] font-mono text-slate-400">
                  <span>ID: {item.id}</span>
                  {latencyMs !== null && (
                    <span className="text-slate-500">
                      Retrieved in {latencyMs.toFixed(1)} ms
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Document Detail Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in duration-150">
          <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-xl">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
              <div className="space-y-0.5">
                <h3 className="font-bold text-base text-slate-900">
                  {selectedDoc.metadata?.title || selectedDoc.id}
                </h3>
                <span className="text-xs text-slate-500 font-mono">
                  Document ID: {selectedDoc.id}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setSelectedDoc(null)}
                className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4">
              <div className="flex items-center gap-2">
                <ProvenanceBadge
                  type={selectedDoc.metadata?.provenance_type}
                  status={selectedDoc.metadata?.verification_status}
                  size="md"
                />
                {selectedDoc.score !== null && selectedDoc.score !== undefined && (
                  <span className="text-xs font-mono text-slate-500">
                    Relevance Score: {(selectedDoc.score * 100).toFixed(1)}%
                  </span>
                )}
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs sm:text-sm text-slate-800 leading-relaxed font-mono whitespace-pre-wrap">
                {selectedDoc.text}
              </div>

              {selectedDoc.metadata && Object.keys(selectedDoc.metadata).length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-xs font-semibold text-slate-600 uppercase tracking-wider block">
                    Source Metadata
                  </span>
                  <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-xs font-mono space-y-1">
                    {Object.entries(selectedDoc.metadata).map(([k, v]) => (
                      <div key={k} className="flex items-center justify-between text-slate-600">
                        <span className="capitalize">{k.replace("_", " ")}:</span>
                        <span className="text-slate-900 font-medium">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="px-6 py-3.5 border-t border-slate-200 bg-slate-50/50 flex justify-end rounded-b-2xl">
              <button
                type="button"
                onClick={() => setSelectedDoc(null)}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-xs cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
