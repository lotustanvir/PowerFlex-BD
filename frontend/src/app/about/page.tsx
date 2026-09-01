import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About PowerFlex BD — Independent Bangladesh Energy Intelligence",
  description:
    "Learn about PowerFlex BD, an independent AI-powered energy intelligence platform for Bangladesh. Our mission is to provide transparent, data-driven insights into the Bangladesh power grid, renewable energy potential, and grid optimization.",
  alternates: { canonical: "/about" },
};

export default function AboutPage() {
  return (
    <>
      <header className="py-16 text-center">
        <h1 className="text-4xl font-extrabold tracking-tight text-emerald-400">
          About PowerFlex BD
        </h1>
      </header>

      <section aria-labelledby="mission-heading" className="mx-auto max-w-3xl space-y-6 py-8">
        <h2 id="mission-heading" className="text-2xl font-bold">
          Our Mission
        </h2>
        <p className="text-slate-300">
          PowerFlex BD is an independent energy intelligence platform built to
          provide transparent, data-driven insights into the Bangladesh power
          grid. We combine real-time grid data with AI-powered forecasting to
          help stakeholders understand supply, demand, deficits, and renewable
          energy potential across all 9 zones of Bangladesh.
        </p>
        <p className="text-slate-300">
          Our goal is to democratize access to energy intelligence — making
          Bangladesh power sector data accessible, interpretable, and actionable
          for researchers, policy analysts, and the public.
        </p>
      </section>

      <section aria-labelledby="technology-heading" className="mx-auto max-w-3xl space-y-6 py-8">
        <h2 id="technology-heading" className="text-2xl font-bold">
          Technology
        </h2>
        <p className="text-slate-300">
          PowerFlex BD leverages machine learning models for solar irradiance
          forecasting, wind speed prediction, and load deficit optimization. Our
          AI pipeline processes meteorological data alongside historical grid
          performance to deliver accurate, zone-level forecasts.
        </p>
        <p className="text-slate-300">
          The platform integrates with PGCB (Power Grid Company of Bangladesh)
          data infrastructure to surface real-time generation, transmission, and
          distribution metrics across the national grid.
        </p>
      </section>

      <section aria-labelledby="data-sources-heading" className="mx-auto max-w-3xl space-y-6 py-8">
        <h2 id="data-sources-heading" className="text-2xl font-bold">
          Data Sources
        </h2>
        <ul className="list-inside list-disc space-y-2 text-slate-300">
          <li>
            <strong className="text-slate-100">PGCB ERP</strong> — Power Grid
            Company of Bangladesh enterprise data for generation, transmission,
            and distribution metrics.
          </li>
          <li>
            <strong className="text-slate-100">Open-Meteo</strong> — Open-source
            weather API providing solar irradiance, wind speed, temperature, and
            precipitation data.
          </li>
          <li>
            <strong className="text-slate-100">FAOSTAT</strong> — Food and
            Agriculture Organization statistical data for biomass and
            agricultural residue estimates.
          </li>
          <li>
            <strong className="text-slate-100">BBS</strong> — Bangladesh Bureau
            of Statistics demographic and economic indicators.
          </li>
          <li>
            <strong className="text-slate-100">SREDA</strong> — Sustainable and
            Renewable Energy Development Authority data on installed renewable
            capacity.
          </li>
        </ul>
      </section>

      <section aria-labelledby="disclaimer-heading" className="mx-auto max-w-3xl space-y-6 py-8">
        <h2 id="disclaimer-heading" className="text-2xl font-bold">
          Disclaimer
        </h2>
        <p className="text-slate-400">
          PowerFlex BD is an independent platform and is{" "}
          <strong className="text-slate-200">not affiliated with, endorsed
          by, or connected to</strong> any government body, the Bangladesh
          Power Grid Company (PGCB), the Bangladesh Energy Regulatory Commission
          (BERC), or any official state entity. All data is sourced from
          publicly available feeds and processed independently.
        </p>
      </section>
    </>
  );
}
