"use client";

import { useState } from "react";
import GridHistory from "@/components/history/GridHistory";
import PredictionsHistory from "@/components/history/PredictionsHistory";
import LoadShieldHistory from "@/components/history/LoadShieldHistory";
import ModelsList from "@/components/history/ModelsList";

type Tab = "grid" | "predictions" | "loadshield" | "models";

const TABS: { id: Tab; label: string; icon: string }[] = [
  { id: "grid", label: "Grid History", icon: "⚡" },
  { id: "predictions", label: "Predictions", icon: "🤖" },
  { id: "loadshield", label: "LoadShield", icon: "🛡️" },
  { id: "models", label: "Models", icon: "📦" },
];

export default function HistoryView() {
  const [activeTab, setActiveTab] = useState<Tab>("grid");

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-white">
          Historical Data
        </h1>
        <p className="mt-1 text-xs text-slate-400">
          Browse past grid snapshots, AI predictions, dispatches, and model registry
        </p>
      </header>

      {/* Tabs */}
      <div className="border-b border-slate-700">
        <nav className="-mb-px flex gap-4 overflow-x-auto sm:gap-6" aria-label="Tabs">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex shrink-0 items-center gap-1.5 border-b-2 px-1 py-3 text-sm font-medium whitespace-nowrap transition-colors sm:gap-2 ${
                activeTab === tab.id
                  ? "border-emerald-500 text-emerald-400"
                  : "border-transparent text-slate-500 hover:border-slate-600 hover:text-slate-300"
              }`}
              aria-current={activeTab === tab.id ? "page" : undefined}
            >
              <span aria-hidden="true">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-4">
        {activeTab === "grid" && <GridHistory />}
        {activeTab === "predictions" && <PredictionsHistory />}
        {activeTab === "loadshield" && <LoadShieldHistory />}
        {activeTab === "models" && <ModelsList />}
      </div>
    </div>
  );
}
