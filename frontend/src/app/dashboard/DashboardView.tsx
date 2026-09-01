"use client";

import GridStatus from "@/components/dashboard/GridStatus";
import LoadShield from "@/components/dashboard/LoadShield";
import SolarAI from "@/components/dashboard/SolarAI";
import WindAI from "@/components/dashboard/WindAI";
import NineZoneAnalysis from "@/components/dashboard/NineZoneAnalysis";
import AllResources from "@/components/dashboard/AllResources";
import BiomassDetail from "@/components/dashboard/BiomassDetail";
import WasteToEnergy from "@/components/dashboard/WasteToEnergy";
import NuclearDetail from "@/components/dashboard/NuclearDetail";
import DemandForecast from "@/components/dashboard/DemandForecast";

export default function DashboardView() {
  return (
    <div className="space-y-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-emerald-400">
            Power Intelligence Dashboard
          </h1>
          <p className="mt-1 text-slate-400">
            Real-time Bangladesh power grid monitoring and AI-driven analysis
          </p>
        </div>
      </header>

      <section aria-label="Grid Status">
        <GridStatus />
      </section>

      <div className="grid gap-8 lg:grid-cols-2">
        <section aria-label="Solar AI Forecast">
          <SolarAI />
        </section>
        <section aria-label="Wind AI Forecast">
          <WindAI />
        </section>
      </div>

      <section aria-label="LoadShield Optimization">
        <LoadShield />
      </section>

      <section aria-label="9-Zone Analysis">
        <NineZoneAnalysis />
      </section>

      <section aria-label="Demand Forecast">
        <DemandForecast />
      </section>

      <section aria-label="All Resources">
        <AllResources />
      </section>

      <div className="grid gap-8 lg:grid-cols-2">
        <section aria-label="Biomass Energy">
          <BiomassDetail />
        </section>
        <section aria-label="Waste to Energy">
          <WasteToEnergy />
        </section>
      </div>

      <section aria-label="Nuclear Energy">
        <NuclearDetail />
      </section>
    </div>
  );
}
