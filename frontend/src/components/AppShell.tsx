"use client";

import React, { useState } from "react";
import { Sidebar } from "./Sidebar";
import { TopHeader } from "./TopHeader";

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentAssetId, setCurrentAssetId] = useState("ACX-420-017");

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      {/* Sidebar (Desktop sticky / Mobile drawer) */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Body Area shifted right on desktop for 240px sidebar */}
      <div className="lg:pl-60 flex-1 flex flex-col min-w-0">
        <TopHeader
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          selectedAssetId={currentAssetId}
          onSelectAssetId={setCurrentAssetId}
        />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
};
