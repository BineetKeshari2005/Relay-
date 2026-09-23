"use client";

import React, { useState, useEffect } from "react";
import {
  BookOpen,
  Plus,
  ShieldCheck,
  UserCheck,
  Clock,
  Sparkles,
  Loader2,
  Calendar,
  User,
  Tag,
  AlertCircle,
} from "lucide-react";
import { ProvenanceBadge } from "@/components/ProvenanceBadge";
import { TeachRelayModal } from "@/components/TeachRelayModal";
import { getContributions } from "@/lib/api";
import { TechnicianContribution } from "@/types/relay";

interface KnowledgeDocItem {
  id: string;
  title: string;
  type: "verified" | "contribution";
  category: string;
  content: string;
  addedBy: string;
  date: string;
  tags?: string[];
  status?: string;
}

export default function KnowledgePage() {
  const [activeTab, setActiveTab] = useState<"all" | "verified" | "pending" | "mine">("all");
  const [contributions, setContributions] = useState<TechnicianContribution[]>([]);
  const [loading, setLoading] = useState(true);
  const [isTeachModalOpen, setIsTeachModalOpen] = useState(false);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  // Authoritative verified company knowledge
  const verifiedCompanyDocs: KnowledgeDocItem[] = [
    {
      id: "DOC-E17-001",
      title: "SOP-E17: High Head Pressure Cutoff Diagnostics",
      type: "verified",
      category: "Manufacturer SOP",
      content:
        "Standard operating procedure for CoolCore ACX-420 series high head pressure error (E17). Cutoff threshold is 190.0 PSI. Mandatory Lockout/Tagout required before electrical cabinet service.",
      addedBy: "CoolCore Engineering",
      date: "Aug 14, 2026",
      tags: ["High Pressure", "E17", "LOTO", "Safety"],
      status: "VERIFIED",
    },
    {
      id: "DOC-VIB-002",
      title: "CoolCore ACX-420 Blower Assembly Overhaul Guide",
      type: "verified",
      category: "Technical Manual",
      content:
        "Comprehensive maintenance manual for dynamic balancing, blower bearing replacement, and impeller alignment tolerances on ACX-420 commercial rooftop units.",
      addedBy: "Service Engineering",
      date: "Jun 10, 2026",
      tags: ["Vibration", "Blower", "Maintenance"],
      status: "VERIFIED",
    },
    {
      id: "DOC-ELEC-003",
      title: "Commercial HVAC Electrical Safety & Lockout/Tagout Standard",
      type: "verified",
      category: "Company Safety Policy",
      content:
        "Mandatory zero-energy state verification protocol prior to servicing disconnect switches, motor starters, and 480V three-phase compressor wiring.",
      addedBy: "Safety Compliance",
      date: "Jan 15, 2026",
      tags: ["Safety", "LOTO", "Electrical"],
      status: "VERIFIED",
    },
  ];

  const fetchContributions = () => {
    setLoading(true);
    getContributions()
      .then((data) => {
        setContributions(data);
      })
      .catch((err) => {
        console.error("Failed to load technician contributions:", err);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchContributions();
  }, []);

  // Combine items for filtering
  const allItems: KnowledgeDocItem[] = [
    ...verifiedCompanyDocs,
    ...contributions.map((c) => ({
      id: c.id || c.contribution_id || "contrib",
      title: c.title,
      type: "contribution" as const,
      category: "Technician Field Observation",
      content: `${c.observed_symptom || c.observation || c.discovered_cause} — Action Taken: ${c.action_taken}`,
      addedBy: c.contributor_name || "Field Technician",
      date: c.created_at ? new Date(c.created_at).toLocaleDateString() : "Recent",
      tags: c.tags || ["Field Finding"],
      status: c.verification_status || "PENDING_REVIEW",
    })),
  ];

  const filteredItems = allItems.filter((item) => {
    if (activeTab === "all") return true;
    if (activeTab === "verified") return item.type === "verified";
    if (activeTab === "pending") return item.type === "contribution";
    if (activeTab === "mine") return item.type === "contribution";
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Knowledge Base
          </h2>
          <p className="text-xs sm:text-sm text-slate-500">
            Company knowledge and field contributions — verified company SOPs and peer field observations.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setIsTeachModalOpen(true)}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs sm:text-sm font-semibold shadow-xs transition-colors self-start sm:self-auto cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          <span>+ Teach Relay</span>
        </button>
      </div>

      {/* Success Banner */}
      {successBanner && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3.5 flex items-center justify-between text-xs text-emerald-800">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{successBanner}</span>
          </div>
          <button
            type="button"
            onClick={() => setSuccessBanner(null)}
            className="text-emerald-700 hover:text-emerald-900 font-bold ml-2 cursor-pointer"
          >
            ✕
          </button>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2 overflow-x-auto text-xs font-medium">
        {[
          { id: "all", label: "All Sources" },
          { id: "verified", label: "Verified Knowledge" },
          { id: "pending", label: "Pending Review" },
          { id: "mine", label: "My Contributions" },
        ].map((tab) => (
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

      {/* Trust & Provenance Notice */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 text-xs text-slate-600 flex items-start gap-2.5">
        <Clock className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong>Provenance Guarantee:</strong> Technician contributions remain clearly marked as{" "}
          <span className="text-amber-700 font-medium">Pending Review</span> and are never silently promoted to verified company knowledge.
        </p>
      </div>

      {/* Knowledge Cards Grid */}
      {loading ? (
        <div className="p-16 flex flex-col items-center justify-center text-slate-400 space-y-3">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
          <span className="text-xs">Loading knowledge records...</span>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-10 text-center space-y-2">
          <p className="text-sm font-semibold text-slate-800">No knowledge records found.</p>
          <p className="text-xs text-slate-500">
            Submit a field finding using the &ldquo;+ Teach Relay&rdquo; button above.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredItems.map((doc) => {
            const isVerified = doc.type === "verified";
            return (
              <div
                key={doc.id}
                className={`bg-white rounded-xl p-5 space-y-3.5 shadow-2xs hover:shadow-xs transition-all flex flex-col justify-between border ${
                  isVerified ? "border-slate-200" : "border-amber-200/80 bg-amber-50/20"
                }`}
              >
                <div className="space-y-2.5">
                  {/* Title & Badge */}
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-bold text-sm sm:text-base text-slate-900 leading-snug">
                      {doc.title}
                    </h3>
                    <ProvenanceBadge
                      type={isVerified ? "VERIFIED_COMPANY_DOCUMENT" : "TECHNICIAN_CONTRIBUTION"}
                      status={doc.status}
                    />
                  </div>

                  <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wide block">
                    {doc.category}
                  </span>

                  {/* Body Content */}
                  <p className="text-xs text-slate-600 leading-relaxed font-normal">
                    {doc.content}
                  </p>
                </div>

                {/* Footer Metadata */}
                <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500">
                  <div className="flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5 text-slate-400" />
                    <span>Added by: <strong className="text-slate-700">{doc.addedBy}</strong></span>
                  </div>
                  <div className="flex items-center gap-1.5 font-mono">
                    <Calendar className="w-3.5 h-3.5 text-slate-400" />
                    <span>{doc.date}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Teach Relay Modal */}
      <TeachRelayModal
        isOpen={isTeachModalOpen}
        onClose={() => setIsTeachModalOpen(false)}
        onSuccess={(contrib) => {
          setSuccessBanner(`Saved field finding "${contrib.title}" as technician-contributed knowledge (Pending Review).`);
          fetchContributions();
        }}
      />
    </div>
  );
}
