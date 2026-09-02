import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Bangladesh Energy Resources — PowerFlex BD",
  description:
    "Overview of all 9 Bangladesh electricity resources: solar, wind, hydro, biomass, waste-to-energy, gas, liquid fuel, coal, and nuclear. Current generation, installed capacity, and data classification for each resource.",
  keywords: [
    "Bangladesh electricity resources",
    "Bangladesh power generation",
    "PGCB generation data",
    "Bangladesh energy mix",
  ],
  alternates: { canonical: "/resources" },
};

const renewableResources = [
  {
    name: "Solar",
    classification: "FORECAST",
    description:
      "Current generation from PGCB ERP (when available). Zone-level forecasts from weather-driven Solar AI model (experimental, not validated against real data). Installed capacity ~757 MW (BPDB/SREDA).",
  },
  {
    name: "Wind",
    classification: "CALCULATED",
    description:
      "Current generation from PGCB ERP (when available). Zone-level estimates from wind power curve model (experimental). Installed capacity ~62 MW. Strong theoretical potential along Chittagong–Cox's Bazar coastline.",
  },
  {
    name: "Hydro",
    classification: "OFFICIAL",
    description:
      "Kaptai Dam (Karnafuli) — only hydro plant in Bangladesh. 230 MW installed. Current generation from PGCB ERP. System-wide only, no zone-level dispatch data.",
  },
  {
    name: "Biomass",
    classification: "CALCULATED",
    description:
      "Calculated potential from FAOSTAT crop production data. No utility-scale grid-connected biomass power plant is operational in Bangladesh. Only off-grid micro-projects exist (~400 kWp total).",
  },
  {
    name: "Waste-to-Energy",
    classification: "CALCULATED",
    description:
      "Calculated from city waste generation data. North Dhaka WtE Plant (42.5 MW) under construction. No operational WtE plants currently feeding the grid.",
  },
];

const conventionalResources = [
  {
    name: "Gas",
    classification: "OFFICIAL",
    description:
      "Natural gas is Bangladesh's dominant generation fuel, accounting for over 50% of grid electricity. Data from PGCB ERP generation breakdown. Installed ~12,194 MW (BPDB Jul 2026).",
  },
  {
    name: "Liquid Fuel",
    classification: "OFFICIAL",
    description:
      "Diesel and furnace oil peaking plants. High marginal cost limits usage to peak demand and emergency supply. Data from PGCB ERP generation breakdown.",
  },
  {
    name: "Coal",
    classification: "OFFICIAL",
    description:
      "Coal-fired plants including Payra 1,320 MW facility. Data from PGCB ERP generation breakdown. Includes domestic plants + Adani Godda import. Total ~7,629 MW installed.",
  },
  {
    name: "Nuclear",
    classification: "UNDER_COMMISSIONING",
    description:
      "Rooppur Nuclear Power Plant (2,400 MW) under commissioning with Russian assistance. Unit 1 fuel loading began Apr 2026. First grid connection expected mid-2026. Not yet generating to grid.",
  },
];

const dataClassifications = [
  {
    label: "OFFICIAL",
    color: "text-emerald-400",
    bg: "bg-emerald-500/8 border-emerald-500/25",
    definition:
      "Verified data from government or institutional sources (e.g., PGCB ERP). Highest reliability classification.",
  },
  {
    label: "FORECAST",
    color: "text-blue-400",
    bg: "bg-blue-500/8 border-blue-500/25",
    definition:
      "Weather-driven or ML-driven predictions. Not measured data. May be experimental if not validated against real operational data.",
  },
  {
    label: "CALCULATED",
    color: "text-amber-400",
    bg: "bg-amber-500/8 border-amber-500/25",
    definition:
      "Engineering or physics-based calculations from available data. Not real-time measurements.",
  },
  {
    label: "UNDER_COMMISSIONING",
    color: "text-orange-400",
    bg: "bg-orange-500/8 border-orange-500/25",
    definition:
      "Capacity that is physically under construction or commissioning. No generation data available yet.",
  },
];

function ClassificationBadge({ classification }: { classification: string }) {
  if (classification === "OFFICIAL") {
    return <span className="rounded-full bg-emerald-500/12 px-2.5 py-0.5 text-xs font-semibold text-emerald-400">{classification}</span>;
  }
  if (classification === "FORECAST") {
    return <span className="rounded-full bg-blue-500/12 px-2.5 py-0.5 text-xs font-semibold text-blue-400">{classification}</span>;
  }
  if (classification === "UNDER_COMMISSIONING") {
    return <span className="rounded-full bg-orange-500/12 px-2.5 py-0.5 text-xs font-semibold text-orange-400">{classification}</span>;
  }
  return <span className="rounded-full bg-amber-500/12 px-2.5 py-0.5 text-xs font-semibold text-amber-400">{classification}</span>;
}

export default function ResourcesPage() {
  return (
    <div className="animate-fade-in space-y-12">
      {/* Hero */}
      <header className="space-y-4">
        <p className="text-sm font-semibold uppercase tracking-widest text-emerald-400">
          Energy Resource Intelligence
        </p>
        <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
          Energy Resources — Bangladesh
        </h1>
        <p className="max-w-2xl text-lg text-slate-300">
          Bangladesh&apos;s electricity grid draws from{" "}
          <strong>9 distinct resource types</strong>. Each is classified by data
          reliability — whether it comes from live grid monitoring, calculated
          estimates, or forward-looking capacity plans. Understanding this
          classification is essential for interpreting the dashboard numbers.
        </p>
      </header>

      {/* CTA */}
      <div>
        <a
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-emerald-500"
        >
          Open the Dashboard for Live Data
          <span aria-hidden="true">&rarr;</span>
        </a>
      </div>

      {/* Renewable Resources */}
      <article className="space-y-6">
        <h2 className="text-2xl font-bold text-white">
          Renewable Resources
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {renewableResources.map((resource) => (
            <article
              key={resource.name}
              className="space-y-2 rounded-xl border border-slate-700/30 bg-slate-800/40 p-5"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-emerald-400">
                  {resource.name}
                </h3>
                <ClassificationBadge classification={resource.classification} />
              </div>
              <p className="text-sm text-slate-400">
                {resource.description}
              </p>
            </article>
          ))}
        </div>
      </article>

      {/* Conventional Resources */}
      <article className="space-y-6">
        <h2 className="text-2xl font-bold text-white">
          Conventional Resources
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {conventionalResources.map((resource) => (
            <article
              key={resource.name}
              className="space-y-2 rounded-xl border border-slate-700/30 bg-slate-800/40 p-5"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-slate-200">
                  {resource.name}
                </h3>
                <ClassificationBadge classification={resource.classification} />
              </div>
              <p className="text-sm text-slate-400">
                {resource.description}
              </p>
            </article>
          ))}
        </div>
      </article>

      {/* Data Classification */}
      <article className="space-y-6">
        <h2 className="text-2xl font-bold text-white">
          Data Classification
        </h2>
        <p className="text-slate-300">
          Every resource on this platform carries a data classification label.
          This tells you how the number was produced and how current it is.
        </p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {dataClassifications.map((cls) => (
            <div
              key={cls.label}
              className={`overflow-hidden rounded-lg border p-5 ${cls.bg}`}
            >
              <h3 className={`w-full text-base font-semibold ${cls.color} truncate`} title={cls.label}>
                {cls.label}
              </h3>
              <p className="mt-2 text-sm text-slate-400">{cls.definition}</p>
            </div>
          ))}
        </div>
      </article>
    </div>
  );
}
