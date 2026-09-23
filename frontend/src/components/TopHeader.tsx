"use client";

import React, { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { Menu, ChevronDown, Cpu, Wifi, WifiOff } from "lucide-react";
import { checkBackendHealth } from "@/lib/api";

interface TopHeaderProps {
  onToggleSidebar?: () => void;
  selectedAssetId?: string;
  onSelectAssetId?: (assetId: string) => void;
}

export const TopHeader: React.FC<TopHeaderProps> = ({
  onToggleSidebar,
  selectedAssetId = "ACX-420-017",
  onSelectAssetId,
}) => {
  const pathname = usePathname();
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [assetDropdownOpen, setAssetDropdownOpen] = useState<boolean>(false);

  useEffect(() => {
    let mounted = true;
    checkBackendHealth()
      .then(() => {
        if (mounted) setIsOnline(true);
      })
      .catch(() => {
        if (mounted) setIsOnline(false);
      });

    const interval = setInterval(() => {
      checkBackendHealth()
        .then(() => {
          if (mounted) setIsOnline(true);
        })
        .catch(() => {
          if (mounted) setIsOnline(false);
        });
    }, 15000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  // Determine title and subtitle based on route
  const getPageMeta = () => {
    if (pathname === "/" || pathname.startsWith("/workspace")) {
      return {
        title: "Workspace",
        subtitle: "Ask. Diagnose. Act. Learn.",
        showAsset: true,
      };
    }
    if (pathname.startsWith("/sessions")) {
      return {
        title: "Sessions",
        subtitle: "Your recent diagnostic sessions",
        showAsset: false,
      };
    }
    if (pathname.startsWith("/evidence")) {
      return {
        title: "Evidence",
        subtitle: "Sources that power Relay's answers",
        showAsset: false,
      };
    }
    if (pathname.startsWith("/knowledge")) {
      return {
        title: "Knowledge",
        subtitle: "Company knowledge and field contributions",
        showAsset: false,
      };
    }
    if (pathname.startsWith("/assets")) {
      return {
        title: "Assets",
        subtitle: "Equipment and service history",
        showAsset: false,
      };
    }
    if (pathname.startsWith("/settings")) {
      return {
        title: "Settings",
        subtitle: "System parameters and copilot preferences",
        showAsset: false,
      };
    }
    if (pathname.startsWith("/help")) {
      return {
        title: "Help & Documentation",
        subtitle: "Diagnostic guidance and troubleshooting procedures",
        showAsset: false,
      };
    }
    return {
      title: "Workspace",
      subtitle: "Ask. Diagnose. Act. Learn.",
      showAsset: true,
    };
  };

  const { title, subtitle, showAsset } = getPageMeta();

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30 shadow-2xs">
      {/* Left: Mobile hamburger & Page Title / Subtitle */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onToggleSidebar}
          className="lg:hidden p-2 text-slate-500 hover:text-slate-800 rounded-lg hover:bg-slate-100 transition-colors"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div>
          <h1 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight leading-tight">
            {title}
          </h1>
          <p className="text-xs text-slate-500 font-medium hidden sm:block">
            {subtitle}
          </p>
        </div>
      </div>

      {/* Right: Asset Selector + Connection Status + Technician Avatar */}
      <div className="flex items-center gap-2.5 sm:gap-4">
        {/* Asset Selector Badge (if relevant) */}
        {showAsset && (
          <div className="relative">
            <button
              type="button"
              onClick={() => setAssetDropdownOpen(!assetDropdownOpen)}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-xs font-mono font-medium text-slate-700 transition-colors cursor-pointer"
            >
              <Cpu className="w-3.5 h-3.5 text-blue-600" />
              <span>{selectedAssetId}</span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {assetDropdownOpen && (
              <div className="absolute right-0 mt-1 w-44 bg-white border border-slate-200 rounded-lg shadow-lg py-1 z-50 text-xs font-mono">
                <button
                  type="button"
                  onClick={() => {
                    onSelectAssetId?.("ACX-420-017");
                    setAssetDropdownOpen(false);
                  }}
                  className={`w-full px-3 py-1.5 text-left flex items-center justify-between hover:bg-slate-50 ${
                    selectedAssetId === "ACX-420-017" ? "font-bold text-blue-600 bg-blue-50" : "text-slate-700"
                  }`}
                >
                  <span>ACX-420-017</span>
                  <span className="text-[10px] text-amber-600">Attention</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onSelectAssetId?.("ACX-420-012");
                    setAssetDropdownOpen(false);
                  }}
                  className={`w-full px-3 py-1.5 text-left flex items-center justify-between hover:bg-slate-50 ${
                    selectedAssetId === "ACX-420-012" ? "font-bold text-blue-600 bg-blue-50" : "text-slate-700"
                  }`}
                >
                  <span>ACX-420-012</span>
                  <span className="text-[10px] text-emerald-600">Operational</span>
                </button>
              </div>
            )}
          </div>
        )}

        {/* Live Backend Connection Indicator */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border bg-white shadow-2xs">
          {isOnline ? (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="text-slate-700 text-xs hidden sm:inline">Connected</span>
            </>
          ) : (
            <>
              <span className="w-2 h-2 rounded-full bg-red-500"></span>
              <span className="text-red-600 text-xs hidden sm:inline">Offline</span>
            </>
          )}
        </div>

        {/* Technician Avatar Profile */}
        <div className="flex items-center gap-2 pl-1 border-l border-slate-200">
          <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center text-xs font-bold font-mono shadow-xs">
            TK
          </div>
          <div className="hidden xl:block text-left">
            <span className="block text-xs font-semibold text-slate-800 leading-none">
              Tech Keshari
            </span>
            <span className="block text-[10px] text-slate-500 font-mono mt-0.5">
              Field Specialist
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
