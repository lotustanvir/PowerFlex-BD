import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "PowerFlex BD Solar AI — Bangladesh Solar Forecast & Zone Intelligence",
  description:
    "AI-powered solar energy forecasting for Bangladesh. PowerFlex BD Solar AI analyzes weather data across 9 zones to predict solar generation potential, radiation levels, and optimal installation locations.",
  keywords: [
    "Bangladesh solar forecast",
    "solar energy potential Bangladesh",
    "solar zone ranking Bangladesh",
    "AI solar prediction",
  ],
  alternates: { canonical: "/solar" },
};

const ZONES = [
  { id: 1, name: "Dhaka Division", avgGHI: "4.2 kWh/m²/day", potential: "High" },
  { id: 2, name: "Chittagong Division", avgGHI: "4.5 kWh/m²/day", potential: "Very High" },
  { id: 3, name: "Rajshahi Division", avgGHI: "4.8 kWh/m²/day", potential: "Very High" },
  { id: 4, name: "Rangpur Division", avgGHI: "4.6 kWh/m²/day", potential: "Very High" },
  { id: 5, name: "Khulna Division", avgGHI: "4.3 kWh/m²/day", potential: "High" },
  { id: 6, name: "Barishal Division", avgGHI: "4.1 kWh/m²/day", potential: "Moderate" },
  { id: 7, name: "Sylhet Division", avgGHI: "3.9 kWh/m²/day", potential: "Moderate" },
  { id: 8, name: "Mymensingh Division", avgGHI: "4.4 kWh/m²/day", potential: "High" },
  { id: 9, name: "Cox's Bazar Coastal", avgGHI: "4.7 kWh/m²/day", potential: "Very High" },
];

const METHOD_STEPS = [
  { step: 1, title: "Weather Data Ingestion", description: "Open-Meteo API delivers hourly global horizontal irradiance (GHI), direct normal irradiance (DNI), diffuse horizontal irradiance (DHI), cloud cover, temperature, and humidity for every point across Bangladesh." },
  { step: 2, title: "Solar Resource Mapping", description: "Raw irradiance data is spatially interpolated and averaged per zone to compute daily energy density maps and historical irradiance profiles." },
  { step: 3, title: "ML Forecasting", description: "A gradient-boosted regression model trained on 5 years of historical solar output and weather patterns generates 7-day solar generation forecasts for each zone." },
  { step: 4, title: "Zone Ranking", description: "Each zone is scored on a composite index of average GHI, forecast confidence, grid proximity, and land suitability — producing a ranked leaderboard." },
];

export default function SolarPage() {
  return (
    <section className="space-y-12">
      {/* Hero */}
      <header className="space-y-4">
        <p className="text-sm font-semibold uppercase tracking-widest text-emerald-400">
          Renewable Intelligence
        </p>
        <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
          Solar AI — Bangladesh
        </h1>
        <p className="max-w-2xl text-lg text-slate-300">
          PowerFlex BD Solar AI delivers AI-powered solar energy forecasting
          across Bangladesh&rsquo;s 9 administrative divisions. By fusing
          real-time weather data with machine-learning models, it predicts
          solar generation potential, identifies optimal installation sites,
          and ranks zones by irradiance quality — giving policymakers,
          developers, and utilities actionable intelligence.
        </p>
      </header>

      {/* CTA */}
      <div>
        <a
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-emerald-500"
        >
          View Live Dashboard
          <span aria-hidden="true">&rarr;</span>
        </a>
      </div>

      {/* How it works */}
      <article className="space-y-6">
        <h2 className="text-2xl font-bold text-white">Methodology</h2>
        <p className="max-w-2xl text-slate-300">
          Solar AI combines Open-Meteo&rsquo;s open weather data with a
          proprietary ML model to forecast solar irradiance and generation
          potential at zone level. The pipeline runs four stages from raw
          data ingestion to final zone ranking.
        </p>
        <ol className="grid gap-6 sm:grid-cols-2" role="list">
          {METHOD_STEPS.map((item) => (
            <li
              key={item.step}
              className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 space-y-2"
            >
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-emerald-600/20 text-sm font-bold text-emerald-400">
                {item.step}
              </span>
              <h3 className="text-lg font-semibold text-white">{item.title}</h3>
              <p className="text-sm text-slate-400">{item.description}</p>
            </li>
          ))}
        </ol>
      </article>

      {/* 9 Zones */}
      <article className="space-y-6">
        <h2 className="text-2xl font-bold text-white">9 Solar Zones</h2>
        <p className="max-w-2xl text-slate-300">
          Bangladesh is divided into 9 administrative divisions. Each zone is
          independently assessed for solar irradiance, forecast confidence,
          and installation suitability.
        </p>
        <div className="overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-800 bg-slate-900/80">
              <tr>
                <th className="px-4 py-3 font-semibold text-slate-300">#</th>
                <th className="px-4 py-3 font-semibold text-slate-300">Zone</th>
                <th className="px-4 py-3 font-semibold text-slate-300">Avg GHI</th>
                <th className="px-4 py-3 font-semibold text-slate-300">Potential</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {ZONES.map((zone) => (
                <tr key={zone.id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-4 py-3 text-slate-500">{zone.id}</td>
                  <td className="px-4 py-3 font-medium text-white">{zone.name}</td>
                  <td className="px-4 py-3 text-slate-300">{zone.avgGHI}</td>
                  <td className="px-4 py-3">
                    <span
                      className={
                        zone.potential === "Very High"
                          ? "rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-xs font-semibold text-emerald-400"
                          : zone.potential === "High"
                            ? "rounded-full bg-amber-500/20 px-2.5 py-0.5 text-xs font-semibold text-amber-400"
                            : "rounded-full bg-slate-500/20 px-2.5 py-0.5 text-xs font-semibold text-slate-400"
                      }
                    >
                      {zone.potential}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
    </section>
  );
}
