import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "PowerFlex BD Wind Estimation — Bangladesh Wind Energy Intelligence",
  description:
    "Engineering-based wind energy estimation for Bangladesh. PowerFlex BD Wind AI analyzes 100m wind speed data across 9 zones using power curve analysis to estimate wind generation potential.",
  keywords: [
    "Bangladesh wind forecast",
    "wind energy potential Bangladesh",
    "wind zone ranking Bangladesh",
    "wind estimation Bangladesh",
  ],
  alternates: { canonical: "/wind" },
};

const ZONES = [
  { id: 1, name: "Dhaka Division", avgSpeed: "4.2 m/s", potential: "Moderate" },
  { id: 2, name: "Chittagong Division", avgSpeed: "5.8 m/s", potential: "High" },
  { id: 3, name: "Rajshahi Division", avgSpeed: "4.5 m/s", potential: "Moderate" },
  { id: 4, name: "Rangpur Division", avgSpeed: "4.8 m/s", potential: "Moderate" },
  { id: 5, name: "Khulna Division", avgSpeed: "5.3 m/s", potential: "High" },
  { id: 6, name: "Barishal Division", avgSpeed: "6.1 m/s", potential: "Very High" },
  { id: 7, name: "Sylhet Division", avgSpeed: "3.7 m/s", potential: "Low" },
  { id: 8, name: "Mymensingh Division", avgSpeed: "4.0 m/s", potential: "Low" },
  { id: 9, name: "Cox's Bazar Coastal", avgSpeed: "7.2 m/s", potential: "Very High" },
];

const POWER_CURVE_INFO = [
  { label: "Cut-in Speed", value: "3–4 m/s", description: "Minimum wind speed at which the turbine begins generating electricity." },
  { label: "Rated Speed", value: "12–14 m/s", description: "Speed at which the turbine reaches its maximum rated power output." },
  { label: "Cut-out Speed", value: "25 m/s", description: "Maximum safe operating speed; turbine shuts down above this threshold." },
  { label: "Optimal Range", value: "8–14 m/s", description: "Wind speed band where turbines operate at peak efficiency." },
];

function PotentialBadge({ potential }: { potential: string }) {
  if (potential === "Very High") {
    return <span className="rounded-full bg-emerald-500/12 px-2.5 py-0.5 text-xs font-semibold text-emerald-400">{potential}</span>;
  }
  if (potential === "High") {
    return <span className="rounded-full bg-sky-500/12 px-2.5 py-0.5 text-xs font-semibold text-sky-400">{potential}</span>;
  }
  if (potential === "Moderate") {
    return <span className="rounded-full bg-amber-500/12 px-2.5 py-0.5 text-xs font-semibold text-amber-400">{potential}</span>;
  }
  return <span className="rounded-full bg-slate-500/12 px-2.5 py-0.5 text-xs font-semibold text-slate-400">{potential}</span>;
}

export default function WindPage() {
  return (
    <div className="animate-fade-in space-y-10">
      {/* Hero */}
      <header className="space-y-4">
        <p className="text-sm font-semibold uppercase tracking-widest text-sky-400">
          Engineering-Based Wind Estimation
        </p>
        <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
          Wind Estimation — Bangladesh
        </h1>
        <p className="max-w-2xl text-lg text-slate-300">
          PowerFlex BD provides engineering-based wind energy estimates
          using 100-meter hub-height wind speed data across Bangladesh&rsquo;s
          9 administrative divisions. The system applies power-curve analysis
          to convert raw wind speeds into estimated generation potential,
          ranking each zone for wind farm development suitability.
        </p>
        <div className="rounded-lg border border-amber-500/25 bg-amber-500/8 p-4 text-sm text-amber-400">
          <strong>Experimental:</strong> Wind estimates use a simplified
          prototype turbine power curve. This is NOT measured wind farm
          generation data. Results should be treated as engineering
          estimates, not measurements.
        </div>
      </header>

      {/* CTA */}
      <div>
        <a
          href="/dashboard"
          className="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-sky-500"
        >
          View Live Dashboard
          <span aria-hidden="true">&rarr;</span>
        </a>
      </div>

      {/* Power Curve Analysis */}
      <article className="space-y-6">
        <h2 className="text-2xl font-bold text-white">Power-Curve Analysis</h2>
        <p className="max-w-2xl text-slate-300">
          Wind AI converts 100m wind speed data into power output estimates
          using industry-standard turbine power curves. Each zone&rsquo;s wind
          profile is mapped against key turbine operating thresholds to
          calculate capacity factor and annual energy production (AEP).
        </p>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {POWER_CURVE_INFO.map((item) => (
            <div
              key={item.label}
              className="space-y-2 rounded-xl border border-slate-700/30 bg-slate-800/40 p-5"
            >
              <dt className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                {item.label}
              </dt>
              <dd className="text-2xl font-bold text-sky-400">{item.value}</dd>
              <p className="text-sm text-slate-400">{item.description}</p>
            </div>
          ))}
        </div>
      </article>

      {/* 100m Data */}
      <article className="space-y-4">
        <h2 className="text-2xl font-bold text-white">100m Hub-Height Data</h2>
        <p className="max-w-2xl text-slate-300">
          Measurements are taken at 100 meters above ground level — the
          standard hub height for modern utility-scale wind turbines. This
          altitude captures the true wind resource above surface roughness
          and turbulence, providing an accurate input for power-curve
          modeling.
        </p>
      </article>

      {/* 9 Zones */}
      <article className="space-y-6">
        <h2 className="text-2xl font-bold text-white">9 Wind Zones</h2>
        <p className="max-w-2xl text-slate-300">
          Each zone is ranked by average 100m wind speed and estimated
          power generation potential.
        </p>
        <div className="overflow-x-auto rounded-xl border border-slate-700/30">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-700/60 bg-slate-900/80">
              <tr>
                <th className="px-4 py-3 font-semibold text-slate-400">#</th>
                <th className="px-4 py-3 font-semibold text-slate-400">Zone</th>
                <th className="px-4 py-3 font-semibold text-slate-400">Avg 100m Speed</th>
                <th className="px-4 py-3 font-semibold text-slate-400">Potential</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/30">
              {ZONES.map((zone) => (
                <tr key={zone.id} className="transition-colors hover:bg-slate-800/40">
                  <td className="px-4 py-3 text-slate-500">{zone.id}</td>
                  <td className="px-4 py-3 font-medium text-white">{zone.name}</td>
                  <td className="px-4 py-3 text-slate-300">{zone.avgSpeed}</td>
                  <td className="px-4 py-3">
                    <PotentialBadge potential={zone.potential} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </article>
    </div>
  );
}
