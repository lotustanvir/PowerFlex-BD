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

export default function ResourcesPage() {
  const renewableResources = [
    {
      name: "Solar",
      classification: "LIVE",
      description:
        "Grid-connected and rooftop solar installations. Data sourced from PGCB real-time dispatch and SREDA installed capacity registers. Growing rapidly with national targets of 30% renewables by 2041.",
    },
    {
      name: "Wind",
      classification: "LIVE",
      description:
        "Coastal and offshore wind installations, primarily in the Bay of Bengal corridor. Limited operational capacity but strong theoretical potential along the Chittagong–Cox&apos;s Bazar coastline.",
    },
    {
      name: "Hydro",
      classification: "LIVE",
      description:
        "Small-scale hydroelectric plants in the hilly regions of Sylhet and Chittagong Hill Tracts. Marginal contribution to national grid but valuable for off-grid electrification.",
    },
    {
      name: "Biomass",
      classification: "CALCULATED",
      description:
        "Energy from crop residue, agricultural waste, and dedicated energy crops. Potential is calculated from FAOSTAT crop production data using residue-to-product ratios. Not yet a significant grid contributor.",
    },
    {
      name: "Waste-to-Energy",
      classification: "CALCULATED",
      description:
        "Electricity from municipal solid waste incineration and anaerobic digestion. All values are calculated estimates — no operational WtE plants are currently feeding the grid.",
    },
  ];

  const conventionalResources = [
    {
      name: "Gas",
      classification: "LIVE",
      description:
        "Natural gas is Bangladesh&apos;s dominant generation fuel, accounting for over 50% of grid electricity. Data from Petrobangla and PGCB dispatch records. Reserves are declining, increasing reliance on imported LNG.",
    },
    {
      name: "Liquid Fuel",
      classification: "LIVE",
      description:
        "Diesel and furnace oil peaking plants. High marginal cost limits usage to peak demand and emergency supply. PGCB dispatch data provides real-time generation figures.",
    },
    {
      name: "Coal",
      classification: "LIVE",
      description:
        "Coal-fired plants including the Payra 1,320 MW facility. Generation data from PGCB. New capacity is being added but coal remains a minority fuel compared to gas.",
    },
    {
      name: "Nuclear",
      classification: "PLANNED",
      description:
        "The Rooppur Nuclear Power Plant (2,400 MW) is under construction with Russian assistance. Not yet operational. When commissioned, it will be Bangladesh&apos;s largest single generation source.",
    },
  ];

  const dataClassifications = [
    {
      label: "LIVE",
      color: "text-emerald-400",
      bg: "bg-emerald-950/40 border-emerald-700/40",
      definition:
        "Data sourced from real-time or near-real-time grid monitoring (PGCB SCADA, dispatch records). Updated every 15 minutes to hourly.",
    },
    {
      label: "CALCULATED",
      color: "text-amber-400",
      bg: "bg-amber-950/40 border-amber-700/40",
      definition:
        "Values derived from applying engineering conversion factors to official production statistics. Not measured in real time. Updated when source datasets are revised.",
    },
    {
      label: "PLANNED",
      color: "text-blue-400",
      bg: "bg-blue-950/40 border-blue-700/40",
      definition:
        "Capacity that is under construction or in advanced planning stages. No generation data available yet. Capacity figures from project announcements.",
    },
  ];

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100">
      <section className="mx-auto max-w-5xl px-6 py-16">
        <h1 className="text-4xl font-bold tracking-tight text-white">
          Energy Resources — Bangladesh
        </h1>

        <p className="mt-6 text-lg leading-relaxed text-gray-300">
          Bangladesh&apos;s electricity grid draws from{" "}
          <strong>9 distinct resource types</strong>. Each is classified by data
          reliability — whether it comes from live grid monitoring, calculated
          estimates, or forward-looking capacity plans. Understanding this
          classification is essential for interpreting the dashboard numbers.
        </p>

        <div className="mt-10">
          <h2 className="text-2xl font-semibold text-white">
            Renewable Resources
          </h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {renewableResources.map((resource) => (
              <article
                key={resource.name}
                className="rounded-lg border border-gray-800 bg-gray-900 p-5"
              >
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-emerald-400">
                    {resource.name}
                  </h3>
                  <span className="rounded-full bg-gray-800 px-2.5 py-0.5 text-xs font-medium text-gray-300">
                    {resource.classification}
                  </span>
                </div>
                <p className="mt-2 text-sm text-gray-400">
                  {resource.description}
                </p>
              </article>
            ))}
          </div>
        </div>

        <div className="mt-10">
          <h2 className="text-2xl font-semibold text-white">
            Conventional Resources
          </h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {conventionalResources.map((resource) => (
              <article
                key={resource.name}
                className="rounded-lg border border-gray-800 bg-gray-900 p-5"
              >
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-200">
                    {resource.name}
                  </h3>
                  <span className="rounded-full bg-gray-800 px-2.5 py-0.5 text-xs font-medium text-gray-300">
                    {resource.classification}
                  </span>
                </div>
                <p className="mt-2 text-sm text-gray-400">
                  {resource.description}
                </p>
              </article>
            ))}
          </div>
        </div>

        <div className="mt-10">
          <h2 className="text-2xl font-semibold text-white">
            Data Classification
          </h2>
          <p className="mt-4 text-gray-300">
            Every resource on this platform carries a data classification label.
            This tells you how the number was produced and how current it is.
          </p>
          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            {dataClassifications.map((cls) => (
              <div
                key={cls.label}
                className={`rounded-lg border p-5 ${cls.bg}`}
              >
                <h3 className={`text-lg font-semibold ${cls.color}`}>
                  {cls.label}
                </h3>
                <p className="mt-2 text-sm text-gray-400">{cls.definition}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-12">
          <a
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-emerald-500"
          >
            Open the Dashboard for Live Data →
          </a>
        </div>
      </section>
    </main>
  );
}
