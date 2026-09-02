import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "LoadShield — Scenario-Based Deficit Optimization for Bangladesh",
  description:
    "LoadShield is PowerFlex BD's scenario-based deficit optimization engine. It analyzes PGCB demand and supply data to recommend resource deployment across 9 zones. Not a real-time grid dispatch system.",
  keywords: [
    "Bangladesh load shedding",
    "Bangladesh power deficit",
    "LoadShield Bangladesh",
    "scenario optimization Bangladesh",
    "peak load management Bangladesh",
  ],
  alternates: { canonical: "/loadshield" },
};

const PIPELINE_STEPS = [
  { step: 1, title: "PGCB Data Ingestion", description: "Demand and supply data is scraped from the Power Grid Company of Bangladesh (PGCB) ERP portal on-demand. Data freshness depends on PGCB website update frequency." },
  { step: 2, title: "Deficit Calculation", description: "The system computes current and projected deficits by comparing peak demand forecasts against available generation capacity. Forecasts use synthetic training data." },
  { step: 3, title: "Resource Analysis", description: "Available renewable and alternative resources are evaluated for each zone — solar forecasts, wind estimates, hydro capacity, biomass potential, and waste-to-energy estimates." },
  { step: 4, title: "9-Zone Scenario Optimization", description: "A scenario optimization engine recommends resource deployment across all 9 zones to cover projected deficits. This provides decision-support, not real-time dispatch commands." },
];

const RESOURCE_TYPES = [
  { name: "Solar Forecast", classification: "FORECAST", description: "Weather-driven solar generation forecast using Open-Meteo data and XGBoost model. Not measured plant output." },
  { name: "Wind Estimate", classification: "CALCULATED", description: "Engineering power-curve model applied to 100m wind speed data. Not measured turbine generation." },
  { name: "Hydro", classification: "OFFICIAL", description: "System-wide hydro generation from PGCB ERP. Zone-level dispatch not available." },
  { name: "Biomass Potential", classification: "CALCULATED", description: "Calculated from FAOSTAT crop production data. No operational grid-connected biomass plants in Bangladesh." },
  { name: "Waste-to-Energy", classification: "CALCULATED", description: "Calculated from city waste generation data. One plant under construction (42.5 MW), none operational." },
];

function ClassificationBadge({ classification }: { classification: string }) {
  if (classification === "OFFICIAL") {
    return <span className="rounded-full bg-emerald-500/12 px-2.5 py-0.5 text-xs font-semibold text-emerald-400">{classification}</span>;
  }
  if (classification === "FORECAST") {
    return <span className="rounded-full bg-blue-500/12 px-2.5 py-0.5 text-xs font-semibold text-blue-400">{classification}</span>;
  }
  return <span className="rounded-full bg-amber-500/12 px-2.5 py-0.5 text-xs font-semibold text-amber-400">{classification}</span>;
}

export default function LoadShieldPage() {
  return (
    <div className="animate-fade-in space-y-10">
      {/* Hero */}
      <header className="space-y-4">
        <p className="text-sm font-semibold uppercase tracking-widest text-rose-400">
          Scenario-Based Decision Support
        </p>
        <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
          LoadShield — Deficit Optimization
        </h1>
        <p className="max-w-2xl text-lg text-slate-300">
          LoadShield is PowerFlex BD&rsquo;s scenario-based deficit optimization
          engine. It analyzes PGCB demand and supply data, projects future
          deficits, and recommends resource deployment across 9 zones.
        </p>
        <div className="rounded-lg border border-amber-500/25 bg-amber-500/8 p-4 text-sm text-amber-400">
          <strong>Important:</strong> LoadShield provides scenario-based
          recommendations for decision support. It does NOT issue real-time
          dispatch commands to the Bangladesh national grid.
        </div>
      </header>

      {/* CTA */}
      <div>
        <a
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded-lg bg-rose-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-rose-500"
        >
          View Dashboard
          <span aria-hidden="true">&rarr;</span>
        </a>
      </div>

      {/* How it works */}
      <article className="space-y-6">
        <h2 className="text-2xl font-bold text-white">How LoadShield Works</h2>
        <p className="max-w-2xl text-slate-300">
          The system follows a four-stage pipeline — from raw grid data
          ingestion to scenario-based resource optimization across all 9 zones.
        </p>
        <ol className="grid gap-6 sm:grid-cols-2" role="list">
          {PIPELINE_STEPS.map((item) => (
            <li
              key={item.step}
              className="space-y-3 rounded-xl border border-slate-700/30 bg-slate-800/40 p-6"
            >
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-rose-500/12 text-sm font-bold text-rose-400">
                {item.step}
              </span>
              <h3 className="text-lg font-semibold text-white">{item.title}</h3>
              <p className="text-sm text-slate-400">{item.description}</p>
            </li>
          ))}
        </ol>
      </article>

      {/* Resource Types */}
      <article className="space-y-6">
        <h2 className="text-2xl font-bold text-white">Resource Types Analyzed</h2>
        <p className="max-w-2xl text-slate-300">
          LoadShield analyzes five renewable and alternative energy resource
          types. Each has a different data classification reflecting its
          reliability and source.
        </p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {RESOURCE_TYPES.map((resource) => (
            <div
              key={resource.name}
              className="space-y-2 rounded-xl border border-slate-700/30 bg-slate-800/40 p-5"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-white">{resource.name}</h3>
                <ClassificationBadge classification={resource.classification} />
              </div>
              <p className="text-sm text-slate-400">{resource.description}</p>
            </div>
          ))}
        </div>
      </article>

      {/* Disclaimer */}
      <article className="rounded-xl border border-red-500/25 bg-red-500/8 p-6">
        <h2 className="mb-3 text-xl font-bold text-red-400">Scientific Disclaimer</h2>
        <ul className="space-y-2 text-sm text-slate-400">
          <li>LoadShield provides scenario-based decision support, not real-time grid control.</li>
          <li>Forecasts are based on synthetic training data and weather models, not historical grid performance.</li>
          <li>Biomass and waste-to-energy values are calculated potentials, not operational capacity.</li>
          <li>Battery and flexible demand values are prototype assumptions, not real assets.</li>
          <li>The system does not issue dispatch commands to the Bangladesh national grid.</li>
        </ul>
      </article>
    </div>
  );
}
