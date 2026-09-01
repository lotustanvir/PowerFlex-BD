import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "LoadShield — AI-Powered Peak Load & Deficit Optimization for Bangladesh",
  description:
    "LoadShield is PowerFlex BD's AI-powered grid protection system. It analyzes real-time PGCB demand and supply data to optimize deficit coverage across solar, wind, hydro, biomass, and waste-to-energy resources.",
  keywords: [
    "Bangladesh load shedding",
    "Bangladesh power deficit",
    "LoadShield Bangladesh",
    "AI grid optimization",
    "peak load management Bangladesh",
  ],
  alternates: { canonical: "/loadshield" },
};

const PIPELINE_STEPS = [
  { step: 1, title: "PGCB Data Ingestion", icon: "⚡", description: "Real-time demand and supply data is pulled from the Power Grid Company of Bangladesh (PGCB) ERP, capturing national load, frequency, and reserve margin every 15 minutes." },
  { step: 2, title: "Deficit Calculation", icon: "📉", description: "The system computes current and projected deficits by comparing peak demand forecasts against available generation capacity, factoring in maintenance schedules and historical load curves." },
  { step: 3, title: "Resource Analysis", icon: "🔋", description: "Available renewable and alternative resources are evaluated for each zone — solar irradiance, wind speed, hydro flow, biomass feedstock, and waste-to-energy input — to estimate real-time dispatchable capacity." },
  { step: 4, title: "9-Zone Dispatch", icon: "🗺️", description: "An optimization engine distributes the deficit load across all 9 zones, matching available resources to demand nodes while minimizing transmission losses and curtailment." },
];

const RESOURCE_TYPES = [
  { name: "Solar PV", contribution: "~8.5%", description: "Grid-scale and distributed solar feeding into the national grid during daylight hours." },
  { name: "Wind", contribution: "~4.2%", description: "Utility-scale wind farms, primarily in coastal zones, contributing variable output." },
  { name: "Hydro", contribution: "~3.5%", description: "Run-of-river and small hydro plants providing baseload and peaking support." },
  { name: "Biomass", contribution: "~6.0%", description: "Agricultural waste-to-energy plants converting jute, rice husk, and bagasse into electricity." },
  { name: "Waste-to-Energy", contribution: "~1.8%", description: "Municipal solid waste incineration and biogas plants generating power from urban waste streams." },
];

export default function LoadShieldPage() {
  return (
    <section className="space-y-12">
      {/* Hero */}
      <header className="space-y-4">
        <p className="text-sm font-semibold uppercase tracking-widest text-rose-400">
          Grid Protection
        </p>
        <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
          LoadShield — AI Grid Protection
        </h1>
        <p className="max-w-2xl text-lg text-slate-300">
          LoadShield is PowerFlex BD&rsquo;s AI-powered grid protection
          system. It continuously monitors PGCB demand and supply data,
          detects emerging deficits, and dispatches renewable resources
          across 9 zones to minimize load shedding and stabilize the
          national grid.
        </p>
      </header>

      {/* CTA */}
      <div>
        <a
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded-lg bg-rose-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-rose-500"
        >
          View Live Dashboard
          <span aria-hidden="true">&rarr;</span>
        </a>
      </div>

      {/* How it works */}
      <article className="space-y-6">
        <h2 className="text-2xl font-bold text-white">How LoadShield Works</h2>
        <p className="max-w-2xl text-slate-300">
          The system follows a four-stage pipeline — from raw grid data
          ingestion to optimized resource dispatch across all 9 zones.
        </p>
        <ol className="grid gap-6 sm:grid-cols-2" role="list">
          {PIPELINE_STEPS.map((item) => (
            <li
              key={item.step}
              className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 space-y-3"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl" aria-hidden="true">{item.icon}</span>
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-rose-600/20 text-sm font-bold text-rose-400">
                  {item.step}
                </span>
              </div>
              <h3 className="text-lg font-semibold text-white">{item.title}</h3>
              <p className="text-sm text-slate-400">{item.description}</p>
            </li>
          ))}
        </ol>
      </article>

      {/* Resource Types */}
      <article className="space-y-6">
        <h2 className="text-2xl font-bold text-white">Dispatchable Resources</h2>
        <p className="max-w-2xl text-slate-300">
          LoadShield aggregates five renewable and alternative energy
          resource types for deficit coverage. Each resource contributes a
          share of the total dispatchable capacity.
        </p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {RESOURCE_TYPES.map((resource) => (
            <div
              key={resource.name}
              className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-2"
            >
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-white">{resource.name}</h3>
                <span className="rounded-full bg-rose-500/20 px-2.5 py-0.5 text-xs font-semibold text-rose-400">
                  {resource.contribution}
                </span>
              </div>
              <p className="text-sm text-slate-400">{resource.description}</p>
            </div>
          ))}
        </div>
      </article>
    </section>
  );
}
