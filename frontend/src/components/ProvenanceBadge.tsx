"use client";

import React from "react";
import { ShieldCheck, History, UserCheck, Clock, HelpCircle } from "lucide-react";
import { ProvenanceType, VerificationStatus } from "@/types/relay";

interface ProvenanceBadgeProps {
  type?: ProvenanceType | string;
  status?: VerificationStatus | string;
  isContribution?: boolean;
  className?: string;
  size?: "sm" | "md";
}

export const ProvenanceBadge: React.FC<ProvenanceBadgeProps> = ({
  type,
  status,
  isContribution,
  className = "",
  size = "sm",
}) => {
  const sizeClasses = size === "sm" ? "text-[11px] px-2 py-0.5" : "text-xs px-2.5 py-1";
  const iconSize = size === "sm" ? "w-3 h-3" : "w-3.5 h-3.5";

  // Check if technician contribution or pending review
  if (
    isContribution ||
    type === "TECHNICIAN_CONTRIBUTION" ||
    status === "PENDING_REVIEW"
  ) {
    if (status === "PENDING_REVIEW") {
      return (
        <span
          className={`inline-flex items-center gap-1 rounded-md font-medium border bg-amber-50 text-amber-700 border-amber-200 ${sizeClasses} ${className}`}
        >
          <Clock className={`${iconSize} text-amber-500`} />
          <span>Pending Review</span>
        </span>
      );
    }

    return (
      <span
        className={`inline-flex items-center gap-1 rounded-md font-medium border bg-indigo-50 text-indigo-700 border-indigo-200 ${sizeClasses} ${className}`}
      >
        <UserCheck className={`${iconSize} text-indigo-500`} />
        <span>Technician Contribution</span>
      </span>
    );
  }

  // Historical service record
  if (
    type === "HISTORICAL_SERVICE_RECORD" ||
    type === "service_record" ||
    type === "historical"
  ) {
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-md font-medium border bg-slate-100 text-slate-700 border-slate-200 ${sizeClasses} ${className}`}
      >
        <History className={`${iconSize} text-slate-500`} />
        <span>Historical Evidence</span>
      </span>
    );
  }

  // Verified company / manufacturer document
  if (
    type === "VERIFIED_COMPANY_DOCUMENT" ||
    type === "MANUFACTURER_DOCUMENT" ||
    type === "sop" ||
    type === "manual" ||
    type === "spec" ||
    type === "bulletin" ||
    status === "VERIFIED"
  ) {
    return (
      <span
        className={`inline-flex items-center gap-1 rounded-md font-medium border bg-emerald-50 text-emerald-700 border-emerald-200 ${sizeClasses} ${className}`}
      >
        <ShieldCheck className={`${iconSize} text-emerald-600`} />
        <span>Verified Knowledge</span>
      </span>
    );
  }

  // Fallback
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md font-medium border bg-slate-50 text-slate-600 border-slate-200 ${sizeClasses} ${className}`}
    >
      <HelpCircle className={`${iconSize} text-slate-400`} />
      <span>Reference Document</span>
    </span>
  );
};
