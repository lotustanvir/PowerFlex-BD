"use client";

import dynamic from "next/dynamic";
import { DecisionSupportProvider } from "@/hooks/useDecisionSupport";
import { useSystemStatus, SystemStatusBadge } from "./SystemStatus";
import NationalOverview from "./NationalOverview";
import EnergyMix from "./EnergyMix";
import RenewableStatus from "./RenewableStatus";
import GridIntelligence from "./GridIntelligence";
import RiskIntelligence from "./RiskIntelligence";
import EnergyInsights from "./EnergyInsights";
import LoadShield from "./LoadShield";
import NineZoneAnalysis from "./NineZoneAnalysis";
import DecisionHub from "./DecisionHub";
import SmartInsights from "./SmartInsights";
import ForecastingCenter from "./ForecastingCenter";
import HistoricalAnalytics from "./HistoricalAnalytics";
import { SectionHeader } from "@/components/ui/SectionHeader";

const InteractiveMap = dynamic(
  () => import("@/components/dashboard/InteractiveMap"),
  {
    ssr: false,
    loading: () => (
      <div className="h-[500px] rounded-xl border border-slate-700/30 bg-slate-800/30 animate-pulse" aria-label="Loading map" />
    ),
  }
);

function DashboardInner() {
  const systemStatus = useSystemStatus();

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <header className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse-slow" />
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-400">
              Live Intelligence
            </p>
          </div>
          <SystemStatusBadge status={systemStatus} />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
          Bangladesh Energy Command Center
        </h1>
        <p className="max-w-2xl text-xs text-slate-400 leading-relaxed">
          Unified real-time intelligence from PGCB grid data, AI forecasts, and scenario-based risk analysis.
        </p>
      </header>

      {/* PRIORITY 1 — National Energy Situation */}
      <section aria-label="National Energy Overview">
        <NationalOverview />
      </section>

      {/* PRIORITY 2 — Primary Energy Intelligence */}
      <section aria-label="Primary Energy Intelligence">
        <SectionHeader>Energy Intelligence</SectionHeader>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <EnergyMix />
          <GridIntelligence />
          <RenewableStatus />
        </div>
      </section>

      {/* PRIORITY 3 — Risk & Decision */}
      <section aria-label="Risk and Decision Support">
        <SectionHeader>Risk &amp; Decision Support</SectionHeader>
        <div className="grid gap-3 lg:grid-cols-3">
          <RiskIntelligence />
          <SmartInsights />
          <DecisionHub />
        </div>
      </section>

      {/* LoadShield — full width */}
      <section aria-label="LoadShield Optimization">
        <LoadShield />
      </section>

      {/* PRIORITY 4 — Analytics & Forecasting */}
      <section aria-label="Analytics and Forecasting">
        <SectionHeader>Analytics &amp; Forecasting</SectionHeader>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <ForecastingCenter />
          <EnergyInsights />
          <HistoricalAnalytics />
        </div>
      </section>

      {/* PRIORITY 5 — Geographic Intelligence */}
      <section aria-label="Geographic Intelligence">
        <SectionHeader>Geographic Intelligence</SectionHeader>
        <div className="grid gap-3 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <NineZoneAnalysis />
          </div>
          <div className="lg:col-span-7">
            <InteractiveMap className="w-full" />
          </div>
        </div>
      </section>
    </div>
  );
}

export default function CommandCenter() {
  return (
    <DecisionSupportProvider intervalMs={300000}>
      <DashboardInner />
    </DecisionSupportProvider>
  );
}
