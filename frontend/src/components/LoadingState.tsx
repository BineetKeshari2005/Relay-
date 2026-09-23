"use client";

import React from "react";
import { Loader2 } from "lucide-react";

interface LoadingStateProps {
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = "Loading data...",
  className = "",
}) => {
  return (
    <div
      className={`bg-white border border-slate-200 rounded-xl p-10 flex flex-col items-center justify-center text-center space-y-3 shadow-sm ${className}`}
    >
      <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
      <p className="text-xs sm:text-sm font-medium text-slate-500">
        {message}
      </p>
    </div>
  );
};
