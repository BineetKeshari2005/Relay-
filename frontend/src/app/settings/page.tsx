"use client";

import React, { useState } from "react";
import { Settings, ShieldCheck, Cpu, Volume2, Save, CheckCircle2 } from "lucide-react";

export default function SettingsPage() {
  const [autoSpeak, setAutoSpeak] = useState(false);
  const [speechRate, setSpeechRate] = useState("1.05");
  const [defaultAsset, setDefaultAsset] = useState("ACX-420-017");
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="space-y-1 border-b border-slate-200 pb-4">
        <h2 className="text-xl font-bold text-slate-900 tracking-tight">
          Copilot Settings
        </h2>
        <p className="text-xs sm:text-sm text-slate-500">
          Configure field copilot audio playback, retrieval defaults, and asset parameters
        </p>
      </div>

      {saved && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3.5 flex items-center gap-2 text-xs text-emerald-800">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>Preferences updated successfully.</span>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-xl p-5 sm:p-6 space-y-6 shadow-2xs">
        {/* Voice Preferences */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Volume2 className="w-4 h-4 text-blue-600" />
            <h3 className="font-bold text-sm text-slate-900">Voice &amp; Audio</h3>
          </div>

          <div className="space-y-3 text-xs">
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-slate-700 font-medium">Auto-speak Spoken Responses</span>
              <input
                type="checkbox"
                checked={autoSpeak}
                onChange={(e) => setAutoSpeak(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500 cursor-pointer"
              />
            </label>

            <div className="flex items-center justify-between">
              <span className="text-slate-700 font-medium">Speech Rate</span>
              <select
                value={speechRate}
                onChange={(e) => setSpeechRate(e.target.value)}
                className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-slate-700 text-xs cursor-pointer"
              >
                <option value="0.9">0.9x (Deliberate)</option>
                <option value="1.0">1.0x (Normal)</option>
                <option value="1.05">1.05x (Optimal Field Speed)</option>
                <option value="1.15">1.15x (Fast)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Default Equipment */}
        <div className="pt-4 border-t border-slate-100 space-y-3">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-blue-600" />
            <h3 className="font-bold text-sm text-slate-900">Default Equipment Focus</h3>
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-700 font-medium">Active Demonstration Asset</span>
            <select
              value={defaultAsset}
              onChange={(e) => setDefaultAsset(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-slate-700 text-xs font-mono cursor-pointer"
            >
              <option value="ACX-420-017">ACX-420-017 (High Pressure Focus)</option>
              <option value="ACX-420-012">ACX-420-012 (Operational)</option>
            </select>
          </div>
        </div>

        {/* Save Button */}
        <div className="pt-4 border-t border-slate-100 flex justify-end">
          <button
            type="button"
            onClick={handleSave}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors cursor-pointer"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Save Preferences</span>
          </button>
        </div>
      </div>
    </div>
  );
}
