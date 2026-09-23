"use client";

import React from "react";
import Link from "next/link";
import { HelpCircle, Mic, ShieldAlert, BookOpen, Database, ArrowRight } from "lucide-react";

export default function HelpPage() {
  const guideSections = [
    {
      icon: Mic,
      title: "Real-time Voice Interaction",
      description:
        "Click the large microphone icon in the Workspace or use speech-to-text. Relay listens for technical symptoms, error codes, and pressure readings, immediately grounding recommendations with Moss retrieval.",
    },
    {
      icon: ShieldAlert,
      title: "Authoritative Safety Constraints",
      description:
        "Relay enforces mandatory safety checks (including Lockout/Tagout protocols) before proposing physical diagnostic procedures. Safety warnings appear prominently in red whenever hazardous thresholds are exceeded.",
    },
    {
      icon: Database,
      title: "Zero-Latency Moss Retrieval",
      description:
        "Relay retrieves evidence before generating any conclusion. Inspect all cited company manuals, manufacturer SOPs, and service bulletins on the Evidence page or by clicking 'Why this answer?'.",
    },
    {
      icon: BookOpen,
      title: "Technician Knowledge Contribution ('Teach Relay')",
      description:
        "When you discover a novel field resolution or diagnostic insight, click '+ Teach Relay' to contribute. Contributions retain a 'Pending Review' status and are immediately searchable by fellow technicians.",
    },
  ];

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="space-y-1 border-b border-slate-200 pb-4">
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">
          Help &amp; Operating Guides
        </h2>
        <p className="text-xs sm:text-sm text-slate-500">
          Field technician copilot operating instructions, safety guarantees, and retrieval principles
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {guideSections.map((sec, idx) => {
          const Icon = sec.icon;
          return (
            <div
              key={idx}
              className="bg-white border border-slate-200 rounded-xl p-5 space-y-2.5 shadow-2xs"
            >
              <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                <Icon className="w-4 h-4" />
              </div>
              <h3 className="font-bold text-sm text-slate-900">{sec.title}</h3>
              <p className="text-xs text-slate-600 leading-relaxed font-normal">
                {sec.description}
              </p>
            </div>
          );
        })}
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 flex items-center justify-between">
        <div>
          <h4 className="font-bold text-sm text-slate-900">Ready to diagnose?</h4>
          <p className="text-xs text-slate-500">Return to the primary workspace to submit voice or text queries.</p>
        </div>
        <Link
          href="/workspace"
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs"
        >
          <span>Open Workspace →</span>
        </Link>
      </div>
    </div>
  );
}
