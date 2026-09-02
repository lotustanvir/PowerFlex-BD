import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Bangladesh Waste-to-Energy Intelligence — PowerFlex BD",
  description:
    "Waste-to-energy intelligence for Bangladesh. Analysis of city waste generation, WtE projects including Aminbazar and Matuail, and calculated electricity potential from municipal solid waste.",
  keywords: [
    "Bangladesh waste to energy",
    "WtE Bangladesh",
    "Aminbazar waste to energy",
    "municipal waste Bangladesh",
  ],
  alternates: { canonical: "/waste-to-energy" },
};

const projects = [
  {
    name: "Aminbazar WtE Plant",
    capacity: "42.5 MW",
    location: "Aminbazar, Dhaka",
    status: "Under construction",
    description:
      "Bangladesh's flagship waste-to-energy project. Designed to process approximately 3,000 tonnes of municipal solid waste per day from Dhaka city, generating 42.5 MW of electricity through incineration with energy recovery.",
  },
  {
    name: "Matuail WtE Plant",
    capacity: "9.1 MW",
    location: "Matuail, Dhaka",
    status: "Under construction",
    description:
      "A smaller-scale facility targeting waste from the Matuail landfill area. Expected to process around 600 tonnes per day with a generation capacity of 9.1 MW.",
  },
];

export default function WasteToEnergyPage() {
  return (
    <div className="animate-fade-in space-y-10">
      {/* Hero */}
      <header className="space-y-4">
        <p className="text-sm font-semibold uppercase tracking-widest text-emerald-400">
          Municipal Waste Intelligence
        </p>
        <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
          Waste-to-Energy — Bangladesh
        </h1>
        <p className="max-w-2xl text-lg text-slate-300">
          Bangladesh generates over <strong>24,000 tonnes of municipal solid
          waste daily</strong>, yet virtually none of it is currently converted to
          energy. This page outlines the status of waste-to-energy (WtE) projects,
          the calculated electricity potential from municipal waste, and the gap
          between current capacity and what is achievable.
        </p>
      </header>

      {/* CTA */}
      <div>
        <a
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-emerald-500"
        >
          Open the Dashboard for Live Calculations
          <span aria-hidden="true">&rarr;</span>
        </a>
      </div>

      {/* Notice */}
      <div className="rounded-lg border border-red-500/25 bg-red-500/8 p-6">
        <h2 className="text-xl font-semibold text-red-400">
          Zero Operational WtE Plants
        </h2>
        <p className="mt-3 text-slate-300">
          As of the latest available data, Bangladesh has{" "}
          <strong>no fully operational grid-connected waste-to-energy
          plant</strong>. The Aminbazar and Matuail projects are under
          construction and have not yet begun commercial generation. Existing
          waste management remains almost entirely landfill-based.
        </p>
      </div>

      {/* Key Projects */}
      <article className="space-y-6">
        <h2 className="text-2xl font-bold text-white">
          Key Projects
        </h2>
        <div className="grid gap-6 sm:grid-cols-2">
          {projects.map((project) => (
            <article
              key={project.name}
              className="space-y-3 rounded-xl border border-slate-700/30 bg-slate-800/40 p-6"
            >
              <h3 className="text-lg font-medium text-emerald-400">
                {project.name}
              </h3>
              <div className="flex flex-wrap gap-3 text-sm">
                <span className="rounded-full bg-slate-900/60 px-3 py-1 text-slate-300">
                  Capacity: {project.capacity}
                </span>
                <span className="rounded-full bg-slate-900/60 px-3 py-1 text-slate-300">
                  {project.location}
                </span>
                <span className="rounded-full bg-yellow-500/12 px-3 py-1 text-yellow-400">
                  {project.status}
                </span>
              </div>
              <p className="text-sm text-slate-400">{project.description}</p>
            </article>
          ))}
        </div>
      </article>

      {/* Calculated Potential */}
      <article className="space-y-4">
        <h2 className="text-2xl font-bold text-white">
          Calculated Potential
        </h2>
        <p className="text-slate-300">
          Using standard waste composition analysis for South Asian cities
          (organic fraction ~60–70%, recyclables ~15–20%, inert ~10–15%) and
          assumed net calorific values for each fraction, we calculate the
          theoretical electricity potential from Bangladesh&apos;s total MSW
          generation. Conservative estimates suggest over{" "}
          <strong>1,500 MW of recoverable capacity</strong> if all generated
          waste were processed through modern WtE facilities.
        </p>
        <p className="text-slate-300">
          The dashboard applies per-city waste generation rates, population
          data, and conversion efficiencies to produce division-level and
          city-level breakdowns.
        </p>
      </article>
    </div>
  );
}
