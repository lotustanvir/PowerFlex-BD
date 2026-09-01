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

export default function WasteToEnergyPage() {
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

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100">
      <section className="mx-auto max-w-4xl px-6 py-16">
        <h1 className="text-4xl font-bold tracking-tight text-white">
          Waste-to-Energy — Bangladesh
        </h1>

        <p className="mt-6 text-lg leading-relaxed text-gray-300">
          Bangladesh generates over <strong>24,000 tonnes of municipal solid
          waste daily</strong>, yet virtually none of it is currently converted to
          energy. This page outlines the status of waste-to-energy (WtE) projects,
          the calculated electricity potential from municipal waste, and the gap
          between current capacity and what is achievable.
        </p>

        <div className="mt-10 rounded-lg border border-red-700/40 bg-red-950/30 p-6">
          <h2 className="text-xl font-semibold text-red-400">
            Zero Operational WtE Plants
          </h2>
          <p className="mt-3 text-gray-300">
            As of the latest available data, Bangladesh has{" "}
            <strong>no fully operational grid-connected waste-to-energy
            plant</strong>. The Aminbazar and Matuail projects are under
            construction and have not yet begun commercial generation. Existing
            waste management remains almost entirely landfill-based.
          </p>
        </div>

        <div className="mt-10">
          <h2 className="text-2xl font-semibold text-white">
            Key Projects
          </h2>
          <div className="mt-4 grid gap-6 sm:grid-cols-2">
            {projects.map((project) => (
              <article
                key={project.name}
                className="rounded-lg border border-gray-800 bg-gray-900 p-6"
              >
                <h3 className="text-lg font-medium text-emerald-400">
                  {project.name}
                </h3>
                <div className="mt-3 flex flex-wrap gap-3 text-sm">
                  <span className="rounded-full bg-gray-800 px-3 py-1 text-gray-300">
                    Capacity: {project.capacity}
                  </span>
                  <span className="rounded-full bg-gray-800 px-3 py-1 text-gray-300">
                    {project.location}
                  </span>
                  <span className="rounded-full bg-yellow-900/50 px-3 py-1 text-yellow-400">
                    {project.status}
                  </span>
                </div>
                <p className="mt-3 text-sm text-gray-400">{project.description}</p>
              </article>
            ))}
          </div>
        </div>

        <div className="mt-10">
          <h2 className="text-2xl font-semibold text-white">
            Calculated Potential
          </h2>
          <p className="mt-4 text-gray-300">
            Using standard waste composition analysis for South Asian cities
            (organic fraction ~60–70%, recyclables ~15–20%, inert ~10–15%) and
            assumed net calorific values for each fraction, we calculate the
            theoretical electricity potential from Bangladesh's total MSW
            generation. Conservative estimates suggest over{" "}
            <strong>1,500 MW of recoverable capacity</strong> if all generated
            waste were processed through modern WtE facilities.
          </p>
          <p className="mt-3 text-gray-300">
            The dashboard applies per-city waste generation rates, population
            data, and conversion efficiencies to produce division-level and
            city-level breakdowns.
          </p>
        </div>

        <div className="mt-12">
          <a
            href="/dashboard"
            className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-emerald-500"
          >
            Open the Dashboard for Live Calculations →
          </a>
        </div>
      </section>
    </main>
  );
}
