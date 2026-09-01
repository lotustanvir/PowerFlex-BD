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
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
          Historical Data
        </h1>
        <p className="mt-1 text-gray-500 dark:text-gray-400">
          Browse past grid snapshots, AI predictions, dispatches, and model registry
        </p>
      </header>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex gap-6" aria-label="Tabs">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 border-b-2 px-1 py-3 text-sm font-medium whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? "border-blue-500 text-blue-600 dark:border-blue-400 dark:text-blue-400"
                  : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:border-gray-600 dark:hover:text-gray-300"
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
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-900">
        {activeTab === "grid" && <GridHistory />}
        {activeTab === "predictions" && <PredictionsHistory />}
        {activeTab === "loadshield" && <LoadShieldHistory />}
        {activeTab === "models" && <ModelsList />}
      </div>
    </div>
  );
}
