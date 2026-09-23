"use client";

import React from "react";
import { CircleDot, CheckCircle2, AlertTriangle, AlertCircle, PowerOff } from "lucide-react";

interface StatusBadgeProps {
  status: string;
  size?: "sm" | "md";
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = "sm",
  className = "",
}) => {
  const norm = (status || "").toLowerCase();
  const sizeClasses = size === "sm" ? "text-[11px] px-2 py-0.5" : "text-xs px-2.5 py-1";
  const dotSize = size === "sm" ? "w-3 h-3" : "w-3.5 h-3.5";

  if (norm === "active" || norm === "running") {
    return (
      <span
        className={`inline-flex items-center gap-1.5 rounded-full font-medium border bg-blue-50 text-blue-700 border-blue-200 ${sizeClasses} ${className}`}
      >
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-600"></span>
        </span>
        <span>Active</span>
      </span>
    );
  }

  if (norm === "completed" || norm === "operational" || norm === "verified" || norm === "ready") {
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-full font-medium border bg-emerald-50 text-emerald-700 border-emerald-200 ${sizeClasses} ${className}`}
      >
        <CheckCircle2 className={`${dotSize} text-emerald-600`} />
        <span>{status === "operational" ? "Operational" : status === "completed" ? "Completed" : "Ready"}</span>
      </span>
    );
  }

  if (norm === "attention" || norm === "warning" || norm === "escalated" || norm === "needs_information") {
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-full font-medium border bg-amber-50 text-amber-700 border-amber-200 ${sizeClasses} ${className}`}
      >
        <AlertTriangle className={`${dotSize} text-amber-600`} />
        <span>{status === "attention" ? "Attention" : status === "needs_information" ? "Needs Info" : "Warning"}</span>
      </span>
    );
  }

  if (norm === "offline" || norm === "critical" || norm === "safety_escalation" || norm === "error") {
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-full font-medium border bg-red-50 text-red-700 border-red-200 ${sizeClasses} ${className}`}
      >
        <AlertCircle className={`${dotSize} text-red-600`} />
        <span>{status === "offline" ? "Offline" : "Critical"}</span>
      </span>
    );
  }

  // Neutral
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full font-medium border bg-slate-100 text-slate-700 border-slate-200 ${sizeClasses} ${className}`}
    >
      <CircleDot className={`${dotSize} text-slate-500`} />
      <span className="capitalize">{status}</span>
    </span>
  );
};
