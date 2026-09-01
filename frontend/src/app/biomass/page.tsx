import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Bangladesh Biomass Energy Potential — PowerFlex BD",
  description:
    "Calculated biomass energy potential for Bangladesh based on official crop production, livestock, and organic waste data. Division-wise analysis of crop residue, animal manure, and biogas potential from FAOSTAT, DLS, and BBS sources.",
  keywords: [
    "Bangladesh biomass energy",
    "biomass potential Bangladesh",
    "crop residue energy",
    "biogas Bangladesh",
  ],
  alternates: { canonical: "/biomass" },
};

export default function BiomassPage() {
  const dataSources = [
    {
      name: "FAOSTAT",
      role: "Crop production yields and residue-to-product ratios for rice, wheat, jute, sugarcane, and other major crops.",
    },
    {
      name: "DLS (Department of Livestock Services)",
      role: "Livestock population by species and division for manure-based biogas calculations.",
    },
    {
      name: "BBS (Bangladesh Bureau of Statistics)",
      role: "Administrative boundaries, population data, and supplementary agricultural statistics.",
    },
    {
      name: "SREDA (Sustainable and Renewable Energy Development Authority)",
      role: "National biomass energy targets and policy framework references.",
    },
  ];

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100">
      <section className="mx-auto max-w-4xl px-6 py-16">
        <h1 className="text-4xl font-bold tracking-tight text-white">
          Biomass Energy — Bangladesh
        </h1>

        <p className="mt-6 text-lg leading-relaxed text-gray-300">
          This page presents <strong>calculated biomass energy potential</strong>{" "}
          for Bangladesh derived entirely from official datasets. The figures shown
          are not live measurements — they are the result of applying established
          engineering formulas to publicly available production statistics.
        </p>

        <div className="mt-10 rounded-lg border border-amber-700/40 bg-amber-950/30 p-6">
          <h2 className="text-xl font-semibold text-amber-400">
            Calculated From Official Data — Not Live
          </h2>
          <p className="mt-3 text-gray-300">
            Every energy potential value on this platform is{" "}
            <strong>calculated</strong>, not measured in real time. We apply
            conversion factors and residue ratios to raw production data published
            by government agencies. This ensures transparency, reproducibility, and
            auditability — but it also means values reflect the most recent
            official reporting period, not real-time output.
          </p>
        </div>

        <div className="mt-10">
          <h2 className="text-2xl font-semibold text-white">Methodology</h2>
          <ol className="mt-4 list-decimal space-y-3 pl-6 text-gray-300">
            <li>
              <strong>Crop residue estimation:</strong> For each major crop (rice,
              wheat, jute, sugarcane, maize, potato), we multiply total production
              by documented residue-to-product ratios (RPR) to obtain dry residue
              mass.
            </li>
            <li>
              <strong>Energy conversion:</strong> Residue mass is multiplied by
              the lower heating value (LHV) specific to each residue type,
              yielding thermal energy in GJ and electricity potential in GWh
              assuming typical boiler and turbine efficiencies.
            </li>
            <li>
              <strong>Animal manure potential:</strong> Livestock population
              counts are multiplied by per-head daily excretion rates, dried, and
              converted to biogas yield using standard methane content assumptions
              (60% CH₄).
            </li>
            <li>
              <strong>Organic waste:</strong> Municipal organic waste volumes are
              estimated from per-capita waste generation rates and urban population
              data, then converted to electricity potential via anaerobic digestion
              or direct combustion pathways.
            </li>
            <li>
              <strong>Divisional aggregation:</strong> All results are rolled up
              to Bangladesh&apos;s 8 administrative divisions for
              geographic comparison.
            </li>
          </ol>
        </div>

        <div className="mt-10">
          <h2 className="text-2xl font-semibold text-white">Data Sources</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {dataSources.map((source) => (
              <article
                key={source.name}
                className="rounded-lg border border-gray-800 bg-gray-900 p-5"
              >
                <h3 className="text-lg font-medium text-emerald-400">
                  {source.name}
                </h3>
                <p className="mt-2 text-sm text-gray-400">{source.role}</p>
              </article>
            ))}
          </div>
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
