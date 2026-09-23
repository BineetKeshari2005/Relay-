"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Wrench,
  Activity,
  History,
  BookOpen,
  Database,
  Cpu,
  Settings,
  HelpCircle,
  X,
  Layers,
} from "lucide-react";

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen = false, onClose }) => {
  const pathname = usePathname();

  const navItems = [
    {
      label: "Workspace",
      href: "/workspace",
      aliases: ["/"],
      icon: Activity,
    },
    {
      label: "Sessions",
      href: "/sessions",
      aliases: ["/sessions"],
      icon: History,
    },
    {
      label: "Evidence",
      href: "/evidence",
      aliases: ["/evidence"],
      icon: Database,
    },
    {
      label: "Knowledge",
      href: "/knowledge",
      aliases: ["/knowledge"],
      icon: BookOpen,
    },
    {
      label: "Assets",
      href: "/assets",
      aliases: ["/assets"],
      icon: Cpu,
    },
  ];

  const isItemActive = (itemHref: string, aliases: string[]) => {
    if (pathname === itemHref) return true;
    if (itemHref === "/workspace" && pathname === "/") return true;
    return aliases.some((alias) => alias !== "/" && pathname.startsWith(alias));
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-slate-900/30 backdrop-blur-xs z-40 lg:hidden transition-opacity"
        />
      )}

      {/* Persistent Sidebar */}
      <aside
        className={`fixed top-0 bottom-0 left-0 w-60 bg-white border-r border-slate-200 z-50 flex flex-col transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Brand / Logo */}
        <div className="h-16 px-5 border-b border-slate-200 flex items-center justify-between">
          <Link
            href="/workspace"
            onClick={onClose}
            className="flex items-center gap-2.5 text-slate-900 group"
          >
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-xs group-hover:bg-blue-700 transition-colors">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <span className="font-bold text-sm tracking-tight block text-slate-900">
                RELAY
              </span>
              <span className="text-[10px] text-slate-500 font-medium tracking-tight block">
                Field Technician Copilot
              </span>
            </div>
          </Link>

          {/* Close button for mobile */}
          <button
            type="button"
            onClick={onClose}
            className="lg:hidden p-1.5 text-slate-400 hover:text-slate-600 rounded-md hover:bg-slate-100"
            aria-label="Close navigation"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Primary Navigation */}
        <div className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Diagnostic Copilot
          </div>
          {navItems.map((item) => {
            const active = isItemActive(item.href, item.aliases);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                  active
                    ? "bg-blue-50 text-blue-600 font-semibold"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                }`}
              >
                <Icon
                  className={`w-4 h-4 shrink-0 ${
                    active ? "text-blue-600" : "text-slate-400"
                  }`}
                />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>

        {/* Bottom Utility Items */}
        <div className="p-3 border-t border-slate-200 space-y-1">
          <Link
            href="/settings"
            onClick={onClose}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
              pathname === "/settings"
                ? "bg-blue-50 text-blue-600 font-semibold"
                : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
            }`}
          >
            <Settings className="w-4 h-4 text-slate-400 shrink-0" />
            <span>Settings</span>
          </Link>
          <Link
            href="/help"
            onClick={onClose}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
              pathname === "/help"
                ? "bg-blue-50 text-blue-600 font-semibold"
                : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
            }`}
          >
            <HelpCircle className="w-4 h-4 text-slate-400 shrink-0" />
            <span>Help &amp; Guides</span>
          </Link>
        </div>
      </aside>
    </>
  );
};
