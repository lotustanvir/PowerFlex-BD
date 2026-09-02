import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About PowerFlex BD — Independent Bangladesh Energy Intelligence",
  description:
    "Learn about PowerFlex BD, an independent energy intelligence and decision-support platform for Bangladesh. Our mission is to provide transparent, data-driven insights into the Bangladesh power grid and renewable energy potential.",
  alternates: { canonical: "/about" },
};

const dataClassifications = [
  { label: "Official Data", color: "text-emerald-400", description: "Verified data from government or institutional sources (PGCB ERP)" },
  { label: "Live Feed Data", color: "text-sky-400", description: "Near-real-time data from external APIs (Open-Meteo weather)" },
  { label: "Forecast Data", color: "text-blue-400", description: "Weather-driven or ML-driven predictions (solar forecast, demand forecast)" },
  { label: "Calculated Data", color: "text-amber-400", description: "Engineering or physics-based calculations (wind power curve, biomass potential)" },
  { label: "Prototype Data", color: "text-slate-400", description: "Placeholder assumptions awaiting real data (battery, flexible demand)" },
];

const dataSources = [
  { name: "PGCB ERP", description: "Official grid data for demand, supply, load-shedding, and generation breakdown." },
  { name: "Open-Meteo", description: "Open-source weather API providing solar irradiance, wind speed, temperature, and precipitation data." },
  { name: "FAOSTAT", description: "UN FAO statistical data for biomass and agricultural residue estimates." },
  { name: "BBS", description: "Bangladesh Bureau of Statistics demographic and economic indicators." },
  { name: "SREDA", description: "Sustainable and Renewable Energy Development Authority data on installed renewable capacity." },
];

export default function AboutPage() {
  return (
    <div className="animate-fade-in space-y-10">
      {/* Hero */}
      <header className="space-y-4 py-8 text-center">
        <p className="text-sm font-semibold uppercase tracking-widest text-emerald-400">
          Independent Energy Intelligence
        </p>
        <h1 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
          About PowerFlex BD
        </h1>
        <p className="mx-auto max-w-2xl text-lg text-slate-400">
          An independent energy intelligence and decision-support platform
          for Bangladesh — transparent, data-driven, and publicly accessible.
        </p>
      </header>

      {/* Mission */}
      <section aria-labelledby="mission-heading" className="mx-auto max-w-4xl space-y-4">
        <h2 id="mission-heading" className="text-2xl font-bold text-white">
          Our Mission
        </h2>
        <p className="text-slate-300">
          PowerFlex BD is an independent energy intelligence and
          decision-support platform built to provide transparent, data-driven
          insights into the Bangladesh power grid. We combine official grid
          data from PGCB with weather-driven forecasting and scenario-based
          optimization to help stakeholders understand supply, demand,
          deficits, and renewable energy potential across all 9 zones.
        </p>
        <p className="text-slate-300">
          Our goal is to democratize access to energy intelligence — making
          Bangladesh power sector data accessible, interpretable, and actionable
          for researchers, policy analysts, and the public.
        </p>
      </section>

      {/* Data Transparency */}
      <section aria-labelledby="transparency-heading" className="mx-auto max-w-4xl space-y-4">
        <h2 id="transparency-heading" className="text-2xl font-bold text-white">
          Data Transparency
        </h2>
        <p className="text-slate-300">
          Every value on this platform is classified by its data source and
          reliability. We distinguish between:
        </p>
        <ul className="space-y-2 text-slate-300">
          {dataClassifications.map((cls) => (
            <li key={cls.label}>
              <strong className={cls.color}>{cls.label}</strong> — {cls.description}
            </li>
          ))}
        </ul>
      </section>

      {/* Technology */}
      <section aria-labelledby="technology-heading" className="mx-auto max-w-4xl space-y-4">
        <h2 id="technology-heading" className="text-2xl font-bold text-white">
          Technology
        </h2>
        <p className="text-slate-300">
          PowerFlex BD uses weather-driven models and engineering calculations
          for solar and wind estimation. The demand forecasting model uses
          XGBoost trained on synthetic profiles based on published Bangladesh
          load research patterns, anchored to real-time PGCB demand.
        </p>
        <p className="text-slate-300">
          The platform scrapes the PGCB ERP portal on-demand for official grid
          data including demand, supply, load-shedding, and generation breakdown.
          Data freshness depends on PGCB website update frequency.
        </p>
      </section>

      {/* Data Sources */}
      <section aria-labelledby="data-sources-heading" className="mx-auto max-w-4xl space-y-4">
        <h2 id="data-sources-heading" className="text-2xl font-bold text-white">
          Data Sources
        </h2>
        <ul className="space-y-2 text-slate-300">
          {dataSources.map((source) => (
            <li key={source.name}>
              <strong className="text-slate-100">{source.name}</strong> — {source.description}
            </li>
          ))}
        </ul>
      </section>

      {/* Disclaimer */}
      <section aria-labelledby="disclaimer-heading" className="mx-auto max-w-4xl space-y-4 pb-8">
        <h2 id="disclaimer-heading" className="text-2xl font-bold text-white">
          Scientific Disclaimer
        </h2>
        <div className="space-y-4 rounded-lg border border-amber-500/25 bg-amber-500/8 p-6">
          <p className="text-slate-300">
            PowerFlex BD is an independent energy intelligence and
            decision-support platform. It is{" "}
            <strong className="text-slate-100">not affiliated with, endorsed
            by, or connected to</strong> any government body, the Bangladesh
            Power Grid Company (PGCB), the Bangladesh Energy Regulatory Commission
            (BERC), or any official state entity.
          </p>
          <p className="text-slate-300">
            <strong className="text-amber-400">This platform does NOT operate,
            control, or issue dispatch commands to the Bangladesh national grid.</strong>
          </p>
          <p className="text-slate-300">
            Forecasts, calculated estimates, technical potential assessments,
            and scenario analyses presented on this platform must not be
            interpreted as official real-time grid measurements.
          </p>
          <p className="text-slate-300">
            Experimental models (solar AI, wind power curve, demand forecast)
            are not validated against real Bangladesh operational data and
            should not be used for production decision-making without
            independent validation.
          </p>
        </div>
      </section>
    </div>
  );
}
