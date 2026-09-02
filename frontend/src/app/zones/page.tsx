import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "9-Zone Renewable Energy Analysis — Bangladesh | PowerFlex BD",
  description:
    "Comprehensive 9-zone renewable energy analysis for Bangladesh. Solar, wind, biomass, and waste-to-energy potential for Dhaka, Chittagong, Comilla, Khulna, Rajshahi, Mymensingh, Sylhet, Barishal, and Rangpur zones.",
  keywords: [
    "Bangladesh renewable energy zones",
    "9 zone analysis Bangladesh",
    "solar potential zones Bangladesh",
    "wind potential zones Bangladesh",
  ],
  alternates: { canonical: "/zones" },
};

const zones = [
  {
    name: "Dhaka",
    description:
      "Highest waste-to-energy potential in the country due to dense urban population. Moderate solar irradiance. Limited wind resources.",
  },
  {
    name: "Chittagong",
    description:
      "Coastal location provides strong wind corridors, especially along the bay. High solar potential and significant industrial waste streams.",
  },
  {
    name: "Comilla",
    description:
      "Transitional zone between delta and hills. Balanced solar irradiance. Moderate biomass availability from rice and jute cultivation.",
  },
  {
    name: "Khulna",
    description:
      "Sundarbans-adjacent delta region. Strong solar resource. Coastal wind potential. Significant agricultural residue from rice monoculture.",
  },
  {
    name: "Rajshahi",
    description:
      "Northwestern high-solar zone with Bangladesh's highest average irradiance. Major fruit and crop belt contributing substantial biomass residue.",
  },
  {
    name: "Mymensingh",
    description:
      "Northern agricultural heartland. Very high biomass potential from rice, wheat, and maize. Good solar resource with moderate wind.",
  },
  {
    name: "Sylhet",
    description:
      "Hilly northeastern region with unique microclimate. Lower solar due to cloud cover. Moderate biomass. Potential for small-scale hydro.",
  },
  {
    name: "Barishal",
    description:
      "Southern delta with high humidity reducing solar efficiency. Strong coastal wind potential. Significant organic waste from riverine agriculture.",
  },
  {
    name: "Rangpur",
    description:
      "Far-northwestern region with high solar irradiance. Major wheat and tobacco producing area with good biomass residue potential.",
  },
];

export default function ZonesPage() {
  return (
    <div className="animate-fade-in space-y-12">
      {/* Hero */}
      <header className="space-y-4">
        <p className="text-sm font-semibold uppercase tracking-widest text-emerald-400">
          Geographic Resource Mapping
        </p>
        <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
          9-Zone Analysis — Bangladesh
        </h1>
        <p className="max-w-2xl text-lg text-slate-300">
          Bangladesh is divided into <strong>9 analytical zones</strong> for
          renewable energy assessment. Each zone is evaluated across four energy
          dimensions: solar, wind, biomass, and waste-to-energy. This
          zone-based approach reveals the geographic diversity of Bangladesh&apos;s
          renewable resource landscape and enables targeted investment decisions.
        </p>
      </header>

      {/* CTA */}
      <div>
        <a
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-emerald-500"
        >
          Open the Dashboard for Live Rankings
          <span aria-hidden="true">&rarr;</span>
        </a>
      </div>

      {/* 9 Zones */}
      <article className="space-y-6">
        <h2 className="text-2xl font-bold text-white">The 9 Zones</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {zones.map((zone) => (
            <article
              key={zone.name}
              className="rounded-xl border border-slate-700/30 bg-slate-800/40 p-5"
            >
              <h3 className="text-lg font-medium text-emerald-400">
                {zone.name}
              </h3>
              <p className="mt-2 text-sm text-slate-400">{zone.description}</p>
            </article>
          ))}
        </div>
      </article>

      {/* Methodology */}
      <article className="space-y-4">
        <h2 className="text-2xl font-bold text-white">Methodology</h2>
        <p className="text-slate-300">
          Each zone&apos;s renewable energy potential is computed by aggregating
          four independent models:
        </p>
        <ul className="mt-4 list-disc space-y-3 pl-6 text-slate-300">
          <li>
            <strong>Solar AI:</strong> Satellite-derived global horizontal
            irradiance (GHI) data processed through a machine learning model
            trained on ground-station measurements. Produces zone-level average
            daily solar insolation (kWh/m²/day).
          </li>
          <li>
            <strong>Wind AI:</strong> Mesoscale wind resource assessment
            combining ERA5 reanalysis data with coastal and topographic
            corrections. Outputs average wind speed and power density at 80m hub
            height.
          </li>
          <li>
            <strong>Biomass:</strong> Division-level crop production data
            multiplied by residue-to-product ratios and energy conversion
            factors. Aggregated per zone using administrative boundary
            mapping.
          </li>
          <li>
            <strong>Waste-to-Energy:</strong> Municipal solid waste generation
            estimates from population and per-capita rates, converted to
            electricity potential using standard incineration and anaerobic
            digestion efficiencies.
          </li>
        </ul>
      </article>

      {/* Live Rankings */}
      <article className="space-y-4">
        <h2 className="text-2xl font-bold text-white">
          Live Rankings
        </h2>
        <p className="text-slate-300">
          The dashboard computes composite scores for each zone by normalizing
          all four resource dimensions and applying configurable weights. This
          produces a ranked list showing which zones offer the greatest overall
          renewable energy opportunity.
        </p>
      </article>
    </div>
  );
}
